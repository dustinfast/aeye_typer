/////////////////////////////////////////////////////////////////////////////
// An abstraction of an eye tracker.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <fstream>
#include <assert.h>
#include <stdio.h>
#include <cstring>
#include <chrono>

#include <tobii/tobii.h>
#include <tobii/tobii_config.h>
#include <tobii/tobii_streams.h>
#include <tobii/tobii_licensing.h>
#include <tobii/tobii_advanced.h>

#include <boost/thread.hpp>

#include "app.h"

using namespace std;
using namespace std::chrono;

/////////////////////////////////////////////////////////////////////////////
// Defs

#define URL_MAX_LEN 256
#define CALIB_FILE_MAX_BYTES 400000
#define NO_ERROR TOBII_ERROR_NO_ERROR

string CALIB_PATH = APP_CFG["EYETRACKER_CALIB_PATH"].Scalar().c_str();
string LIC_PATH = APP_CFG["EYETRACKER_LICENSE_PATH"].Scalar().c_str();

/////////////////////////////////////////////////////////////////////////////
// Prototypes

void sync_device_time_async(tobii_device_t *device);
size_t read_license_file(uint16_t* license);
void single_url_receiver(char const *url, void *user_data);
void calibration_writer(void const* data, size_t size, void* user_data);

/////////////////////////////////////////////////////////////////////////////
// Class

class EyeTracker {
    public:
        EyeTracker();
        ~EyeTracker();
        void sync_device_time();
        void print_device_info();
        void print_feature_group();
        void calibration_write();
        int64_t devicetime_to_systime(int64_t);

    protected:
        int64_t m_device_time_offset;
        tobii_device_t *m_device;
        tobii_api_t *m_api;
        bool m_is_elevated;
        void set_display(float, float, float);
        void calibration_load();
    
    private:
        shared_ptr<boost::thread> m_async_time_syncer;
};

// Default constructor
EyeTracker::EyeTracker() {
    // Instantiate eyetracker api
    assert(tobii_api_create(&m_api, NULL, NULL) == NO_ERROR);

    char url[256] = {0};
    assert(
        tobii_enumerate_local_device_urls(m_api, single_url_receiver, url
        ) == NO_ERROR && *url != '\0'
    );

    // Attempt to load an eyetracker device license file
    size_t license_size = read_license_file(0);
    assert(license_size > 0);
    uint16_t* license_key = (uint16_t*)malloc(license_size);
    memset(license_key, 0, license_size);
    read_license_file(license_key);

    // Attempt to open the eyetracker with elevated privelidges
    tobii_license_key_t license = {license_key, license_size};
    tobii_license_validation_result_t validation_result;
    tobii_device_create_ex(m_api,
                            url,
                            &license,
                            1,
                            &validation_result,
                            &m_device
    );

    free(license_key);

    // If open elevated failed, open in unelevated mode
    if (validation_result != TOBII_LICENSE_VALIDATION_RESULT_OK) {
        warn("Failed to create elevated eyetracking device... ");

        if (validation_result == TOBII_LICENSE_VALIDATION_RESULT_EXPIRED) {
            printf("License expired. ");
        } else {
            printf("License invalid. ");
        }

        printf("Using non-elevated device instead...\n");
        assert(tobii_device_create(m_api, url, &m_device) == NO_ERROR);
        m_is_elevated = False;
    
    // Else if elevated create succeeded
    } else {
        info("Using elevated eyetracking device.\n");
        m_is_elevated = True;
    }

    // Load calibration from file -- if no exist, will warn
    calibration_load();
    
    // Set default states
    m_async_time_syncer = NULL;
    m_device_time_offset = 0;
}

// Destructor
EyeTracker::~EyeTracker() {
    // Cleanup the time synchronizer iff needed
    if (m_async_time_syncer) {
        m_async_time_syncer->interrupt();
        m_async_time_syncer->join();
    }

    // Destroy the eyetracker device instance
    assert(tobii_device_destroy(m_device) == NO_ERROR);
    assert(tobii_api_destroy(m_api) == NO_ERROR);
}

// The device clock and the system clock it's connected to may drift over time
// therefore they need to be synchronized every ~30 seconds for accurate device 
// timestamps. Calling this function will cause that to occur asynchronously.
void EyeTracker::sync_device_time() {
    if (m_async_time_syncer)
        return;  // No need to run multiple times

    // Start syncing time asynchronously
    shared_ptr<boost::thread> m_async_time_syncer = 
        make_shared<boost::thread>(sync_device_time_async, m_device);

    //Establish device to system clock offset (in microseconds)
    assert(tobii_system_clock(m_api, &m_device_time_offset) == NO_ERROR);
    m_device_time_offset = 
        time_point_cast<microseconds>(system_clock::now()
            ).time_since_epoch().count() - m_device_time_offset;
}

// Given a device timestamp, returns the timestamp after applying the system
// clock offset to it. This is necessary because the device knows nothing 
// about the epoch.
// Note: You MUST call sync_device_time at least once before using this.
int64_t EyeTracker::devicetime_to_systime(int64_t device_time) {
    return device_time + m_device_time_offset;
}

// Prints eyetracker device info
void EyeTracker::print_device_info() {
    tobii_device_info_t info;
    tobii_supported_t supported;

    assert(tobii_get_device_info(m_device, &info) == NO_ERROR);
    
    // Basic device info
    printf("Device SN: %s\n", info.serial_number);
    printf("Device Model: %s\n", info.model);
    printf("Device Generation: %s\n", info.generation);
    printf("Device Firmware Ver: %s\n", info.firmware_version);
    printf("Device Calibration Ver: %s\n", info.hw_calibration_version);
    printf("Device Calibration Date: %s\n", info.hw_calibration_date);
    printf("Device Integration Type: %s\n", info.integration_type);
    printf("Device Runtime Build Ver: %s\n", info.runtime_build_version);

    // Feature group
    print_feature_group();

    // Supported streams info
    printf("Device supports stream user presence: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_USER_PRESENCE, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }
    
    printf("\nDevice supports stream gaze point: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_GAZE_POINT, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }
    
    printf("\nDevice supports stream gaze origin: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_GAZE_ORIGIN, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\nDevice supports stream eye position: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_EYE_POSITION_NORMALIZED, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\nDevice supports stream position guide: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_USER_POSITION_GUIDE, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\nDevice supports stream head pose: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_HEAD_POSE, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\nDevice supports stream gaze data: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_GAZE_DATA, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\nDevice supports stream diag image: "); 
    tobii_stream_supported(m_device, TOBII_STREAM_DIAGNOSTICS_IMAGE, &supported);
    if(supported == TOBII_SUPPORTED) { printf( "True" ); 
    } else { printf( "False" ); }

    printf("\n");
}

// Prints the device's active feature group to stdout. Note that the feature
// group is mostly dependent on the license file loaded, if any.
void EyeTracker::print_feature_group() {
    tobii_feature_group_t feature_group;
    tobii_error_t error = tobii_get_feature_group(m_device, &feature_group);
    assert(error == NO_ERROR );

    printf("Device Feature Group: ");
    if(feature_group == TOBII_FEATURE_GROUP_BLOCKED)
        printf("Blocked");
    else if(feature_group == TOBII_FEATURE_GROUP_CONSUMER)
        printf("Consumer");
    else if(feature_group == TOBII_FEATURE_GROUP_CONFIG)
        printf("Config");
    else if(feature_group == TOBII_FEATURE_GROUP_PROFESSIONAL)
        printf("Professional");
    else if(feature_group == TOBII_FEATURE_GROUP_INTERNAL)
        printf("Internal");
    else
        printf("Unknown");
    printf("\n");
}

// Sets the eyetrackers's display area from the given screen sz & device-mount offset.
void EyeTracker::set_display(float width_mm, float height_mm, float offset_x_mm) {
    tobii_error_t error;
    tobii_geometry_mounting_t geo_mounting;
    tobii_display_area_t display_area;

    // Get mounting geometry
    error = tobii_get_geometry_mounting(m_device, &geo_mounting);
    assert(error == NO_ERROR );

    // Calculate display area
    error = tobii_calculate_display_area_basic(
        m_api, width_mm, height_mm, offset_x_mm, &geo_mounting, &display_area);
    assert(error == NO_ERROR );
    
    // Set device's disp area
    error = tobii_set_display_area(m_device, &display_area);
    assert(error == NO_ERROR );
}

// Requests that the eyetracker's calibration be written to file
void EyeTracker::calibration_write() {
    tobii_error_t error;
    void *v;

    error = tobii_calibration_retrieve(m_device, calibration_writer, v);
    assert(error == NO_ERROR );
}

// Sets the eyetracker's calibration from file
void EyeTracker::calibration_load() {
    tobii_error_t error;
    size_t size;
    void *data[CALIB_FILE_MAX_BYTES];

    // Load calibration data from file
    fstream f(CALIB_PATH, ios::in | ios::binary);
    
    // Ensure file exists
    if (!f) {
        warn("Calibration load failed. Please calibrate your device with ");
        printf("'./aeye_typer.py --calibrate'. This error may be ignored if ");
        printf("encountered during calibration.\n");
        return;
    }

    // Read up to max bytes
    f.read((char*)data, CALIB_FILE_MAX_BYTES);
    size = f.gcount();
    f.close();

    // Apply the calibration data
    error = tobii_calibration_apply(m_device, data, size);
    if (error != NO_ERROR) {
        if (error == TOBII_ERROR_INSUFFICIENT_LICENSE)
            warn("Calibration load failed (insufficient license).\n");
        else
            warn("Calibration load failed (unknown reason).\n");
    } else {
        info("Calibration loaded successfully.\n");
    }
}

/////////////////////////////////////////////////////////////////////////////
// Misc Helpers

// Callback for writing eyetracker device calibration to file
void calibration_writer(void const* data, size_t size, void* _) {
    // Ensure reasonable size
    if (size >= CALIB_FILE_MAX_BYTES) {
        error("Calibration write failed - Data sz outside expected bounds.\n");
        return;
    }

    // Write calibration data to file
    fstream f(CALIB_PATH, ios::out | ios::binary);
    f.write((char*)data, size);
    f.close();
}

// Syncs eyetracker device time w/ system clock every 30s until interrupted
void sync_device_time_async(tobii_device_t *device) {
    try {
        while (True) {
            tobii_update_timesync(device);
            boost::this_thread::sleep_for(boost::chrono::seconds{10});
        }
    } catch (boost::thread_interrupted&) {}
}

// Reads an eyetracker license file (Copied from the tobii stream SDK docs)
size_t read_license_file(uint16_t* license) {
    FILE *license_file = fopen(LIC_PATH.c_str(), "rb");

    if(!license_file) {
        error("License load failed (file not found)");
        return 0;
    }
    fseek(license_file, 0, SEEK_END);

    long file_size = ftell(license_file);
    rewind(license_file);

    if(file_size <= 0){
        error("License load failed (file is empty)");
        return 0;
    }

    if(license) {
        fread(license, sizeof(uint16_t), file_size / sizeof(uint16_t), license_file);
    }

    fclose(license_file);
    return (size_t)file_size;
}


// Populates user_data with the first eyetracker found.
void single_url_receiver(char const *url, void *user_data) {
    char *buffer = (char *) user_data;

    if (*buffer != '\0') return; // only keep first device

    if (strlen(url) < URL_MAX_LEN)
        strcpy(buffer, url);
}
