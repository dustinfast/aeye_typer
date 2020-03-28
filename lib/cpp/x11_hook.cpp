// Handles keyboard and mouse hooking
// Author: Dustin Fast, 2020

#include "x11_hook.h"

using namespace std;


// Handle device events
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
    Display *display;
    char deviceId[16];

    // Get device id from cmd line arg
    if (argc < 2) {
        printf("Missing cmd line arg: DeviceID.\n");
        exit(1);
    }
    sprintf(deviceId, "%s", argv[1]);

    // Get the X11 display
    display =  get_display(NULL);

    if (display == NULL) {
        printf("ERROR: X11 Display not found.\n");
        exit(1);
    }

    // Start the hook... Blocks
    hook_device(display, deviceId, handle_events);

    // Cleanup
    XSync(display, False);
    XCloseDisplay(display);

    return 0;
}