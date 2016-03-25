#!/bin/bash
# file: I2CSetup.sh
# http://elinux.org/Interfacing_with_I2C_Devices
# https://devtalk.nvidia.com/default/topic/770603/embedded-systems/i2c-port-name-and-i2cbus-number/post/4397340/#4397340
# http://tldp.org/HOWTO/Bash-Prog-Intro-HOWTO.html
# https://xgoat.com/wp/2008/01/29/i2c-device-udev-rule/

#System I2C Device Address used in Overview One so far
#0x2B, 0x2C, 0x0A, 0x1A, 0x2A, 0x3A, 0x4A, 0x5A, Camera #1 TBD, Camera #2 TBD

$ sudo apt-get update
$ sudo apt-get install -y i2c-tools
$ apt-cache policy i2c-tools i2c-tools:

$ gcc CROSS-COMPILE=arm-none-linux-gnueabi ARCH=arm i2c_interface.c -o i2c_binary

#Normal Probing - http://manpages.ubuntu.com/manpages/hardy/man8/i2cdetect.8.html
$ sudo i2cdetect -y 0

#I2cdump PORT SLAVE_ADDR - http://manpages.ubuntu.com/manpages/trusty/en/man8/i2cdump.8.html
$ sudo i2cdump -f -y 4 0x40

#i2cset PORT SLAVE_ADDR REG VALUE - http://manpages.ubuntu.com/manpages/trusty/en/man8/i2cset.8.html
$ sudo i2cset -f -y 4 0x40 0x58 0x05

#i2cget PORT SLAVE_ADDR REG - http://manpages.ubuntu.com/manpages/trusty/en/man8/i2cget.8.html
$ sudo i2cget -f -y 4 0x40 0x58


#udev rule that would make any userspace i2c devices be owned by the i2c group:
KERNEL=="i2c-[0-9]*", GROUP="i2c"
#You can stick that in a file in /etc/udev/rules.d if you’re using Fedora
