#include <stdio.h>
#include <assert.h>
#include <cstring>


#include "tobii_stream_eng.h"
#include <tobii/tobii_config.h>

using namespace std;


int main() {
    // Connect to default eye-tracker
    tobii_api_t *api;
    tobii_error_t error = tobii_api_create(&api, NULL, NULL);
    assert(error == TOBII_ERROR_NO_ERROR);

    char url[256] = {0};
    error = tobii_enumerate_local_device_urls(api, single_url_receiver, url);
    assert(error == TOBII_ERROR_NO_ERROR && *url != '\0');

    tobii_device_t *device;
    error = tobii_device_create(api, url, &device);
    assert(error == TOBII_ERROR_NO_ERROR);

    printf("Device found:\n");
    error = print_device_info(device);
    assert(error == TOBII_ERROR_NO_ERROR);

    // Ensure device is capable of 2D calibration
    tobii_capability_t capability = TOBII_CAPABILITY_CALIBRATION_2D;
    tobii_supported_t supported;
    error =  tobii_capability_supported(device, capability, &supported );
    assert(error == TOBII_ERROR_NO_ERROR);
    assert(supported == TOBII_SUPPORTED);

    // error = tobii_gaze_point_subscribe(device, gaze_point_callback, 0);
    // assert(error == TOBII_ERROR_NO_ERROR);

    // int is_running = 1000; // in this sample, exit after some iterations
    // while (--is_running > 0) {
    //     error = tobii_wait_for_callbacks(1, &device);
    //     assert(error == TOBII_ERROR_NO_ERROR || error == TOBII_ERROR_TIMED_OUT);

    //     error = tobii_device_process_callbacks(device);
    //     assert(error == TOBII_ERROR_NO_ERROR);
    // }

    // error = tobii_gaze_point_unsubscribe(device);
    // assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_device_destroy(device);
    assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_api_destroy(api);
    assert(error == TOBII_ERROR_NO_ERROR);
    return 0;
}