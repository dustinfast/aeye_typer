// Handles keyboard and mouse button-press logging
// Author: Dustin Fast, 2020


#include "app.h"
#include "x11_hook.h"
#include "sql_helpers.h"

using namespace std;


#define DRY_RUN false
#define EVENT_CODE_KEY_UP 68
#define EVENT_CODE_KEY_DOWN 67
#define EVENT_CODE_MOUSEBTN_UP 69
#define EVENT_CODE_MOUSEBTN_DOWN 70


class LogKeys {
    sqlite3 *db;
    bool dry_run;
    int num_hooks;
    Display *display;
    map<string, string> config;

    public:
        LogKeys(map<string, string>, bool);
        void hook_device(char*);
        int log_start();
        void log_stop();
        void event_logger(Display*);
};

// Constructor
LogKeys::LogKeys(map<string, string> app_config, bool is_dry_run=false) {
    db = NULL;
    num_hooks = 0;
    config = app_config;
    dry_run = is_dry_run;
    display = get_display(NULL);

    if (display == NULL) 
        cout << "ERROR: X11 Display not found.\n";

    // Open db for logging iff not dry run
    if (!dry_run)
        db = sqlite_get_db(config["APP_KEY_EVENTS_DB_PATH"].c_str());
    else
        cout << "INFO: Logging with is_dry_run = True.";

    sqlite_create_logtables(db);
}

// Inits the x11 global hook for the given device & increments the hook counter
void LogKeys::hook_device(char *device_id) {

    XDeviceInfo *info = device_info(display, device_id, True);

    if(!info) {
        printf("ERROR: Failed to find device '%s'\n", device_id);
    }
    else {
        if(register_events(display, info, device_id)) {
            printf("INFO: Registered device %s - %s\n", device_id, info->name);
            num_hooks++;
        }
        else {
            fprintf(
                stderr, "ERROR: No handled events for device '%s'\n",device_id);
        }
    }
}

// Registers for mouse and keyboard event and starts the logger
int LogKeys::log_start() {
    // Ensure valid display set
    if (display == NULL) {
        printf("ERROR: X11 Display not set.\n");
        return 0;
    }

    // Define helper container
    int max_id_len = max(
        config["DEVICE_ID_MOUSE"].size(), 
        config["DEVICE_ID_KEYBOARD"].size()
    );
    char device_id[max_id_len];

    // Set device event hooks
    num_hooks = 0;
    sprintf(device_id, "%s", config["DEVICE_ID_MOUSE"].c_str());
    hook_device(device_id);
    sprintf(device_id, "%s", config["DEVICE_ID_KEYBOARD"].c_str());
    hook_device(device_id);

    // Start logging iff at least one hook registered
    if (num_hooks) {
        event_logger(display);  // Blocks indefinately
    }
    else {
        cout << "ERROR: No devices registered.";
        return 0;
    }
}

//Stops the logging process
void LogKeys::log_stop() {
    // TODO: Unset hooks and figure out async usage
    XSync(display, False);
    XCloseDisplay(display);
}

// Logs keyboard and mouse button up/down events
void LogKeys::event_logger(Display *dpy) {
    XEvent Event;
    
    setvbuf(stdout, NULL, _IOLBF, 0);

    while(1) {
        XNextEvent(dpy, &Event);

        // Keyboard key up/down events
        if ((Event.type == key_down_type) || (Event.type == key_up_type)) {
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;

            printf("Key %s %d @ %lums\n", (
                Event.type == key_down_type) ? "down" : "up",
                key->keycode,
                key->time
            );
        }
        // Mouse btn updown events
        else if (Event.type == btn_down_type) {
            XDeviceButtonEvent *btn = (XDeviceButtonEvent *) &Event;
            printf("Btn down %d @ %lums\n", btn->button, btn->time);

            printf("Key %s %d @ %lums\n", (
                Event.type == key_down_type) ? "down" : "up",
                btn->button,
                btn->time
            );
        }
    }
}


int main(int argc, char **argv)
{
    map<string, string> config = get_app_config();
    LogKeys logger = LogKeys(config);
    logger.log_start();

    return 0;
}