/////////////////////////////////////////////////////////////////////////////
// An abstraction of an eye tracker.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////


#include <assert.h>
#include <stdio.h>
#include <cstring>
#include <chrono>


#include <tobii/tobii.h>
#include <tobii/tobii_config.h>
#include <tobii/tobii_streams.h>
#include "tobii/tobii_licensing.h"
#include <boost/thread.hpp>

using namespace std;
using namespace std::chrono;

/////////////////////////////////////////////////////////////////////////////
// Defs

#define URL_MAX_LEN 256
#define LIC_PATH "/opt/app/src/licenses/fast_aeye_typer_temp_se_license_key"
#define NO_ERROR TOBII_ERROR_NO_ERROR

void sync_device_time_async(tobii_device_t *device);
static size_t read_license_file(uint16_t* license);
void single_url_receiver(char const *url, void *user_data);


/////////////////////////////////////////////////////////////////////////////
// Class

class EyeTracker {
    public:
        EyeTracker();
        ~EyeTracker();
        int64_t devicetime_to_systime(int64_t);
        void sync_device_time();
        void print_device_info();
        void print_feature_group();

    protected:
        int64_t m_device_time_offset;
        bool m_is_elevated;
        tobii_device_t *m_device;
        tobii_api_t *m_api;
    
    private:
        boost::thread *m_async_time_syncer;
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
    // TODO: Catch file not found
    size_t license_size = read_license_file(0);
    assert(license_size > 0);
    uint16_t* license_key = (uint16_t*)malloc(license_size);
    memset(license_key, 0, license_size);
    read_license_file(license_key);

    // Attemtp to open the eyetracker with elevated privelidges
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
        printf("WARN: Failed to create elevated eyetracking device... ");

        if (validation_result == TOBII_LICENSE_VALIDATION_RESULT_EXPIRED) {
            printf("License expired.");
        } else {
            printf("License invalid.");
        }

        printf("\nINFO: Using non-elevated device instead...\n");
        assert(tobii_device_create(m_api, url, &m_device) == NO_ERROR);
        m_is_elevated = False;
    
    // Else if elevated create succeeded
    } else {
        printf("INFO: Using elevated eyetracking device...\n");
        m_is_elevated = True;
    }
    
    // Set default states
    m_async_time_syncer = NULL;
    m_device_time_offset = 0;
}

// Destructor
EyeTracker::~EyeTracker() {
    // Cleanup the time synchronizer iff needed
    if (m_async_time_syncer) {
        m_async_time_syncer->interrupt();
        delete m_async_time_syncer;
    }

    // Destroy the eyetracker device instance
    assert(tobii_device_destroy(m_device) == NO_ERROR);
    assert(tobii_api_destroy(m_api) == NO_ERROR);
}

// The device clock and the system clock it's connected to may drift over time
// therefore they need to be synchronized every ~30 seconds for accurate device 
// timestamps. Calling this function will cause that to occur asynchronously.
void EyeTracker::sync_device_time() {
    // Start syncing time asynchronously
    m_async_time_syncer = new boost::thread(sync_device_time_async, m_device);

    //Establish device to system clock offset (in mircroseconds)
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

    assert(tobii_get_device_info(m_device, &info) == NO_ERROR);
    
    printf("Device SN: %s\n", info.serial_number);
    printf("Device Model: %s\n", info.model);
    printf("Device Generation: %s\n", info.generation);
    printf("Device Firmware Ver: %s\n", info.firmware_version);
    printf("Device Calibration Ver: %s\n", info.hw_calibration_version);
    printf("Device Calibration Date: %s\n", info.hw_calibration_date);
    printf("Device Integration Type: %s\n", info.integration_type);
    printf("Device Runtime Build Ver: %s\n", info.runtime_build_version);
}

void EyeTracker::print_feature_group() {
    tobii_feature_group_t feature_group;
    tobii_error_t error = tobii_get_feature_group(m_device, &feature_group);
    assert(error == TOBII_ERROR_NO_ERROR );
    if( feature_group == TOBII_FEATURE_GROUP_BLOCKED)
        printf( "Running with 'blocked' feature group.\n" );
    if( feature_group == TOBII_FEATURE_GROUP_CONSUMER)
        printf( "Running with 'consumer' feature group.\n" );
    if( feature_group == TOBII_FEATURE_GROUP_CONFIG)
        printf( "Running with 'config' feature group.\n" );
    if( feature_group == TOBII_FEATURE_GROUP_PROFESSIONAL)
        printf( "Running with 'professional' feature group.\n" );
    if( feature_group == TOBII_FEATURE_GROUP_INTERNAL)
        printf( "Running with 'internal' feature group.\n" );
}



/////////////////////////////////////////////////////////////////////////////
// Misc Helpers

// Syncs eyetracker device time w/ system clock every 30s until interrupted
void sync_device_time_async(tobii_device_t *device) {
    try {
        while (True) {
            tobii_update_timesync(device);
            boost::this_thread::sleep_for(boost::chrono::seconds{30});
        }
    } catch (boost::thread_interrupted&) {}
}

// Reads an eyetracker license file (Copied from the tobii stream SDK docs)
static size_t read_license_file(uint16_t* license) {
    FILE *license_file = fopen(LIC_PATH, "rb");

    if(!license_file) {
        printf("License key could not be found!");
        return 0;
    }
    fseek(license_file, 0, SEEK_END);

    long file_size = ftell(license_file);
    rewind(license_file);

    if(file_size <= 0){
        printf("License file is empty!");
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
