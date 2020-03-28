// Adapted from https://webhamster.ru/site/page/index/articles/comp/367 by
// Dustin Fast, 2020

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>

#include <X11/Xlib.h>
#include <X11/extensions/XInput.h>

using namespace std;

#define INVALID_EVENT_TYPE -1


// Function declarations
static int register_events(Display *display, XDeviceInfo *info, char *dev_name);
static XDeviceInfo* device_info(Display *display, char *name, Bool only_extended);
static XDeviceInfo* list_available_devices(Display *display);
static int hook_devices(Display *display, char **device_ids, int device_count, void (event_watcher(Display*)));
static int xinput_version(Display *display);
static Display* get_display(_Xconst char* display_name);

// Static global vars
static int key_press_type = INVALID_EVENT_TYPE;
static int key_rel_type = INVALID_EVENT_TYPE;
static int btn_press_type = INVALID_EVENT_TYPE;
static int btn_rel_type = INVALID_EVENT_TYPE;


///////////////////////////////////////////////////////////////////////////////
// Function defs

// Registers for key and/or btn presses on the given device
static int register_events(Display *display, XDeviceInfo *info, char *dev_name) {
    int n = 0;  // number of events registered
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
// event_watcher is your (possibly blocking) event handler implementing XNextEvent.
static int hook_devices(Display *display,
                char **device_ids,
                int device_count,
                void (event_watcher(Display*))) {

    int num_registered = 0;
    
    // Register for each given device's events
    for (int i = 0; i < device_count; i++) {
        char dev_id[3];
        sprintf(dev_id, "%s", device_ids[i]);

        XDeviceInfo *info = device_info(display, dev_id, True);

        if(!info) {
            printf("ERROR: Failed to find device '%s'\n", dev_id);
        }
        else {
            if(register_events(display, info, dev_id)) {
                num_registered++;
                printf("INFO: Registered device %s - %s\n", dev_id, info->name);
            }
            else {
                fprintf(
                    stderr, 
                    "ERROR: No handled events for device '%s'\n",
                    dev_id
                );
            }
        }
    }

    // Call device event handler - probably blocks, depending on implementation
    if (num_registered)
        event_watcher(display);
    
    return 0;
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
