// A class for annotating gaze status from the eyetracker in real time.
// Gaze point is displayed on the screen when valid.

#include <stdio.h>
#include <cstring>

#include <X11/Xlib.h>
#include <X11/X.h>
#include <X11/Xutil.h>

#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>

#include <cairo/cairo.h>
#include <cairo/cairo-xlib.h>


using namespace std;

#define GAZE_MARK_INTERVAL 7
#define GAZE_MARKER_WIDTH 5
#define GAZE_MARKER_HEIGHT 20
#define GAZE_MARKER_CDEPTH 32
#define GAZE_MARKER_OPAQUENESS 100
#define GAZE_MARKER_BORDER 0
#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160


class GazeStatus {
    public:
        Display *disp;
        Window root_wind;
        XVisualInfo vinfo;
        XSetWindowAttributes attrs;
        Window overlay;
        int default_screen;
        int mark_count;
        // TODO: Ring buffer: vector<tobii_gaze_point_t*> gaze_points; 

        GazeStatus();
        ~GazeStatus();
        // void gaze_status_callback(tobii_gaze_point_t const*, void*);
};

// Default constructor
GazeStatus::GazeStatus() {
    disp = XOpenDisplay(NULL);
    root_wind = DefaultRootWindow(disp);
    default_screen = XDefaultScreen(disp);

    XMatchVisualInfo(
        disp, DefaultScreen(disp), GAZE_MARKER_CDEPTH, TrueColor, &vinfo);

    attrs.override_redirect = true;
    attrs.colormap = XCreateColormap(disp, root_wind, vinfo.visual, AllocNone);
    attrs.background_pixel = GAZE_MARKER_OPAQUENESS;
    attrs.border_pixel = 0;

    mark_count = 0;
}

// Destructor
GazeStatus::~GazeStatus() {
        XCloseDisplay(disp);
}

void gaze_status_callback(tobii_gaze_point_t const *gaze_point, void *user_data) {
    // Cast user_data ptr to a GazeStatus 
    GazeStatus *gaze_status = static_cast<GazeStatus*>(user_data);

    // Only mark every GAZE_MARK_INTERVAL callbacks
    gaze_status->mark_count++;
    if (gaze_status->mark_count % GAZE_MARK_INTERVAL != 0)
        return;

    gaze_status->mark_count = 0;

    if (gaze_point->validity == TOBII_VALIDITY_VALID) {
        // Convert gaze point to screen coords
        int x = gaze_point->position_xy[0] * DISP_WIDTH;
        int y = gaze_point->position_xy[1] * DISP_HEIGHT;

        printf("Gaze points: %d, %d\n", x, y);  // debug
        // printf("%d", gaze_status->mark_count);

        // Create the gaze marker as an overlay window
        gaze_status->overlay = XCreateWindow(
            gaze_status->disp,
            gaze_status->root_wind,
            x, y, 
            GAZE_MARKER_WIDTH, 
            GAZE_MARKER_HEIGHT,
            GAZE_MARKER_BORDER,
            gaze_status->vinfo.depth,
            InputOutput, 
            gaze_status->vinfo.visual,
            CWOverrideRedirect | CWColormap | CWBackPixel | CWBorderPixel, 
            &gaze_status->attrs
        );

        XMapWindow(gaze_status->disp, gaze_status->overlay);

        cairo_surface_t* surf = cairo_xlib_surface_create(
            gaze_status->disp, 
            gaze_status->overlay,
            gaze_status->vinfo.visual,
            GAZE_MARKER_WIDTH,
            GAZE_MARKER_HEIGHT);

        // Destroy the marker
        XFlush(gaze_status->disp);
        cairo_surface_destroy(surf);
        XUnmapWindow(gaze_status->disp, gaze_status->overlay);
    }
    else
    {
        printf("WARN: Received invalid gaze_point.\n");
    }
}
