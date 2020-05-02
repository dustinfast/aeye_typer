/////////////////////////////////////////////////////////////////////////////
// Demonstrates eye-tracking by connecting to the eye tracker and marking
// gaze point to the screen in real time for the duration given by GAZE_TIME.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <stdio.h>

// #include <boost/chrono.hpp>

#include "eyetracker_gaze.h"

using namespace std;


#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160
#define GAZE_MARK_INTERVAL 7
#define GAZE_BUFF_SZ 450000
#define GAZE_TIME 1


int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        DISP_WIDTH, DISP_HEIGHT, GAZE_MARK_INTERVAL, GAZE_BUFF_SZ);

    printf("Marking gaze point for %d seconds from device...\n", GAZE_TIME);
    gaze.print_device_info();
    gaze.sync_device_time();
    
    gaze.start();
    boost::this_thread::sleep_for(boost::chrono::seconds{GAZE_TIME});
    // gaze.gaze_to_csv("test.csv");
    // gaze.sample_rate();
    gaze.stop();

    return 0;
}