// A gaze point callback for marking gaze point to the screen in real time.

// TODO: Refactor into a class


#include <assert.h>
#include <stdio.h>
#include <cstring>
#include <chrono>
#include <thread>

#include <X11/Xlib.h>
#include <X11/X.h>
#include <X11/Xutil.h>

#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>

#include "/usr/include/cairo/cairo.h"
#include "/usr/include/cairo/cairo-xlib.h"


using namespace std;

#define GAZE_MARK_INTERVAL 7
#define GAZE_MARKER_WIDTH 5
#define GAZE_MARKER_HEIGHT 20
#define GAZE_MARKER_CDEPTH 32
#define GAZE_MARKER_OPAQUENESS 100
#define GAZE_MARKER_BORDER 0
#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160

static Display *d;
static Window root;
static XVisualInfo vinf;
static XSetWindowAttributes attrs;
static Window overlay;
static int default_screen;
static int mark_count;

void init_marker_disp() {
    d = XOpenDisplay(NULL);
    root = DefaultRootWindow(d);
    default_screen = XDefaultScreen(d);

    XMatchVisualInfo(d, DefaultScreen(d), GAZE_MARKER_CDEPTH, TrueColor, &vinf);

    attrs.override_redirect = true;
    attrs.colormap = XCreateColormap(d, root, vinf.visual, AllocNone);
    attrs.background_pixel = GAZE_MARKER_OPAQUENESS;
    attrs.border_pixel = 0;

    mark_count = 0;
}

void close_marker_display() {
        XCloseDisplay(d);
}

void gaze_marker_callback(tobii_gaze_point_t const *gaze_point, void *user_data) {
    // Only mark ever GAZE_MARK_INTERVAL callbacks
    mark_count++;
    if (mark_count % GAZE_MARK_INTERVAL != 0)
        return;

    mark_count = 0;

    if (gaze_point->validity == TOBII_VALIDITY_VALID) {
        // Convert gaze point to screen coords
        int x = gaze_point->position_xy[0] * DISP_WIDTH;
        int y = gaze_point->position_xy[1] * DISP_HEIGHT;

        // printf("Gaze points: %d, %d\n", x, y);  // debug

        overlay = XCreateWindow(
            d, root, x, y, 
            GAZE_MARKER_WIDTH, 
            GAZE_MARKER_HEIGHT,
            GAZE_MARKER_BORDER,
            vinf.depth,
            InputOutput, 
            vinf.visual,
            CWOverrideRedirect | CWColormap | CWBackPixel | CWBorderPixel, 
            &attrs
        );

        XMapWindow(d, overlay);

        cairo_surface_t* surf = cairo_xlib_surface_create(
            d, overlay, vinf.visual, GAZE_MARKER_WIDTH, GAZE_MARKER_HEIGHT);
        XFlush(d);


        cairo_surface_destroy(surf);

        XUnmapWindow(d, overlay);
    }
    else
    {
        printf("WARN: Received invalid gaze_point.\n");
    }
}