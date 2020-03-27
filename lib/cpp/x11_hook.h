#include <X11/Xlib.h>
#include <X11/extensions/XInput.h>

#ifdef HAVE_XI2
#include <X11/extensions/XInput2.h>
#endif

#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>

extern int xi_opcode; // xinput extension op code

XDeviceInfo* find_device_info(Display *display, char *name, Bool only_extended);

#if HAVE_XI2
XIDeviceInfo* xi2_find_device_info(Display *display, char *name);
int xinput_version(Display* display);
#endif