// Connects to the eye tracker and marks gaze point to the screen in real time.

#include <assert.h>
#include <stdio.h>

#include "eyetracker.h"
#include "eyetracker_gazestatus.h"

using namespace std;


#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160
#define GAZE_MARK_INTERVAL 7


int main() {
    // Connect to eyetracker
    EyeTracker e = EyeTracker();

    printf("\n*** Eye Tracking Device Detected!\n");
    e.print_device_info();

    // Instantiate gaze status
    GazeStatus gaze = GazeStatus(DISP_WIDTH, DISP_HEIGHT, GAZE_MARK_INTERVAL);


    // Subscribe to gaze point
    assert(tobii_gaze_point_subscribe(e.device, cb_gaze_point, &gaze
    ) == TOBII_ERROR_NO_ERROR);

    printf("Marking gaze point...\n");
    int is_running = 1000;
    while (--is_running > 0) {
        assert(tobii_wait_for_callbacks(1, &e.device) == TOBII_ERROR_NO_ERROR);
        assert(tobii_device_process_callbacks(e.device) == TOBII_ERROR_NO_ERROR);
    }

    assert(tobii_gaze_point_unsubscribe(e.device) == TOBII_ERROR_NO_ERROR);

    return 0;
}