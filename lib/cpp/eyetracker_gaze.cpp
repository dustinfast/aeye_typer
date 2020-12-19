/////////////////////////////////////////////////////////////////////////////
// Demonstrates eye-tracking by connecting to the eye tracker and marking
// gaze point to the screen in real time for the duration given by GAZE_TIME.
//
// Usage: See main()
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
/////////////////////////////////////////////////////////////////////////////

#include <stdio.h>

#include "app.h"
#include "eyetracker_gaze.h"

using namespace std;


#define GAZE_TIME 2


int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        APP_CFG["EYETRACKER_MOUNT_OFFSET_MM"].as<float>(),
        APP_CFG["DISP_WIDTH_MM"].as<float>(),
        APP_CFG["DISP_HEIGHT_MM"].as<float>(),
        APP_CFG["DISP_WIDTH_PX"].as<int>(),
        APP_CFG["DISP_HEIGHT_PX"].as<int>(),
        APP_CFG["EYETRACKER_MARK_INTERVAL"].as<int>(),
        APP_CFG["EYETRACKER_BUFF_SZ"].as<int>(),
        APP_CFG["EYETRACKER_SMOOTH_OVER"].as<int>()
    );
    
    gaze.print_device_info();
    
    printf("\nMarking real-time gaze point for %d seconds...\n", GAZE_TIME);
    gaze.start();

    for (int i = 0; i < GAZE_TIME; i++) {
        boost::this_thread::sleep_for(boost::chrono::seconds{1});
    }

    gaze.stop();

    return 0;
}