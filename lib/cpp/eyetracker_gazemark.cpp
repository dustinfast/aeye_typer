// Connects to the eye tracker and marks gaze point to the screen in real time.

#include <assert.h>
#include <stdio.h>

// #include "eyetracker.h"
#include "eyetracker_gazestatus.h"

using namespace std;


// TODO: Move to config
#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160
#define GAZE_MARK_INTERVAL 7
#define GAZE_BUFF_SZ 10


int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        DISP_WIDTH, DISP_HEIGHT, GAZE_MARK_INTERVAL, GAZE_BUFF_SZ);

    printf("Marking gaze point...\n");
    gaze.start(0);

    gaze.print_gaze_data();

    return 0;
}