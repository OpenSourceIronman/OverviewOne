// ----------------------------------------------------------
// UVC Still Capture Linux Driver
//
// Copyright SpaceVR, 2016.  All rights reserved.
// ----------------------------------------------------------

I.  Building the driver

Requirements:
  * Standard development tools: gcc, g++, make
  * Linux kernel headers and build script (for installed kernel)
    See below.
  * libpng development package
    Run: sudo apt-get install libpng12-dev
  * libwebp development package
    Run: sudo apt-get install libwebp-dev
  * libjpeg-turbo development package
    Run: sudo apt-get install libjpeg-turbo8-dev

Running 'make' in the project directory will compile the module and
several small utilities.

I.1.  How to get the kernel headers and build script?

The /lib/modules/<some-kernel-version> directory contains the installed 
modules for a particular kernel version.  For our purposes, this directory 
is mostly interesting because it is the canonical place to look for a symbolic 
link named "build" that gives the headers which match the version you want 
to build a module against.  The link usually points to the root of the kernel 
directory tree that includes at least the headers.

For standard Ubuntu kernels, there are linux headers packages that provide 
the headers and create the "build" link.
    Run: sudo apt-get install linux-headers-$(uname -r)
You're ready to go!

For the custom grinch kernel (e.g. version 21.3.4), we'll need to download 
the full kernel source tarball.  The headers are a subset of this.
    Run: wget http://www.jarzebski.pl/files/jetsontk1/grinch-21.3.4/jetson-tk1-grinch-21.3.4-source.tar.bz2

Now, we're just going to manually point "build" to the root of the full 
kernel source.   The directory it points to should have subdirectories 
named "include", "drivers", "arch", and others.  If you expanded the source 
tarball in /usr/src:

Run: sudo ln -s /usr/src/linux-grinch-21.3.4 /lib/modules/3.10.40-grinch-21.3.4/build


II.  Installing the driver

Both the uvcstill and uvcvideo drivers desire ownership of USB
video devices.  How to prefer the uvcstill driver?

    * If uvcvideo is an unloadable kernel module, unload it.
      Run: sudo rmmod uvcvideo

      For more information about kernel modules and how they
      are loaded and unloaded...
      See:  https://wiki.archlinux.org/index.php/Kernel_modules

    * The opposite of a loadable module is of course a non-loadable 
      (statically linked) one.  (When building the Linux kernel, it is 
      possible to choose to package these drivers as part of the system.)
      The builder of the grinch kernel appears to have done this with the 
      uvcvideo module.  (This is rarely done on desktops but is more common 
      on embedded platforms where the hardware is fixed and the exact set 
      of needed drivers is supposedly predetermined.)
    
      If uvcvideo is built into the kernel, it can temporarily
      dissociated from a *connected* device by writing the device
      bus address to /sys/bus/usb/drivers/uvcvideo/unbind.
      Run: make unbind
      This is a convenient Makefile target to do exactly the above.

    * A more permanent solution is to permanently configure the uvcvideo
      driver to ignore devices with certain USB identifiers.  
      (TBD: more info).

If you've successfully compiled the uvcstill driver, there should be a
uvcstill.ko file in the source directory.  This module can be loaded in 
the normal manner (via insmod or modprobe).
    Run: sudo insmod uvcstill.ko


III.  Capturing an still image

Once the module has been loaded successfully, it will create a device
for every attached USB video-class device.  These will appear as
/dev/still or /dev/stillXXX (where XXX is a number).  By default,
these devices are only readable as root, but the permissions can be
changed.

The utility program 'snapshot' will read the image
bytes directly into a memory buffer.  Conveniently, it will also
convert the result to RGB and then write it to disk as a PNG image.
    Run: sudo ./snapshot output.png

There are many options.  The usage instruction will be printed by running
without any options.
    Run: ./snapshot

Note that both of the above commands need to be run as root, because
the /dev/still device is (by default) only readable by root. 


IV.  Troubleshooting

Information is logged into kernel log, typically at /var/log/kern.log.
Output specific to this driver will be prefixed with "uvcstill".

Q:  What drivers (e.g. uvcvideo or uvcstill) are loaded?
A:  Run: lsmod

Q:  I can't open the /dev/still device.
A.  Does your user have permissions?  By default, it is readable only by root.

Q:  What are the USB descriptors for a particular UVC device?
A:  Run: lsusb -v
