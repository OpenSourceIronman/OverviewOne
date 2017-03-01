/**
 * @file yuyv2jpg.cpp
 * @author Aaron Hurst SpaceVR(TM)
 * @date 09/16/16
 * @link https://en.wikipedia.org/wiki/YUV
 * @version 1.0
 *
 * @brief Convert raw 26 MB YUYV image to 1 MB JPG image
 * 
 */

#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <iostream>
#include <vector>
#include <turbojpeg.h>

using namespace std;

typedef unsigned char u8;

// Frame dimensions
int g_width = 4192, g_height = 3104;

// Image quality
int g_jpg_quality = 90;

// --------------------------------------------------------
// Image Manipulation
// --------------------------------------------------------

/**
 * @brief Convert RGB image data into a .JPEG image format
 *
 * @param buf Memory location of the inital RGB image file
 * @param out Memory location of the compress JPEG output
 * 
 * @return Size of JPEG image
 */
size_t rgb_to_jpg(u8 * buf, u8 ** out /*output, must free*/) {
   tjhandle jpegCompressor = tjInitCompress();

   long unsigned int out_size;
   tjCompress2(jpegCompressor, buf, g_width, 0, g_height, TJPF_RGB,
              out, &out_size, TJSAMP_422, g_jpg_quality,
              TJFLAG_FASTDCT);

   tjDestroy(jpegCompressor);
   return out_size;
}


/**
 * @brief Convert YUYV420 images bytes into a RGB image bytes
 *
 * @link https://en.wikipedia.org/wiki/YUV
 *
 * @section DESCRIPTION
 *
 * YUV is a color space typically used as part of a color image 
 * pipeline. It encodes a color image or video taking human perception 
 * into account, allowing reduced bandwidth for chrominance components, 
 * thereby typically enabling transmission errors or compression artifacts 
 * to be more efficiently masked by the human perception than using a 
 * "direct" RGB-representation.
 * 
 * @param y Luma (or brigthness) of the image
 * @param u First chrominance (or color) component 
 * @param v Second chrominance (or color) component 
 * @param r Red chrominance (or color) component value from 0 to 255
 * @param g Green chrominance (or color) component value from 0 to 255
 * @param b Blue chrominance (or color) component value from 0 to 255
 * 
 * @return NOTHING
 */
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

/**
 * @brief Cycle through and convert every pixel in a  YUYV420 image
 *
 * @link https://en.wikipedia.org/wiki/YUV
 * 
 * @param yuyv_buf Memory location of the inital YUYV420 image file
 * @param yuyv_buf Memory location of the outout RGB image file
 * 
 * @return NOTHING
 */
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

/**
 * @brief Get current Linux system time to milisecond resolution. 
 * 
 * @param NONE
 *
 * @return milisecond system time 
 */
long get_msec() {
    struct timeval tp;
    gettimeofday(&tp, NULL);
    return tp.tv_sec * 1000 + tp.tv_usec / 1000;
}


// Program entry point
int main(int argc, char **argv)
{
    long start_time = get_msec();

    // Print usage
    if (argc < 2) {
        cout << "Usage: yuyv2jpg [options...] <input files ...>" << endl;
        cout << endl;
        cout << "   --size <width> <height> : frame size (default: 4192 x 3104)" << endl;
        cout << "   --jpg-quality [1..100]  : image quality (default: 70)" << endl;
        return 1; // failure
    }

    // Parse options
    vector<string> infilenames;

    //TO-DO??? Comment this better
    for(int i=1; i<argc; ++i) {
        const char * opt = argv[i];

        if (!strcmp(opt, "--size")) {
            if (i+2 < argc && argv[i+1][0] != '-' && argv[i+2][0] != '-') {
                g_width = atoi(argv[i+1]);
                g_height = atoi(argv[i+2]);
                i += 2;
            } else {
                cout << "Option --size requires two arguments" << endl;
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
        else {
            infilenames.push_back(argv[i]);
        }
    }
    if (infilenames.empty()) {
        cout << "Input filename required" << endl;
        return 1;
    }

    // Process each file
    cout << "Processing " << infilenames.size() << " files" << endl;
    for(const auto & infilename : infilenames) {
        FILE * dev = fopen(infilename.c_str(), "rb");
        if (dev == NULL) {
            cout << "    - [ERROR] can't open input file " << infilename << endl;
            continue;
        }

        // Initialize buffer
        // (Add extra bytes to test for a too-large image)
        u8 * yuyv_buf = new u8[g_width*g_height*2 + 10];
        memset(yuyv_buf, 0, g_width*g_height*2);

        // Read image
        int rsl = fread(yuyv_buf, 1, g_width*g_height*2 + 10, dev);

        // Did we get a complete image?
        if (rsl != g_width*g_height*2) {
            cout << "    - [WARNING] skipping image " << infilename
                 << ", which does not match the expected size : "
                 << g_width << " x " << g_height << " ("
                 << (g_width*g_height*2/1024) << "KB )" << endl;
            continue;
        }

        fclose(dev);

        string outfilename = infilename;
        outfilename += ".jpg";

        FILE * outfile = fopen(outfilename.c_str(), "wb");
        if (outfile == NULL) {
           cout << "    - [ERROR] can't open output file " << outfilename << endl;
           continue;
        }

        cout << "    - writing JPEG output " << outfilename << "..." << endl;

        // Convert YUYV to RGB
        u8 * rgb_buf = new u8[g_width*g_height*3];
        yuyv_to_rgb(yuyv_buf, rgb_buf);

        // Convert RGB to JPG
        u8 * jpg_buf = NULL;
        int jpg_size = rgb_to_jpg(rgb_buf, &jpg_buf);
        if (jpg_size == 0) {
            cout << "    - [ERROR] failed to convert" << endl;
            continue;
        }

        fwrite (jpg_buf, sizeof(char), jpg_size, outfile);
        fclose(outfile);

        tjFree(jpg_buf);
        delete [] rgb_buf;
        delete [] yuyv_buf;
    }

    cout << "Total time = "
         << (int)((get_msec()-start_time)/1000.0)
         << " s" << endl;
}
