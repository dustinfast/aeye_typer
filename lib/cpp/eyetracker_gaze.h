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

typedef struct custom_gaze_data {
        int64_t unixtime_us;

        float left_pupildiameter_mm;
        float right_pupildiameter_mm;

        float left_eyeposition_normed_x;
		float left_eyeposition_normed_y;
		float left_eyeposition_normed_z;
		float right_eyeposition_normed_x;
		float right_eyeposition_normed_y;
		float right_eyeposition_normed_z;

        float left_eyecenter_mm_x;
		float left_eyecenter_mm_y;
		float left_eyecenter_mm_z;
		float right_eyecenter_mm_x;
		float right_eyecenter_mm_y;
		float right_eyecenter_mm_z;

        float left_gazeorigin_mm_x;
		float left_gazeorigin_mm_y;
		float left_gazeorigin_mm_z;
		float right_gazeorigin_mm_x;
		float right_gazeorigin_mm_y;
		float right_gazeorigin_mm_z;

        float left_gazepoint_mm_x;
		float left_gazepoint_mm_y;
		float left_gazepoint_mm_z;
		float right_gazepoint_mm_x;
		float right_gazepoint_mm_y;
		float right_gazepoint_mm_z;

        float left_gazepoint_normed_x;
		float left_gazepoint_normed_y;
		float right_gazepoint_normed_x;
		float right_gazepoint_normed_y;

        int combined_gazepoint_x;
        int combined_gazepoint_y;

	    } custom_gaze_data_t;

typedef boost::circular_buffer<shared_ptr<custom_gaze_data_t>> circ_buff;

void do_gaze_data_subscribe(tobii_device_t*, void*);
static void cb_gaze_data(tobii_gaze_data_t const*, void*);


/////////////////////////////////////////////////////////////////////////////
// Class

class EyeTrackerGaze : public EyeTracker {
    public:
        int m_mark_count;
        int m_mark_freq;
        int m_disp_width;
        int m_disp_height;
        Display *m_disp;
        Window m_root_wind;
        XVisualInfo m_vinfo;
        XSetWindowAttributes m_attrs;
        Window m_overlay;

        void start();
        void stop();
        int gaze_to_csv(const char*, int);
        bool is_gaze_valid();
        void enque_gaze_data(shared_ptr<custom_gaze_data_t>);
        void print_gaze_data();
        int gaze_data_sz();
        int sample_rate();
        int disp_x_from_normed_x(float);
        int disp_y_from_normed_y(float);
    
        EyeTrackerGaze(int, int, int, int);
        ~EyeTrackerGaze();

    protected:
        int m_buff_sz;
        shared_ptr<circ_buff> m_gaze_buff;

    private:
        shared_ptr<boost::thread> m_async_streamer;
        shared_ptr<boost::thread> m_async_writer;
        shared_ptr<boost::mutex> m_async_mutex;
};

// Default constructor
EyeTrackerGaze::EyeTrackerGaze(
    int disp_width, int disp_height, int mark_freq, int buff_sz) {
        // Init members from args
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

        // Init circular gaze data buffer and mutex
        m_gaze_buff = make_shared<circ_buff>(buff_sz); 
        m_async_mutex = make_shared<boost::mutex>();

        // Set default states
        m_mark_count = 0;
        m_async_writer = NULL;
        m_async_streamer = NULL;
}

// Destructor
EyeTrackerGaze::~EyeTrackerGaze() {
    int64_t t_start = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();

    stop();
    m_async_mutex->lock();
    m_async_mutex->unlock();
    XCloseDisplay(m_disp);

    int64_t t_end = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();
    printf("Destructor took %li.\n\n", (t_end - t_start));
}

// Starts the async gaze threads
void EyeTrackerGaze::start() {
    if (m_async_streamer) {
        printf("ERROR: Gaze stream already running.");
    } else {
        m_async_streamer = make_shared<boost::thread>(
            do_gaze_data_subscribe, m_device, this
        );
    }
}

// Stops the async gaze threads
void EyeTrackerGaze::stop() {
    // Stop the gaze data streamer with an interrupt
    if (m_async_streamer) {
        m_async_streamer->interrupt();
        m_async_streamer->join();
        m_async_streamer = NULL;
    }

    // Wait for writer thread to finish its current write
    if (m_async_writer) {
        m_async_writer->join();
        m_async_writer = NULL;
    }
}

// Writes the gaze data to the given csv file path, creating it if exists 
// else appending to it. If n is given, writes only the most recent n samples.
// Returns an int representing the number of samples written.
int EyeTrackerGaze::gaze_to_csv(const char *file_path, int n=0) {
    // Copy circ buff contents then (effectively) clear it
    m_async_mutex->lock();
    shared_ptr<circ_buff> gaze_buff = m_gaze_buff;
    m_gaze_buff = make_shared<circ_buff>(m_buff_sz);
    m_async_mutex->unlock();

    // Get buff content count and return if empty
    int sample_count = gaze_buff->size();
    if (sample_count <= 0)
        return 0;
    
    // n == 0 denotes write entire buff contents
    if (n == 0)
        n = sample_count;

    // Ensure any previous async write job has finished and free its mem
    if (m_async_writer) {
        m_async_writer->join();
    }

    // Write the gaze data to file asynchronously
    m_async_writer = make_shared<boost::thread>(
        [file_path, gaze_buff, n]() {
            ofstream f, f2;
            f.open(file_path, fstream::in | fstream::out | fstream::app);

            // Write (at most) the n latest samples to csv in ascending order
            int sz = gaze_buff->size();
            int n_capped = min(sz, n);

            for (int j = sz - n_capped; j < sz; j++)  {
                auto cgd = *gaze_buff->at(j); 
                f << 
                    cgd.unixtime_us << ", " <<
                    cgd.left_pupildiameter_mm << ", " <<
                    cgd.right_pupildiameter_mm << ", " <<
                    cgd.left_eyeposition_normed_x << ", " <<
                    cgd.left_eyeposition_normed_y << ", " <<
                    cgd.left_eyeposition_normed_z << ", " <<
                    cgd.right_eyeposition_normed_x << ", " <<
                    cgd.right_eyeposition_normed_y << ", " <<
                    cgd.right_eyeposition_normed_z << ", " <<
                    cgd.left_eyecenter_mm_x << ", " <<
                    cgd.left_eyecenter_mm_y << ", " <<
                    cgd.left_eyecenter_mm_z << ", " <<
                    cgd.right_eyecenter_mm_x << ", " <<
                    cgd.right_eyecenter_mm_y << ", " <<
                    cgd.right_eyecenter_mm_z << ", " <<
                    cgd.left_gazeorigin_mm_x << ", " <<
                    cgd.left_gazeorigin_mm_y << ", " <<
                    cgd.left_gazeorigin_mm_z << ", " <<
                    cgd.right_gazeorigin_mm_x << ", " <<
                    cgd.right_gazeorigin_mm_y << ", " <<
                    cgd.right_gazeorigin_mm_z << ", " <<
                    cgd.left_gazepoint_mm_x << ", " <<
                    cgd.left_gazepoint_mm_y << ", " <<
                    cgd.left_gazepoint_mm_z << ", " <<
                    cgd.right_gazepoint_mm_x << ", " <<
                    cgd.right_gazepoint_mm_y << ", " <<
                    cgd.right_gazepoint_mm_z << ", " <<
                    cgd.left_gazepoint_normed_x << ", " <<
                    cgd.left_gazepoint_normed_y << ", " <<
                    cgd.right_gazepoint_normed_x << ", " <<
                    cgd.right_gazepoint_normed_y << ", " <<
                    cgd.combined_gazepoint_x << ", " <<
                    cgd.combined_gazepoint_y << "\n";
            }

            f.close();
        }
    );

    return sample_count;
}

// Enques gaze data into the circular buffer
void EyeTrackerGaze::enque_gaze_data(shared_ptr<custom_gaze_data_t> cgd) {
    m_async_mutex->lock();
    m_gaze_buff->push_back(cgd);
    m_async_mutex->unlock();
}

// Prints the coord contents of the circular buffer. For debug convenience.
void EyeTrackerGaze::print_gaze_data() {
    circ_buff::iterator i; 

    m_async_mutex->lock();
    for (i = m_gaze_buff->begin(); i < m_gaze_buff->end(); i++)  {
        printf("(%d, %d)\n",
        i->get()->combined_gazepoint_x,
        i->get()->combined_gazepoint_y); 
    }
    m_async_mutex->unlock();

    printf("Gaze sample count: %li\n", m_gaze_buff->size());

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
    m_async_mutex->lock();
    auto cgd_first = *m_gaze_buff->at(0); 
    auto cgd_last = *m_gaze_buff->at(sample_count-1); 
    m_async_mutex->unlock();

    long unsigned int t1 = cgd_first.unixtime_us;
    long unsigned int t2 = cgd_last.unixtime_us;

    // Sample rate, in hz
    double t_diff = (t2 - t1) * .000001;
    double sample_rate = sample_count / t_diff;

    return sample_rate;
}

// Given a normalized gaze point's x coord, returns the x in display coords.
int EyeTrackerGaze::disp_x_from_normed_x(float x_normed) {
    return x_normed * m_disp_width;
}

// Given a normalized gaze point's y coord, returns the x in display coords.
int EyeTrackerGaze::disp_y_from_normed_y(float y_normed) {
    return y_normed * m_disp_height;
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
        // delete gaze;
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
void do_gaze_data_subscribe(tobii_device_t *device, void *gaze) {

    // Subscribe to gaze point
    assert(tobii_gaze_data_subscribe(device, cb_gaze_data, gaze
    ) == NO_ERROR);

    try {
        while (True) {
            assert(tobii_wait_for_callbacks(1, &device) == NO_ERROR);
            assert(tobii_device_process_callbacks(device) == NO_ERROR);
            boost::this_thread::sleep_for(boost::chrono::microseconds{1});
        }
    } catch (boost::thread_interrupted&) {}

    int64_t t_start = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();
    
    assert(tobii_gaze_data_unsubscribe(device) == NO_ERROR);
    
    int64_t t_end = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();

    printf("\nUnsubscribe took %li.\n\n", (t_end - t_start));
}


// Gaze point callback for use with tobii_gaze_point_subscribe(). Gets the
// eyetrackers predicted on-screen gaze coordinates (x, y) and enques gaze
// data into EyeTrackerGazes' circular buffer. Also creates a shaded window
// overlay denoting the gaze point on the screen.
// ASSUMES: user_data is a ptr to an object of type EyeTrackerGaze.
static void cb_gaze_data(tobii_gaze_data_t const *gaze_data, void *user_data) {
    EyeTrackerGaze *gaze = static_cast<EyeTrackerGaze*>(user_data);

    if(gaze_data->left.gaze_point_validity == TOBII_VALIDITY_VALID ==
    gaze_data->right.gaze_point_validity) {
        
        // Convert gaze point to screen coords
        int left_gazepoint_x = gaze->disp_x_from_normed_x(
            gaze_data->left.gaze_point_on_display_normalized_xy[0]);
        int left_gazepoint_y = gaze->disp_y_from_normed_y(
            gaze_data->left.gaze_point_on_display_normalized_xy[1]);
            
        int right_gazepoint_x = gaze->disp_x_from_normed_x(
            gaze_data->right.gaze_point_on_display_normalized_xy[0]);
        int right_gazepoint_y = gaze->disp_y_from_normed_y(
            gaze_data->right.gaze_point_on_display_normalized_xy[1]);

        int x_gazepoint = (left_gazepoint_x + right_gazepoint_x) / 2;
        int y_gazepoint = (left_gazepoint_y + right_gazepoint_y) / 2;

        // Convert timestamp from device time to system clock time
        int64_t timestamp_us = gaze->devicetime_to_systime(
            gaze_data->timestamp_system_us);

        // Copy data
        shared_ptr<custom_gaze_data_t> cgd = make_shared<custom_gaze_data_t>();

        cgd->unixtime_us = timestamp_us;
        cgd->left_pupildiameter_mm = gaze_data->left.pupil_diameter_mm;
        cgd->right_pupildiameter_mm = gaze_data->right.pupil_diameter_mm;
        cgd->left_eyeposition_normed_x = 
            gaze_data->left.eye_position_in_track_box_normalized_xyz[0];
		cgd->left_eyeposition_normed_y = 
            gaze_data->left.eye_position_in_track_box_normalized_xyz[1];
		cgd->left_eyeposition_normed_z = 
            gaze_data->left.eye_position_in_track_box_normalized_xyz[2];
		cgd->right_eyeposition_normed_x = 
            gaze_data->right.eye_position_in_track_box_normalized_xyz[0];
		cgd->right_eyeposition_normed_y = 
            gaze_data->right.eye_position_in_track_box_normalized_xyz[1];
		cgd->right_eyeposition_normed_z = 
            gaze_data->right.eye_position_in_track_box_normalized_xyz[2];
        cgd->left_eyecenter_mm_x = 
            gaze_data->left.eyeball_center_from_eye_tracker_mm_xyz[0];
		cgd->left_eyecenter_mm_y = 
            gaze_data->left.eyeball_center_from_eye_tracker_mm_xyz[1];
		cgd->left_eyecenter_mm_z = 
            gaze_data->left.eyeball_center_from_eye_tracker_mm_xyz[2];
		cgd->right_eyecenter_mm_x = 
            gaze_data->right.eyeball_center_from_eye_tracker_mm_xyz[0];
		cgd->right_eyecenter_mm_y = 
            gaze_data->right.eyeball_center_from_eye_tracker_mm_xyz[1];
		cgd->right_eyecenter_mm_z = 
            gaze_data->right.eyeball_center_from_eye_tracker_mm_xyz[2];
        cgd->left_gazeorigin_mm_x = 
            gaze_data->left.gaze_origin_from_eye_tracker_mm_xyz[0];
		cgd->left_gazeorigin_mm_y = 
            gaze_data->left.gaze_origin_from_eye_tracker_mm_xyz[1];
		cgd->left_gazeorigin_mm_z = 
            gaze_data->left.gaze_origin_from_eye_tracker_mm_xyz[2];
		cgd->right_gazeorigin_mm_x = 
            gaze_data->right.gaze_origin_from_eye_tracker_mm_xyz[0];
		cgd->right_gazeorigin_mm_y = 
            gaze_data->right.gaze_origin_from_eye_tracker_mm_xyz[1];
		cgd->right_gazeorigin_mm_z = 
            gaze_data->right.gaze_origin_from_eye_tracker_mm_xyz[2];
        cgd->left_gazepoint_mm_x = 
            gaze_data->left.gaze_point_from_eye_tracker_mm_xyz[0];
		cgd->left_gazepoint_mm_y = 
            gaze_data->left.gaze_point_from_eye_tracker_mm_xyz[1];
		cgd->left_gazepoint_mm_z = 
            gaze_data->left.gaze_point_from_eye_tracker_mm_xyz[2];
		cgd->right_gazepoint_mm_x = 
            gaze_data->right.gaze_point_from_eye_tracker_mm_xyz[0];
		cgd->right_gazepoint_mm_y = 
            gaze_data->right.gaze_point_from_eye_tracker_mm_xyz[1];
		cgd->right_gazepoint_mm_z = 
            gaze_data->right.gaze_point_from_eye_tracker_mm_xyz[2];
        cgd->left_gazepoint_normed_x = 
            gaze_data->left.gaze_point_on_display_normalized_xy[0];
		cgd->left_gazepoint_normed_y = 
            gaze_data->left.gaze_point_on_display_normalized_xy[1];
		cgd->right_gazepoint_normed_x = 
            gaze_data->right.gaze_point_on_display_normalized_xy[0];
		cgd->right_gazepoint_normed_y = 
            gaze_data->right.gaze_point_on_display_normalized_xy[1];
        cgd->combined_gazepoint_x = x_gazepoint;
        cgd->combined_gazepoint_y = y_gazepoint;

        gaze->enque_gaze_data(cgd);

        // Annotate (x, y) on the screen every m_mark_freq callbacks
        gaze->m_mark_count++;
        if (gaze->m_mark_count % gaze->m_mark_freq != 0)
            return;

        // Else, reset the gaze mark count & create gaze marker overlay
        gaze->m_mark_count = 0;

        gaze->m_overlay = XCreateWindow(
            gaze->m_disp,
            gaze->m_root_wind,
            x_gazepoint,
            y_gazepoint, 
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

    } else {
        // printf("WARN: Invalid gaze_point.\n"); // debug
    }

}
