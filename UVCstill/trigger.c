// UVC Still Capture Trigger Application
//
// Copyright SpaceVR, 2016.  All rights reserved.
//
// Author: Aaron Hurst (aaronpaulhurst@gmail.com)
// Date:   June 28, 2016

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>		/* open */
#include <unistd.h>		/* exit */
#include <sys/ioctl.h>		/* ioctl */
#include "uvcstill.h"

int main(int argc, char **argv)
{
    int fd = open("/dev/still0", 0);
    if (fd < 0) {
        printf("Can't open device file\n");
        exit(-1);
    }

    int code = UVC_IOCTL_TRIGGER_STILL_IMAGE;
    if (argc > 1) {
        code = atoi(argv[1]);
    }

    int rv = ioctl(fd, code, 0);
    printf("Ioctl %d returned %d\n", code, rv);

    close(fd);
}
