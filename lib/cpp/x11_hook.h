// X11 Device hooking library.
// Adapted from https://webhamster.ru/site/page/index/articles/comp/367 by
// Dustin Fast, 2020

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>

#include <X11/extensions/XInput.h>
#include <X11/Xlib.h>

using namespace std;

#define INVALID_EVENT_TYPE -1


// Function declarations
static int set_device_hook(Display *display, char *device_id, void (event_watcher(Display*)));
static XDeviceInfo* device_info(Display *display, char *name, Bool only_extended);
static int register_events(Display *display, XDeviceInfo *info, char *dev_name);
static XDeviceInfo* list_available_devices(Display *display);
static Display* get_display(_Xconst char* display_name);
static int xinput_version(Display *display);

// Static global vars
static int key_down_type = INVALID_EVENT_TYPE;
static int key_up_type = INVALID_EVENT_TYPE;
static int btn_down_type = INVALID_EVENT_TYPE;
static int btn_up_type = INVALID_EVENT_TYPE;


///////////////////////////////////////////////////////////////////////////////
// Function defs

// Registers for key and/or btn presses on the given device
static int register_events(Display *display, XDeviceInfo *info, char *dev_name) {
    int n, i = 0;
    XEventClass events[7];
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
                    DeviceKeyPress(device, key_down_type, events[n]); n++;
                    DeviceKeyRelease(device, key_up_type, events[n]); n++;
                    break;

                case ButtonClass:
                    DeviceButtonPress(device, btn_down_type, events[n]); n++;
                    DeviceButtonRelease(device, btn_up_type, events[n]); n++;
                    break;

                case ValuatorClass:
                    // Do not handle mouse motion events
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
static XDeviceInfo* device_info(Display *display, char *name, Bool only_extended) {
    XDeviceInfo *devices;
    XDeviceInfo *found;
    int i, num_devices;
    int len = strlen(name);
    Bool is_id = True;
    XID id = (XID)-1;

    devices = XListInputDevices(display, &num_devices);
    found = NULL;

    for(i = 0; i < len; i++) {
        if (!isdigit(name[i])) {
            is_id = False;
            break;
        }
    }

    if (is_id)
        id = atoi(name);

    for(i = 0; i < num_devices; i++) {
        if ((!only_extended || (devices[i].use >= IsXExtensionDevice)) &&
        ((!is_id && strcmp(devices[i].name, name) == 0) ||
        (is_id && devices[i].id == id))) {
            if (found) {
                fprintf(stderr, "ERROR: Multiple devices named '%s'.\n", name);
                return NULL;
            } else {
            found = &devices[i];
            }
        }
    }

    return found;
}


// Prints a list of available devices on the given display to stdout.
// Pass NULL to use the default display.
static XDeviceInfo* list_available_devices(Display *display) {
    XDeviceInfo *devices;
    int num_devices;

    if (display == NULL)
        display = get_display(NULL);

    devices = XListInputDevices(display, &num_devices);

    for(int i = 0; i < num_devices; i++) 
        printf("%lu: %s\n", devices[i].id, devices[i].name);
}


// Starts the hook for the given device on the specified display, where
// event_watcher is your event listener implementing XNextEvent.
static int set_device_hook(Display *display,
                         char *device_id,
                         void (event_watcher(Display*))) {

    XDeviceInfo *info = device_info(display, device_id, True);

    if(!info) {
        printf("ERROR: Failed to find device '%s'\n", device_id);
        return 0;
    }
    else {
        if(register_events(display, info, device_id)) {
            printf("INFO: Registered device %s - %s\n", device_id, info->name);
            return 1;
        }
        else {
            fprintf(
                stderr, "ERROR: No handled events for device '%s'\n",device_id);
            return 0;
        }
    }
}


// Returns the xinput version.
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


// Returns the requested display -- pass NULL for default display.
static Display* get_display(_Xconst char* display_name) {
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
