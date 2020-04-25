// A collection of helpers for using the Tobii Stream Engine API

#include <assert.h>
#include <stdio.h>
#include <cstring>

#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>

using namespace std;

#define URL_MAX_LEN 256


// A gaze point callback that prints gaze data to stdout as it is received.
void gaze_print_callback(tobii_gaze_point_t const *gaze_point, void *user_data) {
    if (gaze_point->validity == TOBII_VALIDITY_VALID)
        printf("Gaze point: %f, %f\n",
               gaze_point->position_xy[0],
               gaze_point->position_xy[1]);
}


// Populates user_data with the first eyetracker found.
static void single_url_receiver(char const *url, void *user_data) {
    char *buffer = (char *) user_data;

    if (*buffer != '\0') return; // only keep first device

    if (strlen(url) < URL_MAX_LEN)
        strcpy(buffer, url);
}


// Prints details of the given device to stdout.
tobii_error_t print_device_info(tobii_device_t *device) {
    tobii_device_info_t info;

    tobii_error_t error = tobii_get_device_info(device, &info);
    
    if (error != TOBII_ERROR_NO_ERROR)
        return error;
    
    printf("Device SN: %s\n", info.serial_number);
    printf("Device Model: %s\n", info.model);
    printf("Device Generation: %s\n", info.generation);
    printf("Device Firmware Ver: %s\n", info.firmware_version);
    printf("Device Integration ID: %s\n", info.integration_id);
    printf("Device Calibration Ver: %s\n", info.hw_calibration_version);
    printf("Device Calibration Date: %s\n", info.hw_calibration_date);
    printf("Device Lot ID: %s\n", info.lot_id);
    printf("Device Integration Type: %s\n", info.integration_type);
    printf("Device Runtime Build Ver: %s\n", info.runtime_build_version);

    return error;
}