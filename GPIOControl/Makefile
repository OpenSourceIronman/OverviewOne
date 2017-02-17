# The name of the compiler that we want to use
CXX=g++

# Compiler flags
CXXFLAGS=$(INCDIRS) -std=c++11

# Linker flags
LDFLAGS=$(LIBDIRS) $(LIBS)

# List of source files that should be compiled into the final executable program
SOURCES=GPIOTestApp.c COM10K1GPIO.c

# List of header files that should be included while compiling
HEADERS=COM10K1GPIO.h 

all:    GPIOTestApp

GPIOTestApp:    $(SOURCES) $(HEADERS)
	$(CXX) -o GPIOTestApp $(SOURCES) $(CXXFLAGS) $(LDFLAGS)  

clean:
	rm -f *.o GPIOTestApp
