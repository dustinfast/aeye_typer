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


// TODO: These are in the conf - pull them from there instead
#define DISP_WIDTH_MM 597.0
#define DISP_HEIGHT_MM 335
#define DISP_WIDTH_PX 3840
#define DISP_HEIGHT_PX 2160
#define MOUNT_OFFSET_MM 0.0
#define GAZE_MARK_INTERVAL 5
#define GAZE_BUFF_SZ 45000
#define GAZE_SMOOTHOVER 4
#define GAZE_TIME 3

int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        MOUNT_OFFSET_MM,
        DISP_WIDTH_MM,
        DISP_HEIGHT_MM,
        DISP_WIDTH_PX,
        DISP_HEIGHT_PX,
        GAZE_MARK_INTERVAL,
        GAZE_BUFF_SZ,
        GAZE_SMOOTHOVER
    );
    
    gaze.print_device_info();
    
    printf("\nMarking real-time gaze point for %d seconds...\n", GAZE_TIME);
    gaze.start();

    for (int i = 0; i < GAZE_TIME; i++) {
        boost::this_thread::sleep_for(boost::chrono::seconds{1});
    }

    gaze.stop();

    printf("Done.\n");
    return 0;
}