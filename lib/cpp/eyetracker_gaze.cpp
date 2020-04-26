// Connects to the eye tracker and marks gaze point to the screen in real time.

#include <assert.h>
#include <stdio.h>

#include <boost/chrono.hpp>

#include "eyetracker_gaze.h"

using namespace std;


// TODO: Move to config
#define DISP_WIDTH 3840
#define DISP_HEIGHT 2160
#define GAZE_MARK_INTERVAL 8
#define GAZE_BUFF_SZ 10
#define GAZE_TIME 3


int main() {
    EyeTrackerGaze gaze = EyeTrackerGaze(
        DISP_WIDTH, DISP_HEIGHT, GAZE_MARK_INTERVAL, GAZE_BUFF_SZ);

    printf("Marking gaze point for %d seconds...\n", GAZE_TIME);
    
    gaze.start();
    boost::this_thread::sleep_for(boost::chrono::seconds{GAZE_TIME});
    gaze.stop();

    printf("Done.\n\nLast %d gaze coords:\n", GAZE_BUFF_SZ);
    gaze.print_gaze_data();

    return 0;
}