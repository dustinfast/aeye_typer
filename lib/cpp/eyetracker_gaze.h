// A class for annotating gaze status from the eyetracker in real time.
// Gaze point is displayed on the screen when valid.

#include <chrono>
#include <stdio.h>

#include <boost/thread.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/circular_buffer.hpp>
#include <cairo/cairo-xlib.h>
#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "eyetracker.h"

using namespace std;
using namespace std::chrono;
using time_stamp = time_point<system_clock, microseconds>;


/////////////////////////////////////////////////////////////////////////////
// Defs

#define GAZE_MARKER_WIDTH 5
#define GAZE_MARKER_HEIGHT 20
#define GAZE_MARKER_CDEPTH 32
#define GAZE_MARKER_OPAQUENESS 100
#define GAZE_MARKER_BORDER 0

typedef struct gaze_data {
		int x;
        int y;
        time_stamp unixtime_us;
	} gaze_data_t;

void do_gaze_point_subscribe(tobii_device_t*, void*);
void cb_gaze_point(tobii_gaze_point_t const* , void*);


/////////////////////////////////////////////////////////////////////////////
// Class

class EyeTrackerGaze : EyeTracker {
    private:
        boost::thread *m_async;
        boost::mutex *m_async_mutex;

    public:
        Display *m_disp;
        Window m_root_wind;
        XVisualInfo m_vinfo;
        XSetWindowAttributes m_attrs;
        Window m_overlay;
        int m_mark_count;
        int m_mark_freq;
        int m_disp_width;
        int m_disp_height;
        bool m_gaze_is_valid;

        EyeTrackerGaze(int, int, int, int);
        ~EyeTrackerGaze();
        void start();
        void stop();
        bool is_gaze_valid();
        void enque_gaze_data(int, int, time_stamp);
        void print_gaze_data();
    
    protected:
        boost::circular_buffer<gaze_data_t> m_gaze_buff;
};

// Default constructor
EyeTrackerGaze::EyeTrackerGaze(
    int disp_width, int disp_height, int update_freq, int buff_sz) {
    m_disp_width = disp_width;
    m_disp_height = disp_height;
    m_mark_freq = update_freq;
    m_gaze_buff = boost::circular_buffer<gaze_data_t>(buff_sz); 

    m_disp = XOpenDisplay(NULL);
    m_root_wind = DefaultRootWindow(m_disp);

    XMatchVisualInfo(
        m_disp, DefaultScreen(m_disp), GAZE_MARKER_CDEPTH, TrueColor, &m_vinfo);

    m_attrs.override_redirect = true;
    m_attrs.colormap = XCreateColormap(
        m_disp, m_root_wind, m_vinfo.visual, AllocNone);
    m_attrs.background_pixel = GAZE_MARKER_OPAQUENESS;
    m_attrs.border_pixel = 0;

    m_mark_count = 0;
    m_gaze_is_valid = False;
}

// Destructor
EyeTrackerGaze::~EyeTrackerGaze() {
    XCloseDisplay(m_disp);
}

// Starts watching the gaze data stream asynchronously until interuppted by
// a stop() call.
void EyeTrackerGaze::start() {
    // TODO: Subscribe to user position, etc.
    m_async_mutex = new boost::mutex;
    m_async = new boost::thread(do_gaze_point_subscribe, m_device, this);
}

void EyeTrackerGaze::stop() {
    // TODO: Try/catch
    m_async->interrupt();
    m_async->join();
    delete m_async;
    delete m_async_mutex;
}

// Returns the current gaze validity state
bool EyeTrackerGaze::is_gaze_valid() {
    return m_gaze_is_valid;
}

// Enques gaze data into the circular buffer
void EyeTrackerGaze::enque_gaze_data(int x, int y, time_stamp unixtime_us) {
    // TODO: mark on freq but enque as often as possible
    gaze_data gd;
    gd.x = x;
    gd.y = y;
    gd.unixtime_us = unixtime_us;

    m_async_mutex->lock();
    m_gaze_buff.push_back(gd);
    m_async_mutex->unlock();
}

// Prints the contents of the circular buffer. For debug convenience.
void EyeTrackerGaze::print_gaze_data() {
    boost::circular_buffer<gaze_data_t>::iterator i; 

    for (i = m_gaze_buff.begin(); i < m_gaze_buff.end(); i++)  {
        printf("(%d, %d)\n", ((gaze_data)*i).x, ((gaze_data)*i).y); 
    }
}


/////////////////////////////////////////////////////////////////////////////
// Gaze subscriber and callback functions

// Starts the gaze data stream
void do_gaze_point_subscribe(tobii_device_t *device, void *gaze) {

    // Subscribe to gaze point
    assert(tobii_gaze_point_subscribe(device, cb_gaze_point, gaze
    ) == TOBII_ERROR_NO_ERROR);

    while (True) {
    try {
        assert(tobii_wait_for_callbacks(1, &device) == TOBII_ERROR_NO_ERROR);
        assert(tobii_device_process_callbacks(device) == TOBII_ERROR_NO_ERROR);
        boost::this_thread::sleep_for(boost::chrono::milliseconds{1});
        }
        catch (boost::thread_interrupted&) {
            break;
        }
    }

    assert(tobii_gaze_point_unsubscribe(device) == TOBII_ERROR_NO_ERROR);
}


// Gaze point callback for use with tobii_gaze_point_subscribe(). Gets the
// eyetrackers predicted on-screen gaze coordinates (x, y) and enques gaze
// data into Gazes' circular buffer.
// ASSUMES: user_data is a ptr to an object of type EyeTrackerGaze.
void cb_gaze_point(tobii_gaze_point_t const *gaze_point, void *user_data) {
    EyeTrackerGaze *gaze = static_cast<EyeTrackerGaze*>(user_data);

    // Only process every m_mark_freq callbacks
    gaze->m_mark_count++;
    if (gaze->m_mark_count % gaze->m_mark_freq != 0)
        return;

    gaze->m_mark_count = 0;

    if (gaze_point->validity == TOBII_VALIDITY_VALID) {
        gaze->m_gaze_is_valid = True;
        
        // Get unix timestamp in microseconds
        time_stamp unixtime_us = time_point_cast<microseconds>(
            system_clock::now()
        );
        // printf("epoch time: %li\n", unixtime_us);  // debug

        // Convert gaze point to screen coords
        int x_coord = gaze_point->position_xy[0] * gaze->m_disp_width;
        int y_coord = gaze_point->position_xy[1] * gaze->m_disp_height;
        // printf("Gaze points: %d, %d\n", x, y);  // debug

        // Enque the gaze data in the circle buffer
        gaze->enque_gaze_data(x_coord, y_coord, unixtime_us);

        // Create the gaze marker as an overlay window
        gaze->m_overlay = XCreateWindow(
            gaze->m_disp,
            gaze->m_root_wind,
            x_coord,
            y_coord, 
            GAZE_MARKER_WIDTH, 
            GAZE_MARKER_HEIGHT,
            GAZE_MARKER_BORDER,
            gaze->m_vinfo.depth,
            InputOutput, 
            gaze->m_vinfo.visual,
            CWOverrideRedirect | CWColormap | CWBackPixel | CWBorderPixel, 
            &gaze->m_attrs
        );

        XMapWindow(gaze->m_disp, gaze->m_overlay);

        cairo_surface_t* surf = cairo_xlib_surface_create(
            gaze->m_disp, 
            gaze->m_overlay,
            gaze->m_vinfo.visual,
            GAZE_MARKER_WIDTH,
            GAZE_MARKER_HEIGHT);

        // Destroy the marker
        XFlush(gaze->m_disp);
        cairo_surface_destroy(surf);
        XUnmapWindow(gaze->m_disp, gaze->m_overlay);
    }
    else
    {
        gaze->m_gaze_is_valid = False;
        printf("WARN: Received invalid gaze_point.\n"); // debug

    }
}
