// YUYV -> WEBP Conversion Program
//
// Copyright SpaceVR, 2016.  All rights reserved.
//
// Author: Aaron Hurst (aaronpaulhurst@gmail.com)
// Date:   June 28, 2016

#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <iostream>
#include <webp/decode.h>
#include <webp/encode.h>
#include <webp/types.h>
#include <vector>

using namespace std;

typedef unsigned char u8;

// Frame dimensions
int g_width = 4192, g_height = 3104;

// --------------------------------------------------------
// Image Manipulation
// --------------------------------------------------------

// Convert 'buf' to WEBP.  Updates the pointer 'out' to the
//    output buffer.
// Returns the size of the new output buffer or 0 on error.
// Caller must free the output buffer.
size_t rgb_to_webp(u8 * buf, u8 ** out /*output, must free*/) {
    return WebPEncodeLosslessRGB(buf, g_width, g_height, g_width*3, out);
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

    // Print usage
    if (argc < 2) {
        cout << "Usage: yuyv2webp [options...] <input files ...>" << endl;
        cout << endl;
        cout << "   --size <width> <height> : frame size (default: 4192 x 3104)" << endl;
        return 1; // failure
    }

    // Parse options
    vector<string> infilenames;

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
        outfilename += ".webp";

        FILE * outfile = fopen(outfilename.c_str(), "wb");
        if (outfile == NULL) {
           cout << "    - [ERROR] can't open output file " << outfilename << endl;
           continue;
        }

        cout << "    - writing WEBP output " << outfilename << "..." << endl;

        // Convert YUYV to RGB
        u8 * rgb_buf = new u8[g_width*g_height*3];
        yuyv_to_rgb(yuyv_buf, rgb_buf);

        // Convert RGB to WEBP
        u8 * webp_buf = NULL;
        int webp_size = rgb_to_webp(rgb_buf, &webp_buf);
        if (webp_size == 0) {
            cout << "    - [ERROR] failed to convert" << endl;
            continue;
        }

        fwrite (webp_buf, sizeof(char), webp_size, outfile);
        fclose(outfile);

        free(webp_buf);
        delete [] rgb_buf;
        delete [] yuyv_buf;
    }

    cout << "Total time = "
         << (int)((get_msec()-start_time)/1000.0)
         << " s" << endl;
}
