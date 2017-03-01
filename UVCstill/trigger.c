/**
 * @file trigger.c
 * @author Aaron Hurst SpaceVR(TM)
 * @date 06/28/16
 * @link www.cajunbot.com/wiki/images/8/85/USB_Video_Class_1.1.pdf
 * @version 1.0
 *
 * @brief UVC Still Capture Trigger Application
 * 
 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>		/* open */
#include <unistd.h>		/* exit */
#include <sys/ioctl.h>  /* ioctl */

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
