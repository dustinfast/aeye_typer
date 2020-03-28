// Adapted from https://webhamster.ru/site/page/index/articles/comp/367

#include <cstdio>
#include <cstdlib>
#include <string.h>
#include <iostream>

#include <X11/Xlib.h>
#include <X11/extensions/XInput.h>

using namespace std;

#define INVALID_EVENT_TYPE -1


static int key_press_type = INVALID_EVENT_TYPE;
static int key_rel_type = INVALID_EVENT_TYPE;
static int btn_press_type = INVALID_EVENT_TYPE;
static int btn_rel_type = INVALID_EVENT_TYPE;


static int register_events(Display *display, XDeviceInfo *info, char *dev_name) {
    int n = 0;    // number of events registered
    XEventClass events[7];
    int i;
    XDevice *device;
    Window root_win;
    unsigned long screen;
    XInputClassInfo *ip;

    screen = DefaultScreen(display);
    root_win = RootWindow(display, screen);
    device = XOpenDevice(display, info->id);

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
                    DeviceButtonPress(device, btn_press_type, events[n]); n++;
                    DeviceButtonRelease(device, btn_rel_type, events[n]); n++;
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

        if (XSelectExtensionEvent(display, root_win, events, n)) {
            printf("WARN: Could not select extended events.\n");
            return 0;
        }
    }
    return n;
}


// Returns the requested device's info
static XDeviceInfo* get_device_info(Display *display, char *name, Bool only_extended)
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


// Starts the hook for the given device on the specified display
int hook_device(Display *display, char *deviceId, void (ev_handler(Display*))) {
    XDeviceInfo *info = get_device_info(display, deviceId, True);

    if(!info) {
        printf("ERROR: Unable to find device '%s'\n", deviceId);
    }
    else {
        if(register_events(display, info, deviceId))
            ev_handler(display);  // Device event handler... Blocks
        else
            fprintf(stderr, "ERROR: No handled events for this device.\n");
    }

    return 0;
}


// Returns the xinput version
static int xinput_version(Display *display) {
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


// Returns the requested display -- pass NULL for default display
static Display* get_display(_Xconst char* display_name)
{
    Display *display;
    int opcode, event, error;

    display = XOpenDisplay(display_name);

    if (display == NULL) {
        printf("ERROR: Failed to connect to X server.\n");
        return NULL;
    }

    if(!XQueryExtension(display, "XInputExtension", &opcode, &event, &error)) {
        printf("X Input ext not available:\nOpcode %d\nEvent %d\nError %d",
            opcode, event, error);
        return NULL;
    }

    if(!xinput_version(display)) {
        printf("%s extension not available.\n", INAME);
        return NULL;
    }

    return display;
}
