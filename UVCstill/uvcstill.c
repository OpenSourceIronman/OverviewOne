// ----------------------------------------------------------
// UVC Still Capture Linux Driver
//
// Copyright SpaceVR, 2016.  All rights reserved.
//
// Author: Aaron Hurst (aaronpaulhurst@gmail.com)
// Date:   June 28, 2016
// ----------------------------------------------------------

// Defining the following forces the driver to ignore the webcam
// built into my HP laptop (when I want to test the Unity device
// on that host).
#undef DISABLE_HP_WEBCAM

// Defining the following causes the USB host to use DMA transfer.
// This is more cpu-efficient and results in faster URB processing.
#undef USE_DMA

// Definiting the following causes the driver to delay the URB
// processing and resubmission to another kernel thread, outside
// of the interrupt handler.  Despite this being "good design",
// it appears to hamper the throughput because we run out of
// URBs before any are resubmitted.
#define DELAYED_WORK

// Defining the following causes the driver to enforce exclusive
// access to the /dev/still device.  Nothing good will happen
// when two clients are interacting with the same camera, but this
// can cause lock-out if a file handle is left open and dangling.
#undef EXCLUSIVE_ACCESS

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/usb.h>
#include <linux/spinlock.h>
#include <linux/workqueue.h>
#include <linux/slab.h>
#include <linux/vmalloc.h>
#include <linux/circ_buf.h>
#include <uapi/linux/usb/video.h>
#include <asm/unaligned.h>
#include <asm/uaccess.h>

#include "uvcstill.h"

// Driver name is used in log messages.
#define DRIVER_NAME "uvcstill"

// How long should we wait for a USB control response?
#define CTRL_TIMEOUT 300

// Number of simultaneous USB URBs "in-flight" at one time.
#define NUM_URBS 8

// Number of URB buffers to preallocate.
#define NUM_INITIAL_URB_BUFS 1600

// Hard cap on the maximum number of URB buffers
#define URB_BUFFER_LIMIT 3000

// Buffer size
#define FRAME_BUF_PAGE_SIZE (4*1024)
#define FRAME_BUF_NUM_PAGES (6400)

#define NUM_STILL_SIZE_PATTERNS 10

// Debug output
#define DEBUG(...) printk(KERN_INFO DRIVER_NAME ": " __VA_ARGS__)
#define WARNING(...) printk(KERN_ERR DRIVER_NAME ": [WARNING] " __VA_ARGS__)

enum {
   // Default state.
   STATUS_WAITING = 0,
   //    -> STATUS_TRIGGERABLE : when a video packet is recieved

   // The video is streaming.  We can trigger
   // a still image at this point (for sure).
   STATUS_TRIGGERABLE,
   //    -> STATUS_IN_PROGRESS : when a still packet is recieved

   // We have received some still image data
   // and are expecting more.
   STATUS_IN_PROGRESS,
   //    -> STATUS_STATUS : when an end-of-frame packet is received
   //    -> STATUS_ERROR : when an unexpected video packet is received

   // We received an incomplete still image.
   // This has not yet been relayed to the read pipe.
   STATUS_ERROR,
   //    -> STATUS_WAITING : when the device is closed

   // We received a complete still image.
   // This has not yet been relayed to the read pipe.
   STATUS_SUCCESS
   //    -> STATUS_WAITING : when the device is closed
};

struct urb_buffer {
    struct list_head list;
#ifdef USE_DMA
    dma_addr_t dma;
#endif
    u8 * buf;
    int buf_len;
    u8 * iso_frame[32];
    int iso_frame_len[32];
    struct uvc_device *dev;
};

// ----------------------------------------------------------
// Main device structure
//
// This is allocated and initialized for each UVC device when
// it is first probed.

int next_dev_id = 1;

struct uvc_device {
    struct usb_device *udev;
    int id; // internal identifier

    // Set to true when termination is in progress.
    bool terminating;

    // ----- Device information -----

    int vendorID, productID;

    // - The control interface
    struct usb_interface *ctrl_intf;
    int ctrl_intfnum;

    // - Input streaming interface -----
    // Assumption: there is only one.

    // The interface number and data structure.
    struct usb_interface *in_intf;
    int in_intfnum;
    // The data input endpoint address.
    u8 in_epaddr;
    // The status interrupt endpoint address.
    u8 int_epaddr;
    // The interface alternate setting with the highest bandwidth.
    int in_altset;
    // Should we use bulk transfer?
    bool use_bulk;

    // - Camera and processing units
    int cameraID; // terminal ID
    int processingID; // unit ID
    int extensionID; // unit ID

    int frameSizeIdx;
    int frameSizeWidth[NUM_STILL_SIZE_PATTERNS];
    int frameSizeHeight[NUM_STILL_SIZE_PATTERNS];

    // ----- Data transfer -----

    int maxPayloadTransferSize;
    int maxPacketSize;
    size_t urb_buffer_len;

    // The USB requests.
    struct urb * urb[NUM_URBS];
    struct urb * int_urb;
    #define INT_BUF_SIZE 16
    u8 int_buf[INT_BUF_SIZE];

    // Work item to process completed URB buffers.
    struct work_struct process_ubs;

    // The transfer buffers.
    struct list_head free_urb_bufs;
    struct list_head full_urb_bufs;
    spinlock_t urb_bufs_lock;  // very short term

    // This flag toggles between frames.
    bool fid;

    // The data buffer.
    void ** buf_pages;
    size_t buf_head; // where to write next
    size_t buf_tail; // where to read next

    spinlock_t frame_buf_write_lock; // held through block
    struct mutex frame_buf_read_lock;  // held through block
    wait_queue_head_t waiting_to_read;
    wait_queue_head_t waiting_to_write;
    wait_queue_head_t waiting_to_trigger;


    // Guard against more than one open device.
    bool alive;
    bool busy;
    int status;
    bool streaming;
    bool active_urbs;
    int video_frames_since_reset;
    spinlock_t status_lock;  // very short term


    // ----- Statistics -----

    long n_packets;       // total
    long n_packets_with_errors;
    long n_bytes_recvd;
    int n_urb_bufs;

    // Per-frame device stats (for debugging mainly)
    long this_dev_packet_count;
    long video_packet_count;
    long still_packet_count;
    long alloc_count;
};

// Per-frame global stats (for debugging mainly)
long all_dev_packet_count = 0;

// Atomic status transition
static bool cond_status_transition(struct uvc_device *dev, int from, int to)
{
    bool rsl = false;

    spin_lock(&dev->status_lock);
    if (dev->status == from) {
        rsl = true;
        dev->status = to;
    }
    spin_unlock(&dev->status_lock);

    return rsl;
}


static void uncond_status_transition(struct uvc_device *dev, int to)
{
    spin_lock(&dev->status_lock);
    dev->status = to;
    spin_unlock(&dev->status_lock);
}


// File operations prototypes
static int     uvc_dev_open(struct inode *, struct file *);
static int     uvc_dev_release(struct inode *, struct file *);
static ssize_t uvc_dev_read(struct file *, char *, size_t, loff_t *);
static ssize_t uvc_dev_write(struct file *, const char *, size_t, loff_t *);
static long    uvc_dev_ioctl(struct file *, unsigned int, unsigned long);

// File operations descriptor
struct file_operations uvc_dev_fops = {
    .read           = uvc_dev_read,
    .write          = uvc_dev_write,
    .open           = uvc_dev_open,
    .release        = uvc_dev_release,
    .unlocked_ioctl = uvc_dev_ioctl,
};

// USB device identifiers
static struct usb_device_id uvc_usb_ids[] = {
    /* Generic USB Video Class */
    { USB_INTERFACE_INFO(USB_CLASS_VIDEO, 1, 0) },
    {}
};

MODULE_DEVICE_TABLE(usb, uvc_usb_ids);

// USB device prototypes
static int uvc_usb_probe(struct usb_interface *, const struct usb_device_id *);
static void uvc_usb_disconnect(struct usb_interface *intf);

// USB device descriptor
struct usb_driver uvc_usb_driver = {
    .name           = "uvcstill",
    .probe          = uvc_usb_probe,
    .disconnect     = uvc_usb_disconnect,
    .id_table       = uvc_usb_ids,
};

// USB device class descriptor
struct usb_class_driver uvc_usb_class_driver = {
    .name           = "still%d",
    .fops           = &uvc_dev_fops,
    .minor_base     = 192
};


// Utility method for any UVC control queries.
static int uvc_ctrl(
        struct uvc_device *dev, u8 query, u8 unit,
        u8 intfnum, u8 cs, void *data, u16 size,
        int timeout, int retries);

static int uvc_trigger_still(struct uvc_device *dev);

static struct urb_buffer * alloc_urb_buffer(struct uvc_device *, int, int);

// ---------------------------------------------------
// USB device enumeration
// ---------------------------------------------------


static bool is_unity(struct uvc_device *dev)
{
    return (dev->udev->descriptor.idVendor == 0x2a12) &&
           (dev->udev->descriptor.idProduct == 0x001);
}


// Returns the endpoint structure with a particular address.
static struct usb_host_endpoint * find_endpoint(
        struct usb_host_interface *alts,
        u8 epaddr)
{
    struct usb_host_endpoint *ep;
    unsigned int i;

    for (i = 0; i < alts->desc.bNumEndpoints; ++i) {
        ep = &alts->endpoint[i];
        if (ep->desc.bEndpointAddress == epaddr)
            return ep;
    }

    return NULL;
}


// UVC STILL_IMAGE_FRAME descriptor.
struct uvc_still_control_descriptor {
        u8  bLength;
        u8  bDescriptorType;
        u8  bDescriptorSubType;
        u8  bEndpointAddress;
        u8  bNumImageSizePatterns;
        u16 wWidthOrHeight[];
        // TODO: compression patterns
 } __attribute__((__packed__));


// Parse all descriptors for stream interface.
static int uvc_parse_stream_descriptors(
        struct uvc_device *dev,
        struct usb_interface *intf)
{
    struct usb_host_interface *alts = &intf->altsetting[0];
    unsigned char *buffer = alts->extra;
    int buflen = alts->extralen;
    int i, psize;

    DEBUG("streaming interface : %d \n", alts->desc.bInterfaceNumber);

    // Skip the standard interface descriptors.
    while (buflen > 2 && buffer[1] != USB_DT_CS_INTERFACE) {
        buflen -= buffer[0];
        buffer += buffer[0];
    }

    // Parse the class-specific descriptors.
    while (buflen > 2 && buffer[1] == USB_DT_CS_INTERFACE) {
        switch (buffer[2]) {

        case UVC_VS_OUTPUT_HEADER:
            DEBUG("output stream \n");
            break;

        case UVC_VS_INPUT_HEADER:
            DEBUG("input stream \n");

            // Record information about input stream
            dev->in_intf = intf;
            dev->in_intfnum = alts->desc.bInterfaceNumber;
            dev->in_epaddr = buffer[6];
            DEBUG("  epaddr = %d \n", buffer[6]);
            DEBUG("  stillCaptureMethod = %d \n", buffer[9]);
            DEBUG("  triggerSupport = %d \n", buffer[10]);
            DEBUG("  triggerUsage = %d \n", buffer[11]);
            break;

        case UVC_VS_STILL_IMAGE_FRAME: {
            struct uvc_still_control_descriptor * still_desc =
                (struct uvc_still_control_descriptor *)buffer;
            int maxWidthIdx = 0;

            DEBUG("still image.  # frame sizes = %d\n", still_desc->bNumImageSizePatterns);
            for(i=0; (i<still_desc->bNumImageSizePatterns) && (i<NUM_STILL_SIZE_PATTERNS); ++i) {
                dev->frameSizeWidth[i] =
                    get_unaligned(&still_desc->wWidthOrHeight[i*2]);
                dev->frameSizeHeight[i] =
                    get_unaligned(&still_desc->wWidthOrHeight[i*2+1]);

                DEBUG("  frame size %d = %d x %d\n", i,
                      dev->frameSizeWidth[i], dev->frameSizeHeight[i]);

                if (dev->frameSizeWidth[i] > dev->frameSizeWidth[maxWidthIdx]) {
                    maxWidthIdx = i;
                }
            }

            // Select the maximum frame size.
            dev->frameSizeIdx = maxWidthIdx;
        }
        break;

        default:
            break;
        }
        buflen -= buffer[0];
        buffer += buffer[0];
    }

    if (dev->in_intf == NULL) {
        // Not an input stream.  Nothing more to do.
        return 0;
    }

    // Which alternate settings has the maximum bandwidth?
    dev->maxPacketSize = 0;
    for (i = 0; i < intf->num_altsetting; ++i) {
        struct usb_host_endpoint *ep;
        alts = &intf->altsetting[i];
        ep = find_endpoint(alts, dev->in_epaddr);
        if (ep == NULL)
            continue;

        psize = le16_to_cpu(ep->desc.wMaxPacketSize);
        psize = (psize & 0x07ff) * (1 + ((psize >> 11) & 3));
        if (psize > dev->maxPacketSize) {
            if (ep->desc.bmAttributes & USB_ENDPOINT_XFER_ISOC) {
                // Prefer isochronous
                dev->use_bulk = false;
                DEBUG("  alternate %d isoc psize = %d \n", alts->desc.bAlternateSetting, psize);
            }
            else if (ep->desc.bmAttributes & USB_ENDPOINT_XFER_BULK) {
                dev->use_bulk = true;
                DEBUG("  alternate %d bulk psize = %d \n", alts->desc.bAlternateSetting, psize);
            }
            else { continue; }

            dev->maxPacketSize = psize;
            dev->in_altset = alts->desc.bAlternateSetting;
        }
    }

    return 0;
}


// Parses a single control interface descriptor.
// The descriptor is in 'buffer' of size 'buflen'.
static int uvc_parse_ctrl_desc(
        struct uvc_device *dev,
        const unsigned char *buffer,
        int buflen)
{
    unsigned int n, i;
    // struct usb_host_interface *alts = dev->ctrl_intf->cur_altsetting;
    struct usb_device *udev = dev->udev;
    struct usb_interface *intf;

    // Common descriptor header:
    struct uvc_descriptor_header * desc =
        (struct uvc_descriptor_header *)buffer;
    // Specialized descriptor types:
    struct uvc_input_terminal_descriptor *itt_desc =
        (struct uvc_input_terminal_descriptor *)buffer;
    struct uvc_processing_unit_descriptor *proc_desc =
        (struct uvc_processing_unit_descriptor *)buffer;
    struct uvc_extension_unit_descriptor *ext_desc =
        (struct uvc_extension_unit_descriptor *)buffer;

    switch (desc->bDescriptorSubType) {
    // The header descriptor contains a list of the other video
    // streaming interfaces.
    case UVC_VC_HEADER:
        DEBUG("header descriptor \n");

        n = buflen >= 12 ? buffer[11] : 0;
        if (buflen < 12 + n) {
            return -EINVAL;
        }

        // Parse all streaming interface descriptors.
        for (i = 0; i < n; ++i) {
            intf = usb_ifnum_to_if(udev, buffer[12+i]);
            if (intf != NULL) {
                uvc_parse_stream_descriptors(dev, intf);
            }
        }
        break;

    case UVC_VC_INPUT_TERMINAL:
        if (itt_desc->wTerminalType == UVC_ITT_CAMERA) {
            DEBUG("found camera entity \n");
            dev->cameraID = itt_desc->bTerminalID;
        }
        break;

    case UVC_VC_PROCESSING_UNIT:
        DEBUG("found processing unit \n");
        dev->processingID = proc_desc->bUnitID;
        break;

    case UVC_VC_EXTENSION_UNIT:
        DEBUG("found extension unit \n");
        dev->extensionID = ext_desc->bUnitID;
        break;

    // Ignore the other control interface descriptors.
    default:
        break;
    }

    return 0;
}


// Main entry point to parse the descriptors for a UVC
// control interface.
//
// Prerequisites: dev->ctrl_intf set
static int uvc_parse_ctrl_descriptors(struct uvc_device *dev)
{
    struct usb_host_interface *alts = dev->ctrl_intf->cur_altsetting;
    unsigned char *buffer = alts->extra;
    int buflen = alts->extralen;
    int ret;

    DEBUG("control interface : %d \n ", alts->desc.bInterfaceNumber);

    // Iterate through all descriptors
    while (buflen > 2) {
        if (buffer[1] == USB_DT_CS_INTERFACE) {
            if ((ret = uvc_parse_ctrl_desc(dev, buffer, buflen)) < 0)
                return ret;
        }

        buflen -= buffer[0];
        buffer += buffer[0];
    }

    // Check if the optional status endpoint is present.
    if (alts->desc.bNumEndpoints == 1) {
        struct usb_host_endpoint *ep = &alts->endpoint[0];
        struct usb_endpoint_descriptor *desc = &ep->desc;

        if (usb_endpoint_is_int_in(desc) &&
            le16_to_cpu(desc->wMaxPacketSize) >= 8 &&
            desc->bInterval != 0)
        {
            DEBUG("intterupt endpoint at %02x \n", desc->bEndpointAddress);
         dev->int_epaddr = desc->bEndpointAddress;
        }
    }

    return 0;
}


// ---------------------------------------------------
// USB device communication
// ---------------------------------------------------

#if 0
// Compute the maximum number of bytes per interval for an endpoint.
// Copy-pasted from UVC video driver.
static unsigned int uvc_endpoint_max_bpi(
        struct usb_device *dev,
        struct usb_host_endpoint *ep)
{
    u16 psize;

    switch (dev->speed) {
    case USB_SPEED_SUPER:
        return le16_to_cpu(ep->ss_ep_comp.wBytesPerInterval);
    case USB_SPEED_HIGH:
        psize = usb_endpoint_maxp(&ep->desc);
        return (psize & 0x07ff) * (1 + ((psize >> 11) & 3));
    case USB_SPEED_WIRELESS:
        psize = usb_endpoint_maxp(&ep->desc);
        return psize;
    default:
        psize = usb_endpoint_maxp(&ep->desc);
        return psize & 0x07ff;
    }
}
#endif



static void uvc_kill_urbs(struct uvc_device * dev)
{
    int i;

    if (!dev->active_urbs) {
        // Already killed
        return;
    }
    dev->active_urbs = false;

    DEBUG("Killing URBs\n");

    for(i=0; i<NUM_URBS; ++i) {
        // NOTE: Any URBs that are killed may still have their
        // completion callbacks invoked in the (distant)
        // future with a non-zero status.  Therefore,
        // failing URBs need to tolerate a bad context.
        if (dev->urb[i]) {
            usb_kill_urb(dev->urb[i]);

            // Successfully killed.  Mark as inactive.
            dev->urb[i]->context = NULL;
        }
    }
}


// URBs must be initialized and ready to submit.
static void uvc_submit_urbs(struct uvc_device * dev)
{
    int i, retval;
    unsigned long flags = 0;
    struct urb_buffer * ALLOC_NEW_URB = (struct urb_buffer *)1;

    if (dev->active_urbs) {
        // Already submitted
        return;
    }
    dev->active_urbs = true;

    DEBUG("Submitting URBs\n");

    for(i=0; i<NUM_URBS; ++i) {
        struct urb * urb = dev->urb[i];
        struct urb_buffer * urb_buf = NULL;

        // !!! Enter critical section !!!
        spin_lock_irqsave(&dev->urb_bufs_lock, flags);

        // Active URBs are indicated by a non-NULL context.
        if (urb->context) {
            // Already active.  Skip.
            spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
            continue;
        }

        // Reuse one from "free" list, if available
        if (!list_empty(&dev->free_urb_bufs)) {
            urb_buf = list_first_entry(&dev->free_urb_bufs,
                                       struct urb_buffer, list);
            list_del(&urb_buf->list);
            urb->context = urb_buf;
        } else {
            // Nope, we'll need to allocate a new one.
            // Tentatively mark URB as active before unlocking.
            urb->context = ALLOC_NEW_URB;
        }

        spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
        // !!! Exit critical section !!!

        // Allocate a new URB buffer, if needed
        if (urb->context == ALLOC_NEW_URB) {
            urb->context = alloc_urb_buffer(dev, urb->number_of_packets, GFP_KERNEL);
        }
        if (urb->context == NULL) {
            WARNING("failed to alloc urb buffer \n");
            continue;
        }

        // Update any URB structures for the new buffer
        urb->transfer_buffer = urb_buf->buf;
#ifdef USE_DMA
        urb->transfer_dma = urb_buf->dma;
#endif

        retval = usb_submit_urb(urb, GFP_KERNEL);
        if (retval) {
            // Submit failed.
            WARNING("urb error on initial submit %d \n", retval);

            // !!! Enter critical section !!!
            spin_lock_irqsave(&dev->urb_bufs_lock, flags);
            // Put the buffer back on the free list.
            list_add(&urb_buf->list, &dev->free_urb_bufs);
            // Mark the URB as inactive.
            urb->context = NULL;
            spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
            // !!! Exit critical section !!!
        }
    }
}


// Returns action:
//   * 0 => skip packet
//   * 1 => process packet
static int pre_process_packet_flags(
        struct uvc_device *dev,
        int flags)
{
    int action;

    if (flags & UVC_STREAM_STI) {
        // --- Still image data ---

        action = 1; // process packet

        if (dev->status == STATUS_IN_PROGRESS) {
            // carry on
        }
        else if (cond_status_transition(dev, STATUS_WAITING, STATUS_IN_PROGRESS)
            || cond_status_transition(dev, STATUS_TRIGGERABLE, STATUS_IN_PROGRESS))
        {
            DEBUG("still image start \n");

            // DEBUG: reset counters
            all_dev_packet_count = 0;
            dev->this_dev_packet_count = 0;
            dev->video_packet_count = 0;
            dev->still_packet_count = 0;
            dev->alloc_count = 0;

            dev->fid = (flags & UVC_STREAM_FID);
            dev->buf_head = dev->buf_tail = 0;
        }
        else {
            WARNING("unexpected still with status = %d \n", dev->status);
        }

        dev->still_packet_count++;
    } else {
        // --- Video stream data ---

        action = 0; // skip packet
        dev->video_packet_count++;

        if (flags & UVC_STREAM_EOF) {
            dev->video_frames_since_reset++;
        }

        if (dev->video_frames_since_reset > 1 &&
            cond_status_transition(dev, STATUS_WAITING, STATUS_TRIGGERABLE))
        {
            DEBUG("ready to trigger \n");

            wake_up_interruptible(&dev->waiting_to_trigger);
        }

        if (cond_status_transition(dev, STATUS_IN_PROGRESS, STATUS_ERROR))
        {
            // We missed the end-of-frame.  Somehow.
            DEBUG("still image finish-- without EOF %d \n", (int)dev->buf_head);

            // Wake up read pipes to return error.
            wake_up_interruptible(&dev->waiting_to_read);
        }
    }

    all_dev_packet_count++;
    dev->this_dev_packet_count++;

    return action;
}


static void post_process_packet_flags(
        struct uvc_device *dev,
        int flags)
{
    // Is this the end-of-frame?
    // Either: the header told us so directory, or the frame FID bit has toggled.
    if ( (flags & UVC_STREAM_EOF) ||
         (dev->fid != (flags & UVC_STREAM_FID)) )
    {
        DEBUG("***** end of frame !!! %d \n", (int)dev->buf_head);
        DEBUG("      utilization stats: other=%ld, this=%ld (still=%ld video=%ld) allocs=%ld \n",
              all_dev_packet_count - dev->this_dev_packet_count,
              dev->this_dev_packet_count,
              dev->still_packet_count, dev->video_packet_count,
              dev->alloc_count);

        spin_lock(&dev->status_lock);
        if (dev->busy) {
            dev->status = STATUS_SUCCESS;
        } else {
            dev->status = STATUS_WAITING;
        }
        spin_unlock(&dev->status_lock);
    }
}


// Copy a single packet into the frame buffer.
// If it is the end of the frame, take appropriate action.
// The buffer must includ  the UVC uncompressed packet header.
static void copy_packet_to_frame_buffer(
        struct uvc_device *dev,
        char * buffer, int buffer_len)
{
    size_t off;
    int p, avail, flags;

    dev->n_packets += 1;

    // Skip empty packets
    if (buffer_len < 2) {
        return;
    }

    // Skip insane packets with header length != 12
    if (buffer[0] != 12) {
        return;
    }

    flags =  buffer[1];
    buffer_len -= buffer[0];
    buffer += buffer[0];

    if (!pre_process_packet_flags(dev, flags)) {
        return;
    }

    spin_lock(&dev->frame_buf_write_lock);

    // DEBUG("writing %d total \n", buffer_len);

    // Write content into frame buffer.
    while(buffer_len > 0) {
        p = dev->buf_head / FRAME_BUF_PAGE_SIZE;
        if (p >= FRAME_BUF_NUM_PAGES) {
            WARNING("out of buffer space \n");
            break;
        }
        off = dev->buf_head % FRAME_BUF_PAGE_SIZE;
        avail = min((size_t)buffer_len,
                    FRAME_BUF_PAGE_SIZE - off);

        // DEBUG("writing %d into page %d at %d \n", avail, p, off);

        memcpy(dev->buf_pages[p] + off, buffer, avail);

        buffer_len -= avail;
        buffer += avail;
        dev->n_bytes_recvd += avail;
        dev->buf_head += avail;
    }

    spin_unlock(&dev->frame_buf_write_lock);

    post_process_packet_flags(dev, flags);

    wake_up_interruptible(&dev->waiting_to_read);
}


// Copy packet to a buffer.
// (This wrapper exists to allow the packet to be consumed
// in multiple different ways.)
static void copy_packet_to_buffer(
        struct uvc_device *dev,
        char * buffer, int buffer_len)
{
    copy_packet_to_frame_buffer(dev, buffer, buffer_len);
}


// Process the completed URBs.  This is triggered via
// a work queue and outside of the intterupt handler.
static void uvc_urb_process2(struct work_struct *raw_work) {
    struct uvc_device *dev = container_of(raw_work, struct uvc_device, process_ubs);
    struct urb_buffer *ub = NULL;
    int i, j = 0;
    unsigned long flags = 0;

    while(1) {

        // !!! Enter critical section !!!
        spin_lock_irqsave(&dev->urb_bufs_lock, flags);
        if (ub != NULL) {
            list_add(&ub->list, &dev->free_urb_bufs);
        }
        ub = NULL;
        if (!list_empty(&dev->full_urb_bufs)) {
            ub = list_first_entry(&dev->full_urb_bufs,
                                  struct urb_buffer, list);
            list_del(&ub->list);
        }
        spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
        // !!! Exit critical section !!!

        if (ub == NULL) {
            break;
        }
        if (++j > URB_BUFFER_LIMIT) {
            // Bad
            WARNING("Infinite loop detected! \n");
            break;
        }

        // Process
        if (dev->terminating) {
            // Skip processing
        } else if (dev->use_bulk) {
            copy_packet_to_buffer(dev, ub->buf, ub->buf_len);
        } else {
            for(i=0; i<32; ++i) {
                if (ub->iso_frame[i] != NULL) {
                    copy_packet_to_buffer(dev, ub->iso_frame[i], ub->iso_frame_len[i]);
                }
            }
        }
    }
}


// Interrupt handler for completed data URBs.
static void uvc_urb_complete(struct urb *urb)
{
    int retval, i;
    struct uvc_device *dev = NULL;
    struct urb_buffer * ub;
    unsigned long flags = 0;

    ub = (struct urb_buffer *)urb->context;
    if (ub == NULL) {
        DEBUG("urb corrupt \n ");
        return;
    }
    dev = ub->dev;

    if (urb->status == -ESHUTDOWN || !dev->active_urbs || dev->terminating) {
        // Don't resubmit
        spin_lock_irqsave(&dev->urb_bufs_lock, flags);
        list_add(&ub->list, &dev->free_urb_bufs);
        spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
        return;
    }

    if (urb->status != 0) {
        DEBUG("urb error %d \n ", urb->status);
        dev->n_packets_with_errors += 1;
        goto resubmit;
    }

    if (!dev->alive) {
        DEBUG("Device %d is alive\n", dev->id);
        dev->alive = true;
    }

    // Copy info to URB buffer
    ub->buf_len = urb->actual_length;
    for(i=0; i<urb->number_of_packets; ++i) {
        ub->iso_frame[i] =
            ub->buf + urb->iso_frame_desc[i].offset;
        ub->iso_frame_len[i] =
            urb->iso_frame_desc[i].actual_length;

        // Skip erroneous packets
        if (urb->iso_frame_desc[i].status < 0) {
            ub->iso_frame[i] = NULL;
        }
    }

    // !!! Enter critical section !!!
    spin_lock_irqsave(&dev->urb_bufs_lock, flags);

    // Move URB buffer to "full" list
    list_add_tail(&ub->list, &dev->full_urb_bufs);
    ub = NULL;

    // Attempt to reuse one from "free" list
    if (!list_empty(&dev->free_urb_bufs)) {
        ub = list_first_entry(&dev->free_urb_bufs,
                              struct urb_buffer, list);

        list_del(&ub->list);
    } else {
        ++dev->alloc_count;
    }

    spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
    // !!! Exit critical section !!!

    // Schedule bottom-half processing work
    schedule_work(&dev->process_ubs);

    // Allocate a new URB buffer if needed
    if (ub == NULL) {
        ub = alloc_urb_buffer(dev, urb->number_of_packets, GFP_ATOMIC);
    }
    if (ub == NULL) {
        WARNING("failed to alloc urb buffer \n");
        // Mark URB as inactive.
        urb->context = NULL;
        return;
    }

    // Update any URB structures for the new buffer
    urb->context = ub;
    urb->transfer_buffer = ub->buf;
#ifdef USE_DMA
    urb->transfer_dma = ub->dma;
#endif

resubmit:
    // Resubmit URB
    retval = usb_submit_urb(urb, GFP_ATOMIC);
    if (retval) {
        // Submit failed.
        WARNING("urb error on resubmit %d \n", retval);

        // !!! Enter critical section !!!
        spin_lock_irqsave(&dev->urb_bufs_lock, flags);
        // Put the buffer back on the free list.
        list_add(&ub->list, &dev->free_urb_bufs);
        // Mark the URB as inactive.
        urb->context = NULL;
        spin_unlock_irqrestore(&dev->urb_bufs_lock, flags);
        // !!! Exit critical section !!!
    }
}


static struct urb_buffer * alloc_urb_buffer(
        struct uvc_device *dev,
        int npackets,
        int flags)
{
    struct urb_buffer * ub;

    if (dev->n_urb_bufs > URB_BUFFER_LIMIT) {
        // We've reached the hard limit
        return NULL;
    }

    if ((ub = kzalloc(sizeof(struct urb_buffer), flags)) == NULL)
        return NULL;

#ifdef USE_DMA
    if ((ub->buf = usb_alloc_coherent(dev->udev,
                dev->urb_buffer_len, flags, &ub->dma)) == NULL) {
        kfree(ub);
        return NULL;
    }
#else
    if ((ub->buf = kmalloc(dev->urb_buffer_len, flags)) == NULL) {
        kfree(ub);
        return NULL;
    }
#endif

    ub->dev = dev;
    ++dev->n_urb_bufs;
    return ub; // success;
}

// Initialize and submit data transfer URBs.
static int uvc_init_data(
        struct uvc_device *dev)
{
    struct urb *urb;
    int npackets = 0;
    struct usb_host_endpoint *ep;
    int i, j, psize = 0;

    // TODO: maybe stash in uvc_device?
    ep = find_endpoint(dev->in_intf->cur_altsetting,
                       dev->in_epaddr);
    if (ep == NULL)
        return -EIO;

    if (dev->use_bulk) {
        npackets = 0; // not used for bulk transfer
        dev->urb_buffer_len = dev->maxPayloadTransferSize;
        DEBUG("init bulk urb psize=%d \n", (int)dev->urb_buffer_len);
    } else {
        npackets = 32; // this is the max
        psize = dev->maxPacketSize;
        dev->urb_buffer_len = psize * npackets;
        DEBUG("init isoc urb psize=%d \n", psize);
    }

    // Allocate URB buffers
    for(i=0; i<NUM_INITIAL_URB_BUFS; ++i) {
        struct urb_buffer * ub = alloc_urb_buffer(dev, npackets, GFP_KERNEL);
        if (ub == NULL) {
            WARNING("could not alloc urb buffer \n");
            return -ENOMEM;
        }
        list_add(&ub->list, &dev->free_urb_bufs);
    }

    for(i=0; i<NUM_URBS; ++i) {
        // Allocate and initialize URBs
        urb = usb_alloc_urb(npackets, GFP_KERNEL);
        if (urb == NULL) {
            WARNING("could not alloc urb \n");
            return -ENOMEM;
        }

        if (dev->use_bulk) {
            // Bulk transfer packet
            usb_fill_bulk_urb(
                /* urb*/ urb,
                /* usb_device */ dev->udev,
                /* pipe */ usb_rcvbulkpipe(dev->udev, dev->in_epaddr),
                /* transfer_buffer */ NULL,
                /* transfer_buffer_length */ dev->urb_buffer_len,
                /* callback */ uvc_urb_complete,
                /* context */ NULL);

        } else {
            // Isochronous packet
            urb->dev = dev->udev;
            urb->context = NULL;
            urb->pipe = usb_rcvisocpipe(dev->udev, dev->in_epaddr);
            urb->transfer_flags = URB_ISO_ASAP;
            urb->interval = ep->desc.bInterval;
            urb->transfer_buffer_length = dev->urb_buffer_len;
            urb->complete = uvc_urb_complete;

            urb->number_of_packets = npackets;
            for (j = 0; j < npackets; ++j) {
                urb->iso_frame_desc[j].offset = j * psize;
                urb->iso_frame_desc[j].length = psize;
            }

        }

#ifdef USE_DMA
        urb->transfer_flags |= URB_NO_TRANSFER_DMA_MAP;
#endif

        dev->urb[i] = urb;
    }

    return 0; // success
}


// ---------------------------------------------------
// USB device control messages
// ---------------------------------------------------

// UVC protocol data structure for: Still Probe and Commit Controls
struct uvc_still_control {
        u8  bFormatIndex;
        u8  bFrameIndex;
        u8  bCompressionIndex;
        u32 dwMaxVideoFrameSize;
        u32 dwMaxPayloadTransferSize;
 } __attribute__((__packed__));


// Control messages can either be directed at an "entity"
// (for example, a camera or processing unit) or the streaming
// interface as a whole.  This value encodes the latter case.
#define UVC_NO_ENTITY 0


// Perform a control message query.
// 'dev' is the uvc_device structure
// 'query' can be one of SET_CUR, GET_CUR, GET_INFO, etc.
// 'cs' is the class of message
// 'unit' can be either an entity ID or UVC_NO_ENTITY as
//     is appropriate to class of message
// 'intfnum' is the interface
// 'data' is a buffer of length 'size'
static int uvc_ctrl(
        struct uvc_device *dev, u8 query, u8 unit,
        u8 intfnum, u8 cs, void *data, u16 size,
        int timeout, int retries)
{
    u8 type = USB_TYPE_CLASS | USB_RECIP_INTERFACE;
    unsigned int pipe;
    int retval = 0;

    pipe = (query & 0x80) ? usb_rcvctrlpipe(dev->udev, 0)
                  : usb_sndctrlpipe(dev->udev, 0);
    type |= (query & 0x80) ? USB_DIR_IN : USB_DIR_OUT;

    while(1) {
        retval = usb_control_msg(dev->udev, pipe, query, type, cs << 8,
                unit << 8 | intfnum, data, size, timeout);

        if (retval == -ETIMEDOUT && --retries > 0) continue;
        break;
    }

    if (retval < 0) {
        WARNING("Failed %s control %u on "
                   "unit %u: error %d \n",
                   (query == UVC_SET_CUR ? "SET_CUR" : "GET"),
                   cs, unit, -retval);
        return retval;
    }
    else if (retval != size) {
        WARNING("Failed %s control %u on "
                   "unit %u: %d (expected %u).\n",
                   (query == UVC_SET_CUR ? "SET_CUR" : "GET"),
                   cs, unit, retval, size);
        return -EIO;
    }

    return 0;
}


// ---------------------------------------------------
// Interrupt endpoints.
// ---------------------------------------------------

static void uvc_interrupt_complete(struct urb *urb)
{
    int retval;
    struct uvc_device *dev;

    dev = (struct uvc_device *)urb->context;

    if (urb->status == -ESHUTDOWN) {
        // Don't resubmit
        return;
    }

    DEBUG("interrupt recieved \n");

    if ((retval = usb_submit_urb(dev->int_urb, GFP_ATOMIC))) {
        WARNING("interrupt urb error on resubmit %d \n", retval);
    }
}

static int uvc_interrupt_init(
        struct uvc_device *dev)
{
    int retval;
    int interval;

    dev->int_urb = usb_alloc_urb(0, GFP_KERNEL);
    if (dev->int_urb == NULL) {
        WARNING("failed to alloc interrupt urb\n");
        return -ENOMEM;
    }

    interval = 7; // ep->desc.bInterval;

    usb_fill_int_urb(/*urb*/ dev->int_urb,
                     /*usb device*/ dev->udev,
                     /*pipe*/ usb_rcvintpipe(dev->udev, dev->int_epaddr),
                     /*transfer_buffer*/ dev->int_buf,
                     /*transfer_buffer_len*/ INT_BUF_SIZE,
                     /*callback*/ uvc_interrupt_complete,
                     /*context*/ dev,
                     /*interval*/ interval);

    if ((retval = usb_submit_urb(dev->int_urb, GFP_KERNEL))) {
        WARNING("urb error on initial submit %d \n", retval);
    }

    return 0; // success
}


// ---------------------------------------------------
// Streaming Negotiation.
// ---------------------------------------------------

// Negotiate video streaming parameters with the device.
// This exists to try to make Unity spit out data.
static int uvc_negotiate_video(
        struct uvc_device *dev)
{
    int retval;
    int size;
    struct uvc_streaming_control msg;

    // XXX: These values are hardcoded.
    memset(&msg, 0, sizeof(msg));
    msg.bFrameIndex = 1; // 640x480 on Unity board
    msg.bFormatIndex = 1;
    msg.dwFrameInterval = 333333;

    // TODO: detect protocol version
    // size = sizeof(msg); // newer version of UVC protocol
    size = 26;             // older version of UVC protocol

    // We send a request with the desired parameters...
    retval = uvc_ctrl(dev, UVC_SET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_PROBE_CONTROL,
                      &msg, size, CTRL_TIMEOUT, 3);
    // if (retval) { return retval; }

    // ... and read back what the device agrees to.
    retval = uvc_ctrl(dev, UVC_GET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_PROBE_CONTROL,
                      &msg, size, CTRL_TIMEOUT, 3);
    // if (retval) { return retval; }

    DEBUG("negotiated video "
           "formatIndex=%d frameIndex=%d "
           "maxPayloadTransferSize=%d "
           "maxVideoFrameSize=%d \n",
           msg.bFormatIndex, msg.bFrameIndex,
           get_unaligned_le32(&msg.dwMaxPayloadTransferSize),
           get_unaligned_le32(&msg.dwMaxVideoFrameSize));

    // Now, we can commit the negotiated settings.
    retval = uvc_ctrl(dev, UVC_SET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_COMMIT_CONTROL,
                      &msg, size, CTRL_TIMEOUT, 3);
    if (retval) { return retval; }

    // Don't verify the committed settings.
    // This appears to be unsupported by the Unity board.

    return 0; // success
}


// Negotiate still frame parameters with the device.
static int uvc_negotiate_still(
        struct uvc_device *dev)
{
    int retval;
    struct uvc_still_control msg;
    memset(&msg, 0, sizeof(msg));

#if 0
    // XXX: Hardcoded frame sizes (with off-by-one)
    msg.bFrameIndex = 0;  // 1280x720  - 1MP  - 2MB
    msg.bFrameIndex = 0;  // 640x480 for ahurst laptop
    msg.bFrameIndex = 2;  // 1920x1080 - 2MP  - 4MB
    msg.bFrameIndex = 3;  // 2592x1944 - 5MP  - 10MB
    msg.bFrameIndex = 4;  // 3264x2448 - 8MP  - 16MB
    msg.bFrameIndex = 5;  // 4128x3096 - 12MP - 24MB
    msg.bFrameIndex = 6;  // 4192x3104 - 13MP - 26MB
#endif

    msg.bFrameIndex = dev->frameSizeIdx;
    DEBUG("choosing still frame size = %d x %d @ index %d \n",
          dev->frameSizeWidth[dev->frameSizeIdx],
          dev->frameSizeHeight[dev->frameSizeIdx],
          dev->frameSizeIdx);
    // HUH: the frame index is off-by-one from the descriptor array
    msg.bFrameIndex++;

    msg.bFormatIndex = 1;
    msg.bCompressionIndex = 1;
    msg.dwMaxVideoFrameSize = 0xffffffff;

    // We send a request with the desired parameters...
    retval = uvc_ctrl(dev, UVC_SET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_STILL_PROBE_CONTROL,
                      &msg, sizeof(msg), CTRL_TIMEOUT, 3);
    // if (retval) { return retval; }

    // ... and read back what the device agrees to.
    retval = uvc_ctrl(dev, UVC_GET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_STILL_PROBE_CONTROL,
                      &msg, sizeof(msg), CTRL_TIMEOUT, 3);
    // if (retval) { return retval; }

    DEBUG("negotiated still "
           "formatIndex=%d frameIndex=%d compressionIndex=%d "
           "maxPayloadTransferSize=%d "
           "maxVideoFrameSize=%d \n",
           msg.bFormatIndex, msg.bFrameIndex, msg.bCompressionIndex,
           get_unaligned_le32(&msg.dwMaxPayloadTransferSize),
           get_unaligned_le32(&msg.dwMaxVideoFrameSize));

    dev->maxPayloadTransferSize =
               get_unaligned_le32(&msg.dwMaxPayloadTransferSize);

    // Now, we can commit the negotiated settings.
    retval = uvc_ctrl(dev, UVC_SET_CUR,
                      UVC_NO_ENTITY, dev->in_intfnum,
                      UVC_VS_STILL_COMMIT_CONTROL,
                      &msg, sizeof(msg), CTRL_TIMEOUT, 3);
    if (retval) { return retval; }

    // Don't verify the committed settings.
    // This appears to be unsupported by the Unity board.
    if (!is_unity(dev)) {
        retval = uvc_ctrl(dev, UVC_GET_CUR,
                                UVC_NO_ENTITY, dev->in_intfnum,
                                UVC_VS_STILL_COMMIT_CONTROL,
                                &msg, sizeof(msg), CTRL_TIMEOUT, 0);
        if (retval) return retval;

        DEBUG("verified "
              "formatIndex=%d frameIndex=%d compressionIndex=%d "
              "maxPayloadTransferSize=%d "
              "maxVideoFrameSize=%d \n",
              msg.bFormatIndex, msg.bFrameIndex, msg.bCompressionIndex,
              get_unaligned_le32(&msg.dwMaxPayloadTransferSize),
              get_unaligned_le32(&msg.dwMaxVideoFrameSize));
    }

    return 0; // success
}

// ---------------------------------------------------
// USB device implementation
// ---------------------------------------------------

// Free everything that needs cleanup.
// This could be called from anywhere, and so it's
// important to first check if the data is valid.
static void cleanup(struct uvc_device *dev)
{
    int i;
    int n_freed = 0;
    struct urb_buffer * ub;

    dev->terminating = true;

    // Wake all
    wake_up_interruptible(&dev->waiting_to_read);
    wake_up_interruptible(&dev->waiting_to_write);
    wake_up_interruptible(&dev->waiting_to_trigger);

    // Flush kernel global workqueue.
    DEBUG("flushing kernel work queue... \n");
    flush_scheduled_work();
    DEBUG("    done \n");

    for(i=0; i<NUM_URBS; ++i) {
        // NOTE: Any URBs that are killed may still have their
        // completion callbacks invoked in the (distant)
        // future with a non-zero status.  Therefore,
        // failing URBs need to tolerate a bad context.
        if (dev->urb[i]) {
            usb_kill_urb(dev->urb[i]);
            usb_free_urb(dev->urb[i]);
            dev->urb[i] = NULL;
        }
    }
    usb_free_urb(dev->int_urb);
    if (dev->buf_pages) {
        for(i=0; i<FRAME_BUF_NUM_PAGES; ++i) {
            kfree(dev->buf_pages[i]); // null ignored
        }
        dev->buf_pages = NULL;
    }

    while(!list_empty(&dev->free_urb_bufs)) {
        ++n_freed;

        ub = list_first_entry(&dev->free_urb_bufs,
                             struct urb_buffer, list);
        kfree(ub->buf);
        list_del(&ub->list);
        kfree(ub);
    }
    DEBUG("freed %d urb buffers \n", n_freed);

    DEBUG("finished cleanup \n");
}


// Callback after probing an interface that matched the
//    one of the descriptor patterns (for the UVC control
//    interface 0).
// This is where we initialize the device driver data and
//    perform any necessary initialize on the hardware.
static int uvc_usb_probe(
    struct usb_interface *intf,
    const struct usb_device_id *id)
{
    struct usb_device *udev = interface_to_usbdev(intf);
    struct uvc_device *dev;
    int i, retval;
    char path[32];
    int retries = 3;

    usb_make_path(udev, path, 32);
    DEBUG("usb probe: %02x %02x at %s\n",
           udev->descriptor.idVendor,
           udev->descriptor.idProduct,
           path);

#ifdef DISABLE_HP_WEBCAM
    if (udev->descriptor.idVendor == 0x058f &&
        udev->descriptor.idProduct == 0x3831)
    {
        DEBUG("ignoring HP webcam \n");
        return 0;
    }
#endif

    // Allocate and initialize our device data
    if ((dev = kzalloc(sizeof *dev, GFP_KERNEL)) == NULL) {
        retval = -ENOMEM;
        goto error;
    }

    dev->udev = usb_get_dev(udev);
    dev->id = next_dev_id++;
    dev->ctrl_intf = usb_get_intf(intf);
    dev->ctrl_intfnum = intf->cur_altsetting->desc.bInterfaceNumber;

    // Allocate frame buffer
    if ((dev->buf_pages = kzalloc(sizeof(void*)*FRAME_BUF_NUM_PAGES, GFP_KERNEL)) == NULL) {
        retval = -ENOMEM;
        goto error;
    }
    for(i=0; i<FRAME_BUF_NUM_PAGES; ++i) {
        if ((dev->buf_pages[i] = kmalloc(FRAME_BUF_PAGE_SIZE, GFP_KERNEL)) == NULL) {
            retval = -ENOMEM;
            goto error;
        }
    }
    dev->buf_head = dev->buf_tail = 0;
    DEBUG("allocated frame buffer of %d KB\n",
          FRAME_BUF_NUM_PAGES*FRAME_BUF_PAGE_SIZE/1024);

    // Init status
    dev->status = STATUS_WAITING;
    dev->streaming = false;
    dev->active_urbs = false;

    // Init locks and queues
    spin_lock_init(&dev->frame_buf_write_lock);
    mutex_init(&dev->frame_buf_read_lock);
    spin_lock_init(&dev->status_lock);
    init_waitqueue_head(&dev->waiting_to_read);
    init_waitqueue_head(&dev->waiting_to_write);
    init_waitqueue_head(&dev->waiting_to_trigger);
    INIT_LIST_HEAD(&dev->free_urb_bufs);
    INIT_LIST_HEAD(&dev->full_urb_bufs);
    spin_lock_init(&dev->urb_bufs_lock);
    INIT_WORK(&dev->process_ubs, uvc_urb_process2);

    // Save device data in usb interface
    usb_set_intfdata(intf, dev);
//    usb_driver_claim_interface(&uvc_usb_driver, intf, NULL);

    // Parse the descriptors to extract hardware details from device
    if ((retval = uvc_parse_ctrl_descriptors(dev))) {
        WARNING("failed to parse descriptors \n");
        goto error;
    }

    // Is there an input stream?
    if (dev->in_intf == NULL) {
        return 0; // success
    }

retry_commands:

    // Reset interface to 0
    if ((retval = usb_set_interface(dev->udev, dev->in_intfnum, 0)) < 0) {
        WARNING("failed to set interface \n");
        goto error;
    }

    // Initialize and enqueue interrupts
    uvc_interrupt_init(dev);

    // Negotiate still image parameters.
    if ((retval = uvc_negotiate_still(dev)) < 0) {
        WARNING("failed to negotiate still parameters \n");
        if (--retries >= 0) goto retry_commands;
        goto error;
    }

    // Negotiate video stream parameters.
    if ((retval = uvc_negotiate_video(dev)) < 0) {
        WARNING("failed to negotiate video stream \n");
        if (--retries >= 0) goto retry_commands;
        goto error;
    }

    // Enable the highest-bandwidth interface.
    DEBUG("setting interface to alternate %d \n", dev->in_altset);
    if ((retval = usb_set_interface(dev->udev, dev->in_intfnum, dev->in_altset)) < 0) {
        WARNING("failed to set interface \n");
        goto error;
    }

    dev->video_frames_since_reset = 0;
    dev->streaming = true;

    // Initialize URBs for data transfer
    if ((retval = uvc_init_data(dev))) {
        WARNING("failed to initialize data URBs \n");
        goto error;
    }

    // Register a device driver
    if ((retval = usb_register_dev(intf, &uvc_usb_class_driver))) {
        WARNING("failed to register class driver \n");
        goto error;
    }

    return 0; // success

error:
    usb_set_intfdata(intf, NULL);
    if (dev) {
        dev->terminating = true;

        cleanup(dev);
        kfree(dev);
        dev = NULL;
    }
    return retval;
}


// Callback when the USB device is disconnected (or when the
//    module is unloaded).
static void uvc_usb_disconnect(struct usb_interface *intf)
{
    struct uvc_device *dev;

    DEBUG("usb disconnect \n");

    dev = usb_get_intfdata(intf);
    usb_set_intfdata(intf, NULL);

    usb_deregister_dev(intf, &uvc_usb_class_driver);
    // usb_driver_release_interface(&uvc_usb_driver, intf);

    // Cleanup
    if (dev) {
        dev->terminating = true;

        // Turn off streaming interface by setting it to alternate 0.
        usb_set_interface(dev->udev, dev->in_intfnum, 0);

        DEBUG("stats: "
               "n_packets=%ld (%ld errors) "
               "n_bytes=%ld \n",
               dev->n_packets, dev->n_packets_with_errors,
               dev->n_bytes_recvd);
        DEBUG("stats: "
               "n_urb_bufs=%d \n",
               (int)dev->n_urb_bufs);

        cleanup(dev);
        kfree(dev);
        dev = NULL;
    }
    DEBUG("usb disconnect done \n");
}


// ---------------------------------------------------
// File operations implementations


// Callback when a device is opened.
static int uvc_dev_open(struct inode *inodep, struct file *filep)
{
    int minor;
    struct usb_interface *intf = NULL;
    struct uvc_device *dev = NULL;

    minor = iminor(inodep);

    // Find interface
    intf = usb_find_interface(&uvc_usb_driver, minor);
    if (intf == NULL) {
        return -ENODEV;
    }
    dev = usb_get_intfdata(intf);
    if (dev == NULL) {
        return -EFAULT;
    }

    DEBUG("Device %d opened \n", dev->id);

    // If another read is in progress, fail.
    spin_lock(&dev->status_lock);

#ifdef EXCLUSIVE_ACCESS
    if (dev->busy) {
        spin_unlock(&dev->status_lock);
        return -EBUSY;
    }
#endif

    filep->private_data = dev;
    dev->busy = true;
    spin_unlock(&dev->status_lock);

    return 0; // success
}


// Callback when a device is closed.
static int uvc_dev_release(struct inode *inodep, struct file *filep)
{
    struct uvc_device *dev = filep->private_data;

    DEBUG("device release \n");

    // Unmark any read that was in progress.
    if (dev) {
        spin_lock(&dev->status_lock);
        dev->busy = false;
        dev->status = STATUS_WAITING;
        spin_unlock(&dev->status_lock);
    }

    return 0; // success
}


// Callback when the device is read from.
static ssize_t uvc_dev_read(struct file *filep, char __user *buf, size_t len, loff_t *loff)
{
    int p, retval;
    ssize_t off, avail, bytes_read = 0;
    struct uvc_device *dev = filep->private_data;
    if (dev == NULL) {
        DEBUG("bad private data\n");
        return -EFAULT;
    }

    mutex_lock(&dev->frame_buf_read_lock);

    while(1) {
        p = dev->buf_tail / FRAME_BUF_PAGE_SIZE;
        off = dev->buf_tail % FRAME_BUF_PAGE_SIZE;
        avail = min(dev->buf_head - dev->buf_tail,
                    (size_t)FRAME_BUF_PAGE_SIZE - off);

        //DEBUG("read data avail = %u \n", avail);
        if (avail > 0) {
            // Data is available.
            break;
        }

        // Finished?
        if (cond_status_transition(dev, STATUS_SUCCESS, STATUS_WAITING))
        {
            DEBUG("read finished \n");
            mutex_unlock(&dev->frame_buf_read_lock);
            // Returning 0 read bytes signals and end-of-file.
            return 0;
        }

        // Error?
        if (cond_status_transition(dev, STATUS_ERROR, STATUS_WAITING))
        {
            DEBUG("read error \n");
            mutex_unlock(&dev->frame_buf_read_lock);
            return -EIO;
        }

        // Terminating?
        if (dev->terminating) {
            return -EFAULT;
        }

        // At this point we're going to need to block.
        // Is this a non-blocking read?
        if (filep->f_flags & O_NONBLOCK) {
            mutex_unlock(&dev->frame_buf_read_lock);
            return -EAGAIN;
        }

        // Block on data.
        // DEBUG("read blocked \n");
        if (wait_event_interruptible(dev->waiting_to_read,
                dev->terminating
                || (dev->status == STATUS_SUCCESS)
                || (dev->status == STATUS_ERROR)
                || (dev->buf_head > dev->buf_tail) ))
        {
            mutex_unlock(&dev->frame_buf_read_lock);
            // DEBUG("read wait interrupted \n");
            return -ERESTARTSYS;
        }
        // DEBUG("read unblocked \n");
    }

    while(1) {
        p = dev->buf_tail / FRAME_BUF_PAGE_SIZE;
        off = dev->buf_tail % FRAME_BUF_PAGE_SIZE;
        // Available bytes is minimum of:
        //    * Total in buffer
        //    * Remaining in current page
        //    * Size of output
        avail = min(dev->buf_head - dev->buf_tail,
                    (size_t)FRAME_BUF_PAGE_SIZE - off);
        avail = min(len, (size_t)avail);
        if (avail <= 0) {
            break;
        }

        retval = copy_to_user(buf, dev->buf_pages[p] + off, avail);
        if (retval) {
            WARNING("read error copying to user buffer\n");
            mutex_unlock(&dev->frame_buf_read_lock);
            return -EFAULT;
        }

        bytes_read += avail;
        buf += avail;
        len -= avail;
        dev->buf_tail += avail;
    }

    mutex_unlock(&dev->frame_buf_read_lock);

    wake_up_interruptible(&dev->waiting_to_write);

    // DEBUG("read %u bytes \n", bytes_read);
    return bytes_read;
}


// Callback when the device is written to.
static ssize_t uvc_dev_write(struct file *filep, const char *buf, size_t len, loff_t *off)
{
    return 0;
}


// Wait until the device is ready and then trigger a still image capture.
static int uvc_trigger_still(struct uvc_device *dev)
{
    int retval;
    u8 trigger_msg = 0;

    if (!dev->streaming || !dev->active_urbs) {
        WARNING("Can't trigger inactive device");
        return 1; // fail
    }

    if (dev->status != STATUS_TRIGGERABLE) {
        DEBUG("waiting for camera to be ready... \n");
    }

    if (wait_event_interruptible(dev->waiting_to_trigger,
            dev->terminating || dev->status == STATUS_TRIGGERABLE) )
    {
        return 1; // fail
    }

    trigger_msg = 1;
    retval = uvc_ctrl(dev, UVC_SET_CUR,
                            UVC_NO_ENTITY, dev->in_intfnum,
                            UVC_VS_STILL_IMAGE_TRIGGER_CONTROL,
                            &trigger_msg, 1, CTRL_TIMEOUT, 0);

    if (retval) return retval;

    DEBUG("triggered still image \n");

    dev->buf_head = dev->buf_tail = 0;

    return 0; // success
}


static int uvc_suspend(struct uvc_device *dev) {
    int retval;
    DEBUG("Supending interface\n");
    if ((retval = usb_set_interface(dev->udev, dev->in_intfnum, 0))) {
        WARNING("Failed to suspend interface.  Error %d\n", retval);
    }
    return retval;
}


static int uvc_resume(struct uvc_device *dev) {
    int retval;
    DEBUG("Resuming interface\n");
    if ((retval = usb_set_interface(dev->udev, dev->in_intfnum, dev->in_altset))) {
        WARNING("failed to resume interface\n");
    }
    dev->video_frames_since_reset = 0;
    dev->status = STATUS_WAITING;
    return retval;
}


// Callback when a device ioctl command is issued.
static long uvc_dev_ioctl(struct file *filep, unsigned int cmd, unsigned long arg)
{
    int retval;
    struct uvc_device *dev = NULL;

    dev = filep->private_data;

    DEBUG("ioctl cmd=%d arg=%0lx\n", cmd, arg);

    switch(cmd) {
    case UVC_IOCTL_STOP:
    {
        if ((retval = uvc_suspend(dev))) {
            return retval;
        }

        uvc_kill_urbs(dev);

        dev->streaming = false;

        return 0; // success
    }
    break;

    case UVC_IOCTL_START:
    {
        dev->streaming = true;

        if ((retval = uvc_negotiate_still(dev))) {
            return retval;
        }

        if ((retval = uvc_negotiate_video(dev))) {
            return retval;
        }

        if ((retval = uvc_resume(dev))) {
            return retval;
        }

        uvc_submit_urbs(dev);

        return 0; // success
    }
    break;

    case UVC_IOCTL_SUSPEND:
    {
        uvc_kill_urbs(dev);
        return 0; // success
    }
    break;

    case UVC_IOCTL_RESUME:
    {
        uvc_submit_urbs(dev);
        return 0; // success
    }
    break;

    case UVC_IOCTL_TRIGGER_STILL_IMAGE:
    {
        return uvc_trigger_still(dev);
    }
    break;

    case UVC_IOCTL_GET_FRAME_SIZE:
    {
        struct uvc_still_frame_size data;
        data.width = dev->frameSizeWidth[dev->frameSizeIdx];
        data.height = dev->frameSizeHeight[dev->frameSizeIdx];

        if ((retval = copy_to_user((void __user *)arg, &data, sizeof(data)))) {
            return retval;
        }

        return 0; // success
    }
    break;

    case UVC_IOCTL_SET_FRAME_SIZE:
    {
        int i, new_index = -1;
        struct uvc_still_frame_size data;

        if ((retval = copy_from_user(&data, (void __user *)arg, sizeof(data)))) {
            return retval;
        }

        for(i=0; i<NUM_STILL_SIZE_PATTERNS; ++i) {
            if (dev->frameSizeWidth[i] == data.width &&
                dev->frameSizeHeight[i] == data.height)
            {
                new_index = i;
                break;
            }
        }

        if (new_index < 0) {
            // Failed to find
            DEBUG("Frame size %d %d is invalid \n", data.width, data.height);
            return -1;
        } else {
            DEBUG("Frame size %d %d is index %d \n", data.width, data.height, new_index);
        }
        dev->frameSizeIdx = new_index;

        if ((retval = uvc_negotiate_still(dev))) {
            WARNING("Failed to negotatiate still parameters");
            return retval;
        }

        if ((retval = uvc_negotiate_video(dev))) {
            WARNING("Failed to negotatiate video parameters");
            return retval;
        }

        uncond_status_transition(dev, STATUS_WAITING);

        DEBUG("set frame size successfully\n");

        return 0; // success
    }
    break;

    case UVC_IOCTL_SET_CAMERA_PROPERTY:
    {
        u8 buf[64];
        struct uvc_still_unit_property * data =
            (struct uvc_still_unit_property *)buf;

        // Copy fixed data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) )))
        {
            return retval;
        }
        // Does the variable data fit?
        if (data->data_len + sizeof(struct uvc_still_unit_property) > sizeof(buf)) {
            return -ENOMEM;
        }
        // Copy variable data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) + data->data_len )))
        {
            return retval;
        }
        // Validate request type
        if (data->request != UVC_SET_CUR) {
            WARNING("Unknown request type\n");
            return 1;
        }

        // We send a request with the desired parameters...
        retval = uvc_ctrl(dev, data->request,
                                dev->cameraID, 0,
                                data->controlSelector,
                                &data->data,
                                data->data_len,
                                CTRL_TIMEOUT, 0);
        if (retval) return retval;

        return 0; // success
    }
    break;


    case UVC_IOCTL_GET_CAMERA_PROPERTY:
    {
        u8 buf[64];
        struct uvc_still_unit_property * data =
            (struct uvc_still_unit_property *)buf;

        // Copy fixed data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) )))
        {            return retval;
        }
        // Does the variable data fit?
        if (data->data_len + sizeof(struct uvc_still_unit_property) > sizeof(buf)) {
            return -ENOMEM;
        }
        // Validate request type
        if (data->request != UVC_GET_CUR &&
            data->request != UVC_GET_MIN &&
            data->request != UVC_GET_MAX &&
            data->request != UVC_GET_RES &&
            data->request != UVC_GET_DEF)
        {
            WARNING("Unknown request type\n");
            return 1;
        }

        // We send a request with the desired parameters...
        retval = uvc_ctrl(dev, data->request,
                                dev->cameraID, 0,
                                data->controlSelector,
                                &data->data,
                                data->data_len,
                                CTRL_TIMEOUT, 0);
        if (retval) return retval;

        // Copy variable data
        if ((retval = copy_to_user((u8 __user *)arg + sizeof(struct uvc_still_unit_property),
                                   data->data, data->data_len)))
        {
            return retval;
        }

        return 0; //success
    }
    break;

    case UVC_IOCTL_SET_EXTENSION_PROPERTY:
    case UVC_IOCTL_SET_PROCESSING_PROPERTY:
    {
        int unit = (cmd == UVC_IOCTL_SET_EXTENSION_PROPERTY)
                   ? dev->extensionID : dev->processingID;
        u8 buf[64];
        struct uvc_still_unit_property * data =
            (struct uvc_still_unit_property *)buf;

        // Copy fixed data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) )))
        {
            return retval;
        }
        // Does the variable data fit?
        if (data->data_len + sizeof(struct uvc_still_unit_property) > sizeof(buf)) {
            return -ENOMEM;
        }
        // Copy variable data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) + data->data_len )))
        {
            return retval;
        }
        // Validate request type
        if (data->request != UVC_SET_CUR) {
            WARNING("Unknown request type\n");
            return 1;
        }

        // We send a request with the desired parameters...
        retval = uvc_ctrl(dev, data->request,
                                unit, 0,
                                data->controlSelector,
                                &data->data,
                                data->data_len,
                                CTRL_TIMEOUT, 0);
        if (retval) return retval;

        return 0; // success
    }
    break;

    case UVC_IOCTL_GET_EXTENSION_PROPERTY:
    case UVC_IOCTL_GET_PROCESSING_PROPERTY:
    {
        int unit = (cmd == UVC_IOCTL_GET_EXTENSION_PROPERTY)
                   ? dev->extensionID : dev->processingID;
        u8 buf[64];
        struct uvc_still_unit_property * data =
            (struct uvc_still_unit_property *)buf;

        // Copy fixed data
        if ((retval = copy_from_user(data, (void __user *)arg,
                                     sizeof(struct uvc_still_unit_property) )))
        {
            WARNING("Bad user buffer (inaccessible command)\n");
            return retval;
        }
        // Does the variable data fit?
        if (data->data_len + sizeof(struct uvc_still_unit_property) > sizeof(buf)) {
            WARNING("Bad user buffer (size)\n");
            return -ENOMEM;
        }
        // Validate request type
        if (data->request != UVC_GET_CUR &&
            data->request != UVC_GET_MIN &&
            data->request != UVC_GET_MAX &&
            data->request != UVC_GET_RES &&
            data->request != UVC_GET_DEF)
        {
            WARNING("Unknown request type\n");
            return 1;
        }

        // We send a request with the desired parameters...
        retval = uvc_ctrl(dev, data->request,
                                unit, 0,
                                data->controlSelector,
                                &data->data,
                                data->data_len,
                                CTRL_TIMEOUT, 0);
        if (retval) return retval;

        // Copy variable data
        if ((retval = copy_to_user((u8 __user *)arg + sizeof(struct uvc_still_unit_property),
                                   data->data, data->data_len)))
        {
            return retval;
        }

        return 0; // success
    }
    break;

    default:
    break;
    }

    // Unsupposed ioctl commands should return ENOTTY
    return -ENOTTY;
}

// ---------------------------------------------------
// Module implementations


// Called when the module is loaded.
// The interesting initialization happens when an interesting
//    USB interface is probed.
static int __init uvcstill_init(void)
{
    int ret = usb_register(&uvc_usb_driver);
    if (ret < 0) {
        DEBUG("init failed \n");
        return ret;
    }

    DEBUG("init succeeded \n");
    return 0; // success
}


// Called when the module is unloaded.
// The important cleanup happens when the USB device driver
//    is disconnected (which will be triggered by
//    usb_deregister).
static void __exit uvcstill_exit(void)
{
    usb_deregister(&uvc_usb_driver);

    DEBUG("unloaded \n");
}

module_init(uvcstill_init);
module_exit(uvcstill_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Aaron Hurst");
MODULE_DESCRIPTION("USB Video Class Still Frame Capture");
