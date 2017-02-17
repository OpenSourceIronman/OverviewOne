obj-m += uvcstill.o

all: build-module build-trigger snapshot yuyv2png yuyv2webp yuyv2jpg

# Build the "trigger" program.
build-trigger:
	g++ -o trigger trigger.c

# Build the "shapshot" program.
snapshot: snapshot.cpp
	g++ -o snapshot snapshot.cpp -lpng -lturbojpeg

# Build the "yuyv2png" program.
yuyv2png: yuyv2png.cpp
	g++ -o yuyv2png yuyv2png.cpp -std=c++0x -lpng

# Build the "yuyv2webp" program.
yuyv2webp: yuyv2webp.cpp
	g++ -o yuyv2webp yuyv2webp.cpp -std=c++0x -lwebp

# Build the "yuyv2webp" program.
yuyv2jpg: yuyv2jpg.cpp
	g++ -o yuyv2jpg yuyv2jpg.cpp -std=c++0x -lturbojpeg

# Build the kernel module.
build-module:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

# Sign the kernel module with (a random key).
sign-module:
	/usr/src/linux-headers-$(shell uname -r)/scripts/sign-file \
		sha512 signing_key.priv signing_key.x509 uvcstill.ko

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

# Install the uvcstill module, ensuring that the uvcvideo module
# has been unloaded.
# Alternatively, echo the bus ID to /sys/bus/usb/drivers/uvcvideo/unbind
install:
	-sudo rmmod uvcvideo
	sudo insmod uvcstill.ko

unbind:
	sudo sh -c 'find /sys/bus/usb/drivers/uvcvideo/ -name "*:1.0" -exec basename {} > /sys/bus/usb/drivers/uvcvideo/unbind \;'

# This target reads bytes from the device into "test.ppm".
# A header is added.
ppm:
	echo "P5 1280 720 255" > test.ppm
	sudo cat /dev/still >> test.ppm
