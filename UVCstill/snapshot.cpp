// UVC Still Capture User Application
//
// Copyright SpaceVR, 2016.  All rights reserved.
//
// Author: Aaron Hurst (aaronpaulhurst@gmail.com)
// Date:   June 28, 2016

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include "uvcstill.h"
#include <iostream>
#include <fstream>
#include <png.h>
#include <linux/usb/video.h>
#include "le_byteshift.h"
#include <turbojpeg.h>

using namespace std;

typedef unsigned char u8;

// Frame dimensions
int g_width = 0, g_height = 0;

// Image quality (for JPG only)
int g_jpg_quality = 70;

// --------------------------------------------------------
// Image Manipulation
// --------------------------------------------------------

int write_jpg(FILE *fp, u8 *buf) {
   tjhandle jpegCompressor = tjInitCompress();

   long unsigned int out_size = 0;
   u8 * out_buf = NULL;

   tjCompress2(jpegCompressor, buf, g_width, 0, g_height, TJPF_RGB,
              &out_buf, &out_size, TJSAMP_422, g_jpg_quality,
              TJFLAG_FASTDCT);

   fwrite (out_buf, sizeof(char), out_size, fp);

   tjDestroy(jpegCompressor);
   tjFree(out_buf);

   return 0; // success
}

int write_png(FILE *fp, u8 *buf) {

    png_structp png_ptr = png_create_write_struct
       (PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png_ptr)
       return 1; // error

    png_infop info_ptr = png_create_info_struct(png_ptr);
    if (!info_ptr)
    {
       png_destroy_write_struct(&png_ptr,
           (png_infopp)NULL);
       return 1; // error
    }

    png_init_io(png_ptr, fp);

    png_set_IHDR(png_ptr, info_ptr,
                 g_width, g_height,
                 8 /*bit_depth*/,
                 PNG_COLOR_TYPE_RGB /*color_type*/,
                 PNG_INTERLACE_NONE /*interlace_type*/,
                 PNG_COMPRESSION_TYPE_DEFAULT /*compression_type*/,
                 PNG_FILTER_TYPE_DEFAULT /*filter_method*/);

    png_byte *row_pointers[g_height];
    for(int i=0; i<g_height; ++i) {
        row_pointers[i] = buf + (i*g_width*3 /*one byte per R, G,B */);
    }

    png_write_info(png_ptr, info_ptr);
    png_write_image(png_ptr, row_pointers);
    png_write_end(png_ptr, info_ptr);

    png_destroy_write_struct(&png_ptr, &info_ptr);

    return 0; // success
}


// Writes a rainbox(?) image file to rainbow.png.
void test_write_png() {
    FILE * outfile = fopen("rainbow.png", "w");
    if (outfile == NULL) {
        cout << "Can't open output file" << endl;
        exit(-1);
    }

    u8 * buf = new u8[640*480*3];
    for(int i=0; i<640*480; ++i) {
        buf[i*3+0] = (i%255);
        buf[i*3+1] = ((i+100)%255);
        buf[i*3+2] = ((i+200)%255);
    }
    write_png(outfile, buf);

    delete [] buf;
}


// Convert YUV bytes into RGB bytes.
static void yuv_to_rgb_pixel(
    int y, int u, int v,
    u8 *r, u8 *g, u8 *b)
{
    int r0, g0, b0;

    u -= 128;
    v -= 128;
    r0 = y + v + (v>>2) + (v>>3) + (v>>5);
    g0 = y - ((u>>2) + (u>>4) + (u>>5)) - ((v>>1) + (v>>3) + (v>>4) + (v>>5));
    b0 = y + u + (u>>1) + (u>>2) + (u>>6);

    if (r0 < 0) r0 = 0; if (r0 > 255) r0 = 255;
    if (g0 < 0) g0 = 0; if (g0 > 255) g0 = 255;
    if (b0 < 0) b0 = 0; if (b0 > 255) b0 = 255;

    *r = r0;
    *g = g0;
    *b = b0;
}


static void yuyv_to_rgb(
        u8 * yuyv_buf,
        u8 * rgb_buf)
{
    for(int i=0; i<(g_width*g_height >> 1); ++i) {

        yuv_to_rgb_pixel(
            yuyv_buf[i*4],
            yuyv_buf[i*4+1],
            yuyv_buf[i*4+3],
            &rgb_buf[i*6+0],
            &rgb_buf[i*6+1],
            &rgb_buf[i*6+2]);

        yuv_to_rgb_pixel(
            yuyv_buf[i*4+2],
            yuyv_buf[i*4+1],
            yuyv_buf[i*4+3],
            &rgb_buf[i*6+3],
            &rgb_buf[i*6+4],
            &rgb_buf[i*6+5]);
    }

}


static void yuyv_to_rgb_grayscale(
        u8 * yuyv_buf,
        u8 * rgb_buf)
{
    for(int i=0; i<g_width*g_height; ++i) {
        rgb_buf[i*3+0] = yuyv_buf[i*2];
        rgb_buf[i*3+1] = yuyv_buf[i*2];
        rgb_buf[i*3+2] = yuyv_buf[i*2];
    }

}


// --------------------------------------------------------
// Device commands
// --------------------------------------------------------

// Triggers the capture of a still image
void trigger_image(int devfd) {
    if (ioctl(devfd, UVC_IOCTL_TRIGGER_STILL_IMAGE, NULL)) {
        cout << "Failed to trigger still" << endl;
        throw std::exception();
    }
}


// Pause streaming
void suspend_stream(int devfd) {
    if (ioctl(devfd, UVC_IOCTL_SUSPEND, NULL)) {
        cout << "Failed to suspend stream" << endl;
        throw std::exception();
    }
}
void resume_stream(int devfd) {
    if (ioctl(devfd, UVC_IOCTL_RESUME, NULL)) {
        cout << "Failed to resume stream" << endl;
        throw std::exception();
    }
}
void start_stream(int devfd) {
    if (ioctl(devfd, UVC_IOCTL_START, NULL)) {
        cout << "Failed to start stream" << endl;
        throw std::exception();
    }
}
void stop_stream(int devfd) {
    if (ioctl(devfd, UVC_IOCTL_STOP, NULL)) {
        cout << "Failed to stop stream" << endl;
        throw std::exception();
    }
}



// Queries the uvcstill device for its current frame size.
//   - 'devfd' is an open file descriptor to /dev/still0 etc.
//   - 'width' and 'height' are the returned values
void get_frame_size(int devfd, int & width, int &height) {
    struct uvc_still_frame_size sz;

    if (ioctl(devfd, UVC_IOCTL_GET_FRAME_SIZE, &sz)) {
        cout << "Error querying frame size" << endl;
        throw std::exception();
    }

    width = sz.width;
    height = sz.height;
}


static inline void put_byte(uint8_t b, void * p) { *(uint8_t *)p = b; }
static inline uint8_t get_byte(void * p) { return *(uint8_t *)p; }


// Set the exposure MODE of the uvcstill device.
void set_exposure_mode(int devfd, uint8_t mode) {
    char buf[sizeof(uvc_still_unit_property)+1] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->controlSelector = UVC_CT_AE_MODE_CONTROL;
    p->request = UVC_SET_CUR;
    p->data_len = 1;
    put_byte(mode, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_CAMERA_PROPERTY, p)) {
        cout << "Error setting exposure" << endl;
        throw std::exception();
    }
}


// Set the exposure of the uvcstill device.
//   - 'exposure' is units of 100us
void set_exposure(int devfd, uint32_t exposure) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_SET_CUR;
    p->controlSelector = UVC_CT_EXPOSURE_TIME_ABSOLUTE_CONTROL;
    p->data_len = 4;
    put_unaligned_le32(exposure, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_CAMERA_PROPERTY, p)) {
        cout << "Error setting exposure" << endl;
        throw std::exception();
    }
}


// Get the exposure of the uvcstill device.
// Result is units of 100us
uint32_t get_exposure(int devfd, int request) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = request;
    p->controlSelector = UVC_CT_EXPOSURE_TIME_ABSOLUTE_CONTROL;
    p->data_len = 4;

    if (ioctl(devfd, UVC_IOCTL_GET_CAMERA_PROPERTY, p)) {
        cout << "Error getting exposure" << endl;
        throw std::exception();
    }

    return get_unaligned_le32(p->data);
}


// Get the exposure mode of a *unity* device.
uint8_t get_unity_exposure_mode(int devfd) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_GET_CUR;
    p->controlSelector = EX_EXPOSURE_MODE;
    p->data_len = 1;

    if (ioctl(devfd, UVC_IOCTL_GET_EXTENSION_PROPERTY, p)) {
        cout << "Error getting exposure mode" << endl;
        throw std::exception();
    }

    return get_byte(p->data);
}


// Set the exposure mode of a *unity* device.
void set_unity_exposure_mode(int devfd, int mode) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_SET_CUR;
    p->controlSelector = EX_EXPOSURE_MODE;
    p->data_len = 1;
    put_byte((uint8_t)mode, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_EXTENSION_PROPERTY, p)) {
        cout << "Error setting exposure mode" << endl;
        throw std::exception();
    }
}


// Get the shutter speed of a *unity* device.
uint8_t get_unity_shutter_speed(int devfd) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_GET_CUR;
    p->controlSelector = EX_SHUTTER_SPEED;
    p->data_len = 1;

    if (ioctl(devfd, UVC_IOCTL_GET_EXTENSION_PROPERTY, p)) {
        cout << "Error getting shutter speed" << endl;
        throw std::exception();
    }

    return get_byte(p->data);
}


// Set the shutter speed of a *unity* device.
//
// See the Unity technical manual for a mapping of
//   the 'speed' value to real-life shutter times.
void set_unity_shutter_speed(int devfd, int speed) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_SET_CUR;
    p->controlSelector = EX_SHUTTER_SPEED;
    p->data_len = 1;
    put_byte((uint8_t)speed, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_EXTENSION_PROPERTY, p)) {
        cout << "Error setting shutter speed" << endl;
        throw std::exception();
    }
}


// Set the ISO value of a *unity* device.
//
// See the Unity technical manual for a mapping of
//   the 'iso' value.
void set_unity_iso_value(int devfd, int iso) {
    char buf[sizeof(uvc_still_unit_property)+4] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_SET_CUR;
    p->controlSelector = EX_GAIN;
    p->data_len = 2;
    put_unaligned_le16((uint16_t)iso, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_EXTENSION_PROPERTY, p)) {
        cout << "Error setting ISO value" << endl;
        throw std::exception();
    }
}


// Set the brightness of the uvcstill device.
//   - 'brightness' is a signed relative value
void set_brightness(int devfd, uint16_t brightness) {
    char buf[sizeof(uvc_still_unit_property)+2] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_SET_CUR;
    p->controlSelector = UVC_PU_BRIGHTNESS_CONTROL;
    p->data_len = 2;
    put_unaligned_le16(brightness, p->data);

    if (ioctl(devfd, UVC_IOCTL_SET_PROCESSING_PROPERTY, p)) {
        cout << "Error setting brightness" << endl;
        throw std::exception();
    }
}


// Get the brightness of the uvcstill device.
uint16_t get_brightness(int devfd, int request) {
    char buf[sizeof(uvc_still_unit_property)+2] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = request;
    p->controlSelector = UVC_PU_BRIGHTNESS_CONTROL;
    p->data_len = 2;

    if (ioctl(devfd, UVC_IOCTL_GET_PROCESSING_PROPERTY, p)) {
        cout << "Error getting brightness" << endl;
        throw std::exception();
    }

    return get_unaligned_le16(p->data);
}


// Get the unity firmware revision.
void get_firmware_revision(int devfd) {
    char buf[sizeof(uvc_still_unit_property)+10] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = UVC_GET_CUR;
    p->controlSelector = EX_FIRMWARE_REV;
    p->data_len = 8;

    if (ioctl(devfd, UVC_IOCTL_GET_EXTENSION_PROPERTY, p)) {
        cout << "Error reading firmware revision" << endl;
        throw std::exception();
    }

    cout << "Firmware version = " << (char *)(p->data) << endl;
}



// Set the brightness of the uvcstill device.
//   - 'brightness' is a signed relative value
uint16_t get_PU_prop16(int devfd, int req, int cs) {
    char buf[sizeof(uvc_still_unit_property)+2] = {0};
    struct uvc_still_unit_property * p =
        (struct uvc_still_unit_property *)buf;

    p->request = req;
    p->controlSelector = cs;
    p->data_len = 2;

    if (ioctl(devfd, UVC_IOCTL_GET_PROCESSING_PROPERTY, p)) {
        cout << "Error getting ??? property" << endl;
        throw std::exception();
    }

    return get_unaligned_le16(p->data);
}


// Set the current frame size of a uvcstill device.
// If the device does not support the *exact* width and
//   height values, the frame size will remain unchanged.
// See the STILL_IMAGE_FRAME descriptor via 'lsusb -v '.
//   - 'devfd' is an open file descriptor to /dev/still0 etc.
//   - 'width' and 'height' are the new values
void set_frame_size(int devfd, int width, int height) {
    struct uvc_still_frame_size sz;
    sz.width = width;
    sz.height = height;

    if (ioctl(devfd, UVC_IOCTL_SET_FRAME_SIZE, &sz)) {
        cout << "Error setting frame size.  Only supported "
             << "dimension values are allowed.  See the STILL_IMAGE_FRAME "
             << "descriptor via 'lsusb -v' for valid sizes." << endl;
        throw std::exception();
    }
}


// --------------------------------------------------------
// Main
// --------------------------------------------------------


long get_msec() {
    struct timeval tp;
    gettimeofday(&tp, NULL);
    return tp.tv_sec * 1000 + tp.tv_usec / 1000;
}


// Program entry point
int main(int argc, char **argv)
{
    long start_time = get_msec();
    u8 * yuyv_buf = NULL;

    // Print usage
    if (argc < 2) {
        cout << "Usage: snapsnot [OPTIONS...] <output file>" << endl;
        cout << endl;
        cout << "   --dev <filename>        : use camera device file (e.g. /dev/still0)" << endl;
        cout << "   --format <type>         : output format: none, png (default), jpg, or yuyv" << endl;
        cout << "   --size <width> <height> : frame size" << endl;
        cout << "   --jpg-quality [1...100] : image quality, for JPEG format (default: 70)" << endl;
        cout << "Exposure control: " << endl;
        cout << "   --auto-exposure         : use auto exposure" << endl;
        cout << "   --shutter <index>       : shutter speed index" << endl;
        cout << "   --iso <val>             : iso value" << endl;
        // cout << "   --exposure <val>        : exposure time, in units of 100us" << endl;
        // cout << "   --brightness <val>      : brightness" << endl;
        cout << "Streaming control:" << endl;
        cout << "   --suspend               : (soft) suspend streaming after capture" << endl;
        cout << "   --resume                : (soft) resume streaming before capture" << endl;
        return 1; // failure
    }

    // Parse options
    const char * outfilename = NULL;
    const char * devfile = "/dev/still0";
    int width = 0;
    int height = 0;
    int exposure = 0;
    int brightness = 0;
    bool auto_exposure = false;
    int shutter_speed = 0, iso_value = 0;
    bool suspend = false, resume = false;
    const char * format = "png";

    for(int i=1; i<argc; ++i) {
        const char * opt = argv[i];

        if (!strcmp(opt, "--dev")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                devfile = argv[i+1];
                i += 1;
            } else {
                cout << "Option --dev requires an argument" << endl;
            }
        }
        else if (!strcmp(opt, "--format")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                format = argv[i+1];
                i += 1;
            } else {
                cout << "Option --format requires an argument" << endl;
                return 1;
            }
            if (strcmp(format, "png")
                    && strcmp(format, "none")
                    && strcmp(format, "yuyv")
                    && strcmp(format, "jpg"))
            {
                cout << "Output format is not valid" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--jpg-quality")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                g_jpg_quality = atoi(argv[i+1]);
                i += 1;
            } else {
                cout << "Option --jpg-quality requires an argument" << endl;
                return 1;
            }
            if (g_jpg_quality < 1 || g_jpg_quality > 100) {
                cout << "Option --jpg-quality takes a value between 1 and 100" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--size")) {
            if (i+2 < argc && argv[i+1][0] != '-' && argv[i+2][0] != '-') {
                width = atoi(argv[i+1]);
                height = atoi(argv[i+2]);
                i += 2;
            } else {
                cout << "Option --size requires two arguments" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--auto-exposure")) {
            auto_exposure = true;
        }
        else if (!strcmp(opt, "--shutter")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                shutter_speed = atoi(argv[i+1]);
                i += 1;
            } else {
                cout << "Option --shutter requires an argument" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--iso")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                iso_value = atoi(argv[i+1]);
                i += 1;
            } else {
                cout << "Option --iso requires an argument" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--exposure")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                exposure = atoi(argv[i+1]);
                i += 1;
            } else {
                cout << "Option --exposure requires an argument" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--brightness")) {
            if (i+1 < argc && argv[i+1][0] != '-') {
                brightness = atoi(argv[i+1]);
                i += 1;
            } else {
                cout << "Option --brightness requires an argument" << endl;
                return 1;
            }
        }
        else if (!strcmp(opt, "--suspend")) { suspend = true; }
        else if (!strcmp(opt, "--resume")) { resume = true; }
        else if (!outfilename) {
            outfilename = argv[i];
        }
        else {
            cout << "Unexpected option: " << opt << endl;
            return 1;
        }
    }
    if (!outfilename) {
        cout << "Output filename required" << endl;
        return 1;
    }

    // Open camera device
    FILE * dev = fopen(devfile, "rb");
    if (dev == NULL) {
        cout << "Can't open device file" << endl;
        exit(-1);
    }
    int devfd = fileno(dev);
    cout << "Opened camera device " << devfile << endl;

    int actual_bytes = 0;

    try {

        // Query or set frame size
        get_frame_size(devfd, g_width, g_height);
        cout << "Frame size (prev) = " << g_width << " x " << g_height << endl;
        if (width && height) {
            g_width = width, g_height = height;
        }
        set_frame_size(devfd, g_width, g_height);
        cout << "Frame size (cur)  = " << g_width << " x " << g_height << endl;

        if (g_width*g_height < 0 || g_width*g_height > 30*1024*1024 /*30MB*/) {
            // Sanity checking the frame size failed
            cout << "Bad frame size" << endl;
            throw std::exception();
        }

        // Set exposure and/or shutter speed
        if ( (auto_exposure ? 1 : 0) +
             (shutter_speed ? 1 : 0) +
             (iso_value ? 1 : 0) > 1)
        {
            cout << "Exposure can be specified *either* by ISO value, "
                    "shutter speed, or automatically." << endl;
            throw std::exception();
        }
        else if (auto_exposure) {
            set_unity_exposure_mode(devfd, 0 /*auto*/);
        }
        else if (shutter_speed) {
            set_unity_exposure_mode(devfd, 3 /*shutter*/);
            set_unity_shutter_speed(devfd, shutter_speed);
        }
        else if (iso_value) {
            set_unity_exposure_mode(devfd, 4 /*iso value*/);
            set_unity_iso_value(devfd, iso_value);
        }

#if 0
        // Get/set brightness
        cout << "Brightness = " << get_brightness(devfd, UVC_GET_CUR) << endl;
        if (brightness) {
            set_brightness(devfd, brightness);
            cout << "Set brightness" << endl;
        }
#endif

        if (resume) { resume_stream(devfd); }

        // Trigger capture
        trigger_image(devfd);

        // Initialize buffer
        yuyv_buf = new u8[g_width*g_height*2];
        memset(yuyv_buf, 0, g_width*g_height*2);

        // Read image
        actual_bytes = fread(yuyv_buf, 1, g_width*g_height*2, dev);
        cout << "Read returned " << actual_bytes/1024 << " KB" << endl;
        cout << "Read time = " << (get_msec()-start_time)/1000.0 << " secs" << endl;

        if (suspend) { suspend_stream(devfd); }
    }
    catch(...) {
        if (yuyv_buf) {
            delete [] yuyv_buf;
        }

        fclose(dev);
        cout << "Closed device" << endl;
        exit(1);
    }

    fclose(dev);
    cout << "Closed device" << endl;

    // Did we get a complete image?
    if (actual_bytes < g_width*g_height*2) {
        cout << "Read ***INCOMPLETE*** frame.  Skipping output" << endl;
        exit(-1);
    } else {
        cout << "Read ***FULL*** frame succesfully" << endl;
    }

    // Open output file for writing (unless format is "none")
    FILE * outfile = NULL;
    if (strcmp(format, "none")) {
        outfile = fopen(outfilename, "wb");
        if (outfile == NULL) {
            cout << "Can't open output file" << endl;
            exit(-1);
        }
    }

    // Write output
    if (!strcmp(format, "png")) {
        // Convert YUYV to RGB
        cout << "Converting buffer to RGB..." << endl;
        u8 * rgb_buf = new u8[g_width*g_height*3];
        // yuyv_to_rgb_grayscale(yuyv_buf, rgb_buf);
        yuyv_to_rgb(yuyv_buf, rgb_buf);

        // Write out file
        cout << "Writing PNG output..." << endl;
        write_png(outfile, rgb_buf);

        delete [] rgb_buf;
    }
    else if (!strcmp(format, "jpg")) {
        // Convert YUYV to RGB
        cout << "Converting buffer to RGB..." << endl;
        u8 * rgb_buf = new u8[g_width*g_height*3];
        yuyv_to_rgb(yuyv_buf, rgb_buf);

        // Write out file
        cout << "Writing JPG output..." << endl;
        write_jpg(outfile, rgb_buf);

        delete [] rgb_buf;
    }
    else if (!strcmp(format, "yuyv")) {
        // Save raw YUYV bytes
        cout << "Writing raw output..." << endl;
        fwrite(yuyv_buf, 1, g_width*g_height*2, dev);
    }
    else if (!strcmp(format, "none")) {
        // No output
    }

    if (outfile) {
        fclose(outfile);
    }

    delete [] yuyv_buf;

    cout << "Total time = " << (get_msec()-start_time)/1000.0 << " secs" << endl;
}
