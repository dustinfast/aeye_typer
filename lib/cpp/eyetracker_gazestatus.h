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

#include <boost/circular_buffer.hpp>

using namespace std;


#define GAZE_MARKER_WIDTH 5
#define GAZE_MARKER_HEIGHT 20
#define GAZE_MARKER_CDEPTH 32
#define GAZE_MARKER_OPAQUENESS 100
#define GAZE_MARKER_BORDER 0

typedef struct gaze_data {
		int x;
        int y;
        int64_t timestamp_us;
	} gaze_data_t;

class GazeStatus {
    boost::circular_buffer<gaze_data_t> gaze_buff;
    int default_screen;

    public:
        Display *disp;
        Window root_wind;
        XVisualInfo vinfo;
        XSetWindowAttributes attrs;
        Window overlay;
        int mark_count;
        int mark_freq;
        int disp_width;
        int disp_height;
        bool gaze_is_valid;

        GazeStatus(int, int, int, int);
        ~GazeStatus();
        bool is_gaze_valid();
        void enque_gaze_data(int x, int y, int64_t timestamp);
        void print_data();
};

// Default constructor
GazeStatus::GazeStatus(
    int display_width, int display_height, int update_freq, int buff_sz) {
    disp_width = display_width;
    disp_height = display_height;
    mark_freq = update_freq;
    gaze_buff = boost::circular_buffer<gaze_data_t>(buff_sz); 

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
    gaze_is_valid = False;
}

// Destructor
GazeStatus::~GazeStatus() {
        XCloseDisplay(disp);
}

// Returns the current gaze validity state
bool GazeStatus::is_gaze_valid() {
    return gaze_is_valid;
}

// Enques gaze data into the circular buffer
void GazeStatus::enque_gaze_data(int x, int y, int64_t timestamp) {
    gaze_data gd;
    gd.x = x;
    gd.y = y;
    gd.timestamp_us = timestamp;

    gaze_buff.push_back(gd);
}

// Prints the contents of the circular buffer. For debug convenience.
void GazeStatus::print_data() {
    gaze_data gd;
    boost::circular_buffer<gaze_data_t>::iterator i; 

    for (i = gaze_buff.begin(); i < gaze_buff.end(); i++)  {
        gd = *i;
        printf("%li\n", gd.timestamp_us); 
    }
}


// Gaze status callback, for use with tobii_gaze_point_subscribe(). Determines
// the eyetrackers predict on-screen gaze coordinates (x, y) and enques gaze
// data into GazeStatus' circular buffer.
// ASSUMES: user_data is a ptr to an object of type GazeStatus.
void cb_gaze_point(tobii_gaze_point_t const *gaze_point, void *user_data) {
    // Cast user_data ptr to a GazeStatus 
    GazeStatus *gaze_status = static_cast<GazeStatus*>(user_data);

    // Only process every mark_freq callbacks
    gaze_status->mark_count++;
    if (gaze_status->mark_count % gaze_status->mark_freq != 0)
        return;

    gaze_status->mark_count = 0;

    if (gaze_point->validity == TOBII_VALIDITY_VALID) {
        gaze_status->gaze_is_valid = True;

        // Convert gaze point to screen coords
        int x_coord = gaze_point->position_xy[0] * gaze_status->disp_width;
        int y_coord = gaze_point->position_xy[1] * gaze_status->disp_height;

        // Enque the gaze data in the circle buffer
        gaze_status->enque_gaze_data(x_coord, y_coord, gaze_point->timestamp_us);

        // printf("Gaze points: %d, %d\n", x, y);  // debug
        printf("Gaze time: %li\n", gaze_point->timestamp_us);  // debug

        // Create the gaze marker as an overlay window
        gaze_status->overlay = XCreateWindow(
            gaze_status->disp,
            gaze_status->root_wind,
            x_coord,
            y_coord, 
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
        gaze_status->gaze_is_valid = False;
        printf("WARN: Received invalid gaze_point.\n"); // debug

    }
}
