/////////////////////////////////////////////////////////////////////////////
// Demonstrates eye-tracking by connecting to the eye tracker and marking
// gaze point to the screen in real time for the duration given by GAZE_TIME.
//
// Usage: See main()
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
/////////////////////////////////////////////////////////////////////////////

#include <stdio.h>

#include "eyetracker_gaze.h"

using namespace std;


#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160
#define GAZE_MARK_INTERVAL 15
#define GAZE_BUFF_SZ 10
#define GAZE_TIME 600


int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        DISP_WIDTH, DISP_HEIGHT, GAZE_MARK_INTERVAL, GAZE_BUFF_SZ);

    // printf("Marking gaze point for %d seconds from device...\n", GAZE_TIME);
    gaze.print_device_info();
    
    gaze.start();

    for (int i = 0; i < GAZE_TIME; i++) {
        boost::this_thread::sleep_for(boost::chrono::seconds{1});
        gaze.gaze_to_csv("test.csv", 10);
    }

    int64_t t_start = time_point_cast<milliseconds>(system_clock::now()
        ).time_since_epoch().count();

    gaze.stop();

    int64_t t_end = time_point_cast<milliseconds>(system_clock::now()
            ).time_since_epoch().count();

    printf("Stopped in %li.\n\n", (t_end - t_start));

    return 0;
}