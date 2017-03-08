# The name of the compiler that we want to use
CXX=g++

# Compiler flags
CXXFLAGS=$(INCDIRS) -std=c++11

# Linker flags
LDFLAGS=$(LIBDIRS) $(LIBS)

# List of header files are included
HEADERS=COM10K1GPIO.h

all:    GPIOTestApp WaitForPinApp

%.o: %.c $(HEADERS)
	$(CXX) -c -o $@ $< $(CXXFLAGS)

# List of GPIOTestApp dependencies.
GPIOTESTAPP_DEPS=\
   GPIOTestApp.o \
   COM10K1GPIO.o \

GPIOTestApp: $(GPIOTESTAPP_DEPS)
	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS)

# List of WaitForPinApp dependencies.
WAITFORPINAPP_DEPS=\
   WaitForPinApp.o \
   COM10K1GPIO.o \

WaitForPinApp: $(WAITFORPINAPP_DEPS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

clean:
	rm -f *.o GPIOTestApp WaitForPinApp
