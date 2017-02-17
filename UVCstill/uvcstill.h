// ----------------------------------------------------------
// UVC Still Capture Linux Driver
//
// Copyright SpaceVR, 2016.  All rights reserved.
//
// Author: Aaron Hurst (aaronpaulhurst@gmail.com)
// Date:   June 28, 2016
// ----------------------------------------------------------

#ifndef MODULE
#include <stdint.h>
#endif

// Magic ioctl number to trigger still image capture.
#define UVC_IOCTL_TRIGGER_STILL_IMAGE 1226

// Magic ioctl number to set/get frame size.
#define UVC_IOCTL_SET_FRAME_SIZE 1227
#define UVC_IOCTL_GET_FRAME_SIZE 1228

struct uvc_still_frame_size {
    uint32_t width;
    uint32_t height;
};

// Magic ioctl number to suspend/resume streaming.
#define UVC_IOCTL_SUSPEND 1229
#define UVC_IOCTL_RESUME 1230

// Magic ioctl number to set/get a camera property.
#define UVC_IOCTL_SET_CAMERA_PROPERTY 1231
#define UVC_IOCTL_GET_CAMERA_PROPERTY 1232

// Magic ioctl number to set/get a processing unit property.
#define UVC_IOCTL_SET_PROCESSING_PROPERTY 1233
#define UVC_IOCTL_GET_PROCESSING_PROPERTY 1234

struct uvc_still_unit_property {
    uint16_t data_len;
    uint8_t controlSelector;
    uint8_t request;
    uint8_t data[];
};

// Magic ioctl number to set/get a extension unit property.
#define UVC_IOCTL_SET_EXTENSION_PROPERTY 1235
#define UVC_IOCTL_GET_EXTENSION_PROPERTY 1236

// Magic ioctl number to start/stop streaming.
// NOTE: This is only valid for isoc endpoints.
#define UVC_IOCTL_START 1237
#define UVC_IOCTL_STOP 1238

// --------------------------------------------
// These are unity-specific camera registers.

#define EX_EXPOSURE_MODE 0x01
// Length: 1.  Values: 0 = Auto, 1 = Hold, 2 = Manual, 3 = Shutter, 4 = ISO

#define EX_EV_CORRECTION 0x02
// Length: 2.  Values: [-6, 6]

#define EX_SHUTTER_SPEED 0x0A
// Length: 1.  Values: [1, 38]

#define EX_GAIN 0x0B
// Length: 2.  Values: [1, 65535]  Default: 800

#define EX_FIRMWARE_REV 0x15
// Length: 8.  Read-only
