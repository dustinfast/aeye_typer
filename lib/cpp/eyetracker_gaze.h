/////////////////////////////////////////////////////////////////////////////
// A class for annotating gaze status from the eyetracker in real time.
// When the gaze point is valid (i.e. a user is present) a gaze_data obj
// is pushed to a circular buffer and the predicted gaze point is annotated
// on the screen.
// An extern "C" wrapper is also defined for select functions.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <fstream>

#include <boost/thread.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/circular_buffer.hpp>
#include <cairo/cairo-xlib.h>

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "eyetracker.h"

using namespace std;


/////////////////////////////////////////////////////////////////////////////
// Defs

#define GAZE_MARKER_WIDTH 5
#define GAZE_MARKER_HEIGHT 20
#define GAZE_MARKER_CDEPTH 32
#define GAZE_MARKER_OPAQUENESS 100
#define GAZE_MARKER_BORDER 0
#define GAZE_MIN_SAMPLE_FOR_RATE_CALC 200

typedef struct gaze_data {
		int x;
        int y;
        int64_t unixtime_us;
	} gaze_data_t;

void do_gaze_point_subscribe(tobii_device_t*, void*);
void cb_gaze_point(tobii_gaze_point_t const* , void*);


/////////////////////////////////////////////////////////////////////////////
// Class

class EyeTrackerGaze : public EyeTracker {
    public:
        int m_mark_count;
        int m_mark_freq;
        int m_disp_width;
        int m_disp_height;
        bool m_gaze_is_valid;
        Display *m_disp;
        Window m_root_wind;
        XVisualInfo m_vinfo;
        XSetWindowAttributes m_attrs;
        Window m_overlay;

        void start();
        void stop();
        int gaze_to_csv(const char*, int);
        bool is_gaze_valid();
        void enque_gaze_data(int, int, int64_t);
        void print_gaze_data();
        int gaze_data_sz();
        int sample_rate();
    
        EyeTrackerGaze(int, int, int, int);
        ~EyeTrackerGaze();

    protected:
        int m_buff_sz;
        boost::circular_buffer<gaze_data_t> *m_gaze_buff;

    private:
        boost::thread *m_async_streamer;
        boost::thread *m_async_writer;
        boost::mutex *m_async_mutex;
};

// Default constructor
EyeTrackerGaze::EyeTrackerGaze(
    int disp_width, int disp_height, int mark_freq, int buff_sz) {
        // Init from args
        m_disp_width = disp_width;
        m_disp_height = disp_height;
        m_mark_freq = mark_freq;
        m_buff_sz = buff_sz;

        // Init X11 display
        m_disp = XOpenDisplay(NULL);
        m_root_wind = DefaultRootWindow(m_disp);

        XMatchVisualInfo(
            m_disp, DefaultScreen(m_disp), GAZE_MARKER_CDEPTH, TrueColor, &m_vinfo);

        m_attrs.override_redirect = true;
        m_attrs.colormap = XCreateColormap(
            m_disp, m_root_wind, m_vinfo.visual, AllocNone);
        m_attrs.background_pixel = GAZE_MARKER_OPAQUENESS;
        m_attrs.border_pixel = 0;

        // Since we care about device timestamps, start time synchronization
        sync_device_time();

        // Init circular gaze point buffer and mutex
        m_gaze_buff = new boost::circular_buffer<gaze_data_t>(buff_sz); 
        m_async_mutex = new boost::mutex;

        // Set default states
        m_gaze_is_valid = False;
        m_mark_count = 0;

        m_async_writer = NULL;
        m_async_streamer = NULL;
}

// Destructor
EyeTrackerGaze::~EyeTrackerGaze() {
    stop();
    m_async_mutex->lock();
    delete m_gaze_buff;
    m_async_mutex->unlock();
    delete m_async_mutex;
    int64_t t_start = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();
    XCloseDisplay(m_disp);
    int64_t t_end = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();
    printf("Destructor took %li.\n\n", (t_end - t_start));
}

// Starts the async gaze threads
void EyeTrackerGaze::start() {
    m_async_streamer = new boost::thread(
        do_gaze_point_subscribe, m_device, this
    );
}

// Stops the async gaze threads
void EyeTrackerGaze::stop() {
    // Stop the gaze data streamer with an interrupt
    if (m_async_streamer) {
        m_async_streamer->interrupt();
        m_async_streamer->join();
        delete m_async_streamer;
        m_async_streamer = NULL;
    }

    // Wait for the writer thread to finish its current write
    if (m_async_writer) {
        m_async_writer->join();
        delete m_async_writer;
        m_async_writer = NULL;
    }
}

// Writes the gaze data to the given csv file path, creating it if exists 
// else appending to it. If n is given, writes only the most recent n samples.
// Returns an int representing the number of samples written.
int EyeTrackerGaze::gaze_to_csv(const char *file_path, int n=0) {
    int sample_count = m_gaze_buff->size();

    if (sample_count <= 0)
        return 0;
    
    if (n == 0)
        n = sample_count;

    // Ensure any previous async write job has finished and free its mem
    if (m_async_writer) {
        m_async_writer->join();
        delete m_async_writer;
        m_async_writer = NULL;
    }

    // Copy circ buff contents then clear it
    m_async_mutex->lock();
    boost::circular_buffer<gaze_data_t> *gaze_buff = m_gaze_buff;
    m_gaze_buff = new boost::circular_buffer<gaze_data_t>(m_buff_sz); 
    m_async_mutex->unlock();

    // Write the gaze data to file asynchronously
    m_async_writer = new boost::thread(
        [file_path, gaze_buff, n]() {
            ofstream f, f2;
            f.open(file_path, fstream::in | fstream::out | fstream::app);

            // Write (at most) the n latest samples to csv in ascending order
            int sz = gaze_buff->size();
            int n_capped = min(sz, n);

            for (int j = sz - n_capped; j < sz; j++)  {
                gaze_data g = gaze_buff->at(j); 
                f << g.x << ", " << g.y << ", " << g.unixtime_us << "\n";
        }

            f.close();
            delete gaze_buff;
        }
    );

    return sample_count;
}

// Returns the current gaze validity state
bool EyeTrackerGaze::is_gaze_valid() {
    return m_gaze_is_valid;
}

// Enques gaze data into the circular buffer
void EyeTrackerGaze::enque_gaze_data(int x, int y, int64_t unixtime_us) {
    shared_ptr<gaze_data> gd(new gaze_data());
    gd->x = x;
    gd->y = y;
    gd->unixtime_us = unixtime_us;

    m_async_mutex->lock();
    m_gaze_buff->push_back(*gd);
    m_async_mutex->unlock();
}

// Prints the coord contents of the circular buffer. For debug convenience.
void EyeTrackerGaze::print_gaze_data() {
    boost::circular_buffer<gaze_data_t>::iterator i; 

    m_async_mutex->lock();
    for (i = m_gaze_buff->begin(); i < m_gaze_buff->end(); i++)  {
        printf("(%d, %d)\n", ((gaze_data)*i).x, ((gaze_data)*i).y); 
    }
    m_async_mutex->unlock();
}

// Returns the current number of gaze points in the gaze data buffer
int EyeTrackerGaze::gaze_data_sz() {
    return m_gaze_buff->size();
}

// Returns the sample rate in hz, calculated from the contents of the buffer.
// If the buffer is not full enough to calculate, returns -1.
int EyeTrackerGaze::sample_rate() {
    int sample_count = gaze_data_sz();

    if (sample_count < GAZE_MIN_SAMPLE_FOR_RATE_CALC) {
        printf("WARN: Eyetracker hz queried but sample count insufficient.");
        return -1;
    }

    // Earliest and latest sample times, in microseconds
    long unsigned int t1 = m_gaze_buff->at(0).unixtime_us;
    long unsigned int t2 = m_gaze_buff->at(sample_count-1).unixtime_us;

    // Sample rate, in hz
    double t_diff = (t2 - t1) * .000001;
    double sample_rate = sample_count / t_diff;

    return sample_rate;
}


/////////////////////////////////////////////////////////////////////////////
// Extern wrapper exposing EyeTrackerGaze(), start(), stop(), & gaze_to_csv()
extern "C" {
    EyeTrackerGaze* eyetracker_gaze_new(
        int disp_width, int disp_height, int mark_freq, int buff_sz) {
            return new EyeTrackerGaze(
                disp_width, disp_height, mark_freq, buff_sz);
    }

    void eyetracker_gaze_destructor(EyeTrackerGaze* gaze) {
        gaze->~EyeTrackerGaze();
    }

    int eyetracker_gaze_to_csv(EyeTrackerGaze* gaze, const char *file_path, int n) {
        return gaze->gaze_to_csv(file_path, n);
    }

    void eyetracker_gaze_start(EyeTrackerGaze* gaze) {
        gaze->start();
    }

    void eyetracker_gaze_stop(EyeTrackerGaze* gaze) {
        gaze->stop();
    }

    int eyetracker_gaze_data_sz(EyeTrackerGaze* gaze) {
        return gaze->gaze_data_sz();
    }
}


/////////////////////////////////////////////////////////////////////////////
// Gaze subscriber and callback functions

// Starts the gaze point data stream
void do_gaze_point_subscribe(tobii_device_t *device, void *gaze) {

    // Subscribe to gaze point
    assert(tobii_gaze_point_subscribe(device, cb_gaze_point, gaze
    ) == NO_ERROR);

    try {
        while (True) {
            assert(tobii_wait_for_callbacks(1, &device) == NO_ERROR);
            assert(tobii_device_process_callbacks(device) == NO_ERROR);
            boost::this_thread::sleep_for(boost::chrono::microseconds{1});
        }
    } catch (boost::thread_interrupted&) {}

    assert(tobii_gaze_point_unsubscribe(device) == NO_ERROR);
}


// Gaze point callback for use with tobii_gaze_point_subscribe(). Gets the
// eyetrackers predicted on-screen gaze coordinates (x, y) and enques gaze
// data into EyeTrackerGazes' circular buffer. Also creates a shaded window
// overlay denoting the gaze point on the screen.
// ASSUMES: user_data is a ptr to an object of type EyeTrackerGaze.
void cb_gaze_point(tobii_gaze_point_t const *gaze_point, void *user_data) {
    EyeTrackerGaze *gaze = static_cast<EyeTrackerGaze*>(user_data);

    // If gaze is detected, do the enque and screen annotation
    if (gaze_point->validity == TOBII_VALIDITY_VALID) {
        gaze->m_gaze_is_valid = True;

        // Convert gaze point to screen coords
        int x_coord = gaze_point->position_xy[0] * gaze->m_disp_width;
        int y_coord = gaze_point->position_xy[1] * gaze->m_disp_height;

        // Convert timestamp from device time to system clock time
        int64_t timestamp = gaze->devicetime_to_systime(
            gaze_point->timestamp_us);
        
        // printf("Gaze points: %d, %d\n", x_coord, y_coord);  // debug
        // printf("timestamp    : %li\n", gaze_point->timestamp_us); // debug
        // printf("timestamp adj: %li\n", timestamp); // debug

        // Enque converted gaze data in the circular buffer
        gaze->enque_gaze_data(x_coord, y_coord, timestamp);
        
        // Annotate (x, y) on the screen every m_mark_freq callbacks
        gaze->m_mark_count++;
        if (gaze->m_mark_count % gaze->m_mark_freq != 0)
            return;

        gaze->m_mark_count = 0;

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

        // Destroy the marker immediately, so it appears for a very short time
        XFlush(gaze->m_disp);
        cairo_surface_destroy(surf);
        XUnmapWindow(gaze->m_disp, gaze->m_overlay);
    }

    // Else if no gaze detected by the device, do nothing
    else {
        gaze->m_gaze_is_valid = False;
        // printf("WARN: Received invalid gaze_point.\n"); // debug

    }
}
