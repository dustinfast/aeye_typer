// Handles keyboard and mouse button-press logging
// Author: Dustin Fast, 2020

#include <cstdlib>
#include <iostream>

#include <sqlite3.h>

#include "app.h"
#include "x11_hook.h"

using namespace std;



// Logs keyboard and mouse button up/down events
void handle_events(Display *dpy) {
    XEvent Event;

    setvbuf(stdout, NULL, _IOLBF, 0);

    while(1) {
        XNextEvent(dpy, &Event);

        // Key down events
        if (Event.type == key_press_type) {
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;
            printf("Key down %d @ %lums\n", key->keycode, key->time);
        }

        // Key up events
        else if (Event.type == key_rel_type) {
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;
            printf("Key up %d @ %lums\n", key->keycode, key->time);
        }

        // Mouse btn down events
        else if (Event.type == btn_press_type) {
            XDeviceButtonEvent *button = (XDeviceButtonEvent *) &Event;
            printf("button press %d @ %lums\n", button->button, button->time);
        }

        // Mouse btn up events
        else if (Event.type == btn_rel_type) {
            XDeviceButtonEvent *button = (XDeviceButtonEvent *) &Event;
            printf("button release %d @ %lums\n", button->button, button->time);
        }
    }
}


int main(int argc, char **argv)
{
    int num_hooks = 0;
    map<string, string> config = get_app_config();
    
    // Get default X11 display
    Display *display = get_display(NULL);

    if (display == NULL) {
        printf("ERROR: X11 Display not found.\n");
        exit(1);
    }

    // Register for mouse and keybd events
    int max_id_len = max(
        config["DEVICE_ID_MOUSE"].size(), config["DEVICE_ID_KEYBOARD"].size());
    char device_id[max_id_len];
    
    sprintf(device_id, "%s", config["DEVICE_ID_MOUSE"].c_str());
    num_hooks += hook_device(display, device_id, handle_events);

    sprintf(device_id, "%s", config["DEVICE_ID_KEYBOARD"].c_str());
    num_hooks += hook_device(display, device_id, handle_events);

    // Start logging
    if (num_hooks)
        handle_events(display);  // Blocks indefinately
    else
        cout << "ERROR: No devices registered.";

    // Cleanup
    XSync(display, False);
    XCloseDisplay(display);

    return 0;
}