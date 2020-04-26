// An abstraction of an Eyetracker.

#include <assert.h>
#include <stdio.h>
#include <cstring>

#include <tobii/tobii.h>
#include <tobii/tobii_config.h>
#include <tobii/tobii_streams.h>

using namespace std;


#define URL_MAX_LEN 256

static void single_url_receiver(char const *url, void *user_data);


class EyeTracker {
    tobii_api_t *api;
    void set_display();

    public:
        tobii_device_t *device;

        EyeTracker();
        ~EyeTracker();
        void print_device_info();
};

// Default constructor
EyeTracker::EyeTracker() {
    // Connect to the default eyetracker
    assert(tobii_api_create(&api, NULL, NULL) == TOBII_ERROR_NO_ERROR);

    char url[256] = {0};
    assert(
        tobii_enumerate_local_device_urls(api, single_url_receiver, url
        ) == TOBII_ERROR_NO_ERROR && *url != '\0'
    );

    assert(tobii_device_create(api, url, &device) == TOBII_ERROR_NO_ERROR);
}

// Destructor
EyeTracker::~EyeTracker() {
    assert(tobii_device_destroy(device) == TOBII_ERROR_NO_ERROR);
    assert(tobii_api_destroy(api) == TOBII_ERROR_NO_ERROR);
}

void EyeTracker::print_device_info() {
    tobii_device_info_t info;

    assert(tobii_get_device_info(device, &info) == TOBII_ERROR_NO_ERROR);
    
    printf("Device SN: %s\n", info.serial_number);
    printf("Device Model: %s\n", info.model);
    printf("Device Generation: %s\n", info.generation);
    printf("Device Firmware Ver: %s\n", info.firmware_version);
    printf("Device Calibration Ver: %s\n", info.hw_calibration_version);
    printf("Device Calibration Date: %s\n", info.hw_calibration_date);
    printf("Device Integration Type: %s\n", info.integration_type);
    printf("Device Runtime Build Ver: %s\n", info.runtime_build_version);
}

void EyeTracker::set_display() {
    // TODO: Get and set display area
    // tobii_geometry_mounting_t *geometry_mounting = new tobii_geometry_mounting_t;
    // error = tobii_get_geometry_mounting(device, geometry_mounting);
    // assert(error == TOBII_ERROR_NO_ERROR);

    // tobii_display_area_t* d_area = new tobii_display_area_t;
    // error = tobii_calculate_display_area_basic(
    //     api,
    //     698.5, // width
    //     393.7, // height
    //     0, // offset
    //     geometry_mounting,
    //     d_area
    // );
    // assert(error == TOBII_ERROR_NO_ERROR);

    // error = tobii_set_display_area(device, d_area);
    // assert(error == TOBII_ERROR_INSUFFICIENT_LICENSE);
    // assert(error == TOBII_ERROR_NO_ERROR);
}

// Populates user_data with the first eyetracker found.
static void single_url_receiver(char const *url, void *user_data) {
    char *buffer = (char *) user_data;

    if (*buffer != '\0') return; // only keep first device

    if (strlen(url) < URL_MAX_LEN)
        strcpy(buffer, url);
}
