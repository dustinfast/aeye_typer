// Adapted from https://webhamster.ru/site/page/index/articles/comp/367

#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include <ctype.h>
#include <string.h>

#include "x_hook.h"

using namespace std;

int xi_opcode;

#define INVALID_EVENT_TYPE -1

static int motion_type = INVALID_EVENT_TYPE;
static int btn_press_type = INVALID_EVENT_TYPE;
static int btn_rel_type = INVALID_EVENT_TYPE;
static int key_press_type = INVALID_EVENT_TYPE;
static int key_rel_type = INVALID_EVENT_TYPE;
static int proximity_in_type = INVALID_EVENT_TYPE;
static int proximity_out_type = INVALID_EVENT_TYPE;

static int register_events(
    Display *dpy, XDeviceInfo *info, char *dev_name, Bool handle_proximity) {
    int n = 0;    /* number of events registered */
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
        printf("unable to open device '%s'\n", dev_name);
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
                    DeviceButtonPress(device, btn_press_type, events[n]); n++;
                    DeviceButtonRelease(device, btn_rel_type, events[n]); n++;
                    break;

                case ValuatorClass:
                    DeviceMotionNotify(device, motion_type, events[n]); n++;
                    if (handle_proximity) {
                        ProximityIn(device, proximity_in_type, events[n]); n++;
                        ProximityOut(device, proximity_out_type, events[n]); n++;
                    }
                    break;

                default:
                    printf("WARN: Unknown input class.\n");
                break;
            }
        }

        if (XSelectExtensionEvent(dpy, root_win, events, n)) {
            printf("WARN: Failed selecting extended events.\n");
            return 0;
        }
    }
    return n;
}


// Prints events to stdout
static void print_events(Display *dpy) {
    XEvent Event;

    setvbuf(stdout, NULL, _IOLBF, 0);

    while(1) {
        XNextEvent(dpy, &Event);

        if (Event.type == motion_type) {
            int loop;
            XDeviceMotionEvent *motion = (XDeviceMotionEvent *) &Event;

            printf("Motion ");

            for(loop=0; loop<motion->axes_count; loop++)
                printf("a[%d]=%d ", motion->first_axis + loop, motion->axis_data[loop]);
            printf("\n");

        } else if ((Event.type == btn_press_type) || (Event.type == btn_rel_type)) {
            int    loop;
            XDeviceButtonEvent *button = (XDeviceButtonEvent *) &Event;

            printf("Button %s %d ", (Event.type == btn_rel_type) ? "release" : "press  ",
            button->button);

            for(loop=0; loop<button->axes_count; loop++)
                printf("a[%d]=%d ", button->first_axis + loop, button->axis_data[loop]);
            printf("\n");

        } else if ((Event.type == key_press_type) || (Event.type == key_rel_type)) {
            int    loop;
            XDeviceKeyEvent *key = (XDeviceKeyEvent *) &Event;

            printf("Key %s %d ", (Event.type == key_rel_type) ? "release" : "press  ",
            key->keycode);

            for(loop=0; loop<key->axes_count; loop++)
                printf("a[%d]=%d ", key->first_axis + loop, key->axis_data[loop]);
            printf("\n");

        } else if ((Event.type == proximity_out_type) || (Event.type == proximity_in_type)) {
            int    loop;
            XProximityNotifyEvent *prox = (XProximityNotifyEvent *) &Event;

            printf("Proximity %s ", (Event.type == proximity_in_type) ? "in " : "out");

            for(loop=0; loop<prox->axes_count; loop++)
                printf("a[%d]=%d ", prox->first_axis + loop, prox->axis_data[loop]);
            printf("\n");

        }

        else {
            printf("WARN: Unhandled event type '%d'\n", Event.type);
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

    Bool handle_proximity = True;

    info = get_device_info(display, deviceId, True);

    if(!info) {
        printf("unable to find device '%s'\n", deviceId);
        exit(1);
    }

    else {
        if(register_events(display, info, deviceId, handle_proximity)) {
            print_events(display);  // Device hook func
        }
        else {
            fprintf(stderr, "no event registered...\n");
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