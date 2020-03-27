// Adapted from https://webhamster.ru/site/page/index/articles/comp/367

#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include <ctype.h>
#include <string.h>

#include "x11_hook.h"

using namespace std;

int xi_opcode;

#define INVALID_EVENT_TYPE -1

static int key_press_type = INVALID_EVENT_TYPE;
static int key_rel_type = INVALID_EVENT_TYPE;

static int register_events(Display *dpy, XDeviceInfo *info, char *dev_name) {
    int n = 0;    // number of events registered
    XEventClass events[7];
    int i;
    XDevice *device;
    Window root_win;
    unsigned long screen;
    XInputClassInfo *ip;

    screen = DefaultScreen(dpy);
    root_win = RootWindow(dpy, screen);
    device = XOpenDevice(dpy, info->id);

    if (!device) {
        printf("ERROR: Failed to open device '%s'\n", dev_name);
        return 0;
    }

    if (device->num_classes > 0) {
        for (ip = device->classes, i=0; i<info->num_classes; ip++, i++) {
            switch (ip->input_class) {
                case KeyClass:
                    DeviceKeyPress(device, key_press_type, events[n]); n++;
                    DeviceKeyRelease(device, key_rel_type, events[n]); n++;
                    break;

                case ButtonClass:
                    // Do not handle mouse btn events
                    // DeviceButtonPress(device, btn_press_type, events[n]); n++;
                    // DeviceButtonRelease(device, btn_rel_type, events[n]); n++;
                    break;

                case ValuatorClass:
                    // Do not handle mouse motion events
                    // DeviceMotionNotify(device, motion_type, events[n]); n++;
                    break;

                default:
                    printf("WARN: Encountered unknown input class.\n");
                    break;
            }
        }

        if (XSelectExtensionEvent(dpy, root_win, events, n)) {
            printf("WARN: Could not select extended events.\n");
            return 0;
        }
    }
    return n;
}


// Handles device events
static void handle_events(Display *dpy) {
    XEvent Event;

    setvbuf(stdout, NULL, _IOLBF, 0);

    while(1) {
        XNextEvent(dpy, &Event);

        // Handle key down events
        if (Event.type == key_press_type) {
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;

            printf("Key down %d @ %lums\n", key->keycode, key->time);
        }

        // Handle key up events
        if (Event.type == key_rel_type) {
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;

            printf("Key up %d @ %lums\n", key->keycode, key->time);
        }
    }
}


int xinput_version(Display    *display) {
    XExtensionVersion    *version;
    static int vers = -1;

    if (vers != -1)
        return vers;

    version = XGetExtensionVersion(display, INAME);

    if (version && (version != (XExtensionVersion*) NoSuchExtension)) {
        vers = version->major_version;
        XFree(version);
    }

    return vers;
}

// Returns the requested device
XDeviceInfo* get_device_info(Display *display, char *name, Bool only_extended)
{
    XDeviceInfo *devices;
    XDeviceInfo *found;
    int loop, num_devices;
    int len = strlen(name);
    Bool is_id = True;
    XID id = (XID)-1;

    devices = XListInputDevices(display, &num_devices);
    found = NULL;

    for(loop=0; loop<len; loop++) {
        if (!isdigit(name[loop])) {
            is_id = False;
            break;
        }
    }

    if (is_id) {
        id = atoi(name);
    }

    for(loop=0; loop<num_devices; loop++) {
        if ((!only_extended || (devices[loop].use >= IsXExtensionDevice)) &&
        ((!is_id && strcmp(devices[loop].name, name) == 0) ||
        (is_id && devices[loop].id == id))) {
            if (found) {
                fprintf(stderr,
                        "Warning: Multiple devices named '%s'.\n"
                        "To ensure the correct one is selected, use "
                        "the device ID instead.\n\n", name);
                return NULL;
            } else {
            found = &devices[loop];
            }
        }
    }

    return found;
}


// Starts the hook for the given display/device
int hook_device(Display *display, char *deviceId) {
    XDeviceInfo *info;

    info = get_device_info(display, deviceId, True);

    if(!info) {
        printf("Unable to find device '%s'\n", deviceId);
        exit(1);
    }

    else {
        if(register_events(display, info, deviceId)) {
            handle_events(display);  // Device event handler
        }
        else {
            fprintf(stderr, "No handled events for this device.\n");
            exit(1);
        }
    }

    return 0;
}


int main(int argc, char **argv)
{
    Display *display;
    int event, error;
    char deviceId[16];

    // Get device id from cmd line arg
    if (argc < 2) {
        printf("Missing cmd line arg: DeviceID.\n");
        exit(1);
    }
    sprintf(deviceId, "%s", argv[1]);

    // Init display
    display = XOpenDisplay(NULL);

    if (display == NULL) {
        printf("Unable to connect to X server.\n");
        exit(1);
    }

    if(!XQueryExtension(display, "XInputExtension", &xi_opcode, &event, &error)) {
        printf("X Input extension not available.\n");
        exit(1);
    }

    if(!xinput_version(display)) {
        printf("%s extension not available.\n", INAME);
        exit(1);
    }

    // Start the hook
    hook_device(display, deviceId);

    // Cleanup
    XSync(display, False);
    XCloseDisplay(display);

    return 0;
}