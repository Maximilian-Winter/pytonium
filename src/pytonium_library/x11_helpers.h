#ifndef X11_HELPERS_H_
#define X11_HELPERS_H_

#if defined(OS_LINUX)

#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/Xutil.h>
#include <cstring>
#include <iostream>

namespace x11_helpers {

// _MOTIF_WM_HINTS structure for removing/adding window decorations
struct MotifWmHints {
    unsigned long flags;
    unsigned long functions;
    unsigned long decorations;
    long input_mode;
    unsigned long status;
};

static const unsigned long MWM_HINTS_DECORATIONS = (1L << 1);
static const unsigned long MWM_HINTS_FUNCTIONS   = (1L << 0);

// Send a _NET_WM_STATE client message to the root window.
// action: 0=remove, 1=add, 2=toggle
inline bool SendNetWmStateEvent(Display* display, Window window,
                                 int action, Atom state1, Atom state2 = None) {
    if (!display || window == None) return false;

    XEvent event;
    memset(&event, 0, sizeof(event));
    event.xclient.type = ClientMessage;
    event.xclient.window = window;
    event.xclient.message_type = XInternAtom(display, "_NET_WM_STATE", False);
    event.xclient.format = 32;
    event.xclient.data.l[0] = action;
    event.xclient.data.l[1] = static_cast<long>(state1);
    event.xclient.data.l[2] = static_cast<long>(state2);
    event.xclient.data.l[3] = 1;  // source indication: normal application

    Window root = DefaultRootWindow(display);
    Status status = XSendEvent(display, root, False,
                                SubstructureNotifyMask | SubstructureRedirectMask,
                                &event);
    XFlush(display);
    return status != 0;
}

// Initiate a native window manager drag via _NET_WM_MOVERESIZE.
// direction=8 means "move" (as opposed to resize edges).
inline bool SendNetWmMoveResize(Display* display, Window window,
                                 int root_x, int root_y, int direction) {
    if (!display || window == None) return false;

    // Ungrab pointer first so WM can take over
    XUngrabPointer(display, CurrentTime);

    XEvent event;
    memset(&event, 0, sizeof(event));
    event.xclient.type = ClientMessage;
    event.xclient.window = window;
    event.xclient.message_type = XInternAtom(display, "_NET_WM_MOVERESIZE", False);
    event.xclient.format = 32;
    event.xclient.data.l[0] = root_x;
    event.xclient.data.l[1] = root_y;
    event.xclient.data.l[2] = direction;  // 8 = _NET_WM_MOVERESIZE_MOVE
    event.xclient.data.l[3] = Button1;    // button that initiated the move
    event.xclient.data.l[4] = 1;          // source indication: normal application

    Window root = DefaultRootWindow(display);
    Status status = XSendEvent(display, root, False,
                                SubstructureNotifyMask | SubstructureRedirectMask,
                                &event);
    XFlush(display);
    return status != 0;
}

// Get window position relative to root window.
inline bool GetRootRelativePosition(Display* display, Window window,
                                     int& x_out, int& y_out) {
    if (!display || window == None) return false;

    Window child;
    int x, y;
    if (XTranslateCoordinates(display, window, DefaultRootWindow(display),
                               0, 0, &x, &y, &child)) {
        x_out = x;
        y_out = y;
        return true;
    }
    return false;
}

// Get the work area (usable screen area minus taskbars/panels).
// Falls back to full screen dimensions if _NET_WORKAREA is not available.
inline bool GetWorkArea(Display* display, int& x, int& y, int& width, int& height) {
    if (!display) return false;

    Atom workarea_atom = XInternAtom(display, "_NET_WORKAREA", True);
    if (workarea_atom != None) {
        Atom actual_type;
        int actual_format;
        unsigned long nitems, bytes_after;
        unsigned char* data = nullptr;

        if (XGetWindowProperty(display, DefaultRootWindow(display),
                                workarea_atom, 0, 4, False, XA_CARDINAL,
                                &actual_type, &actual_format, &nitems,
                                &bytes_after, &data) == Success && data && nitems >= 4) {
            long* values = reinterpret_cast<long*>(data);
            x = static_cast<int>(values[0]);
            y = static_cast<int>(values[1]);
            width = static_cast<int>(values[2]);
            height = static_cast<int>(values[3]);
            XFree(data);
            return true;
        }
        if (data) XFree(data);
    }

    // Fallback: use full screen dimensions
    Screen* screen = DefaultScreenOfDisplay(display);
    x = 0;
    y = 0;
    width = WidthOfScreen(screen);
    height = HeightOfScreen(screen);
    return true;
}

// Check if a window has a specific _NET_WM_STATE atom set.
inline bool HasNetWmState(Display* display, Window window, Atom state_atom) {
    if (!display || window == None) return false;

    Atom wm_state = XInternAtom(display, "_NET_WM_STATE", True);
    if (wm_state == None) return false;

    Atom actual_type;
    int actual_format;
    unsigned long nitems, bytes_after;
    unsigned char* data = nullptr;

    if (XGetWindowProperty(display, window, wm_state, 0, (~0L), False,
                            XA_ATOM, &actual_type, &actual_format,
                            &nitems, &bytes_after, &data) != Success || !data) {
        return false;
    }

    Atom* atoms = reinterpret_cast<Atom*>(data);
    bool found = false;
    for (unsigned long i = 0; i < nitems; i++) {
        if (atoms[i] == state_atom) {
            found = true;
            break;
        }
    }
    XFree(data);
    return found;
}

// Set or remove _MOTIF_WM_HINTS to control window decorations.
// decorations=0 removes all decorations (frameless).
inline void SetMotifWmHints(Display* display, Window window, bool decorations) {
    if (!display || window == None) return;

    Atom motif_atom = XInternAtom(display, "_MOTIF_WM_HINTS", False);

    MotifWmHints hints;
    memset(&hints, 0, sizeof(hints));
    hints.flags = MWM_HINTS_DECORATIONS;
    hints.decorations = decorations ? 1 : 0;

    XChangeProperty(display, window, motif_atom, motif_atom, 32,
                    PropModeReplace, reinterpret_cast<unsigned char*>(&hints),
                    sizeof(MotifWmHints) / sizeof(long));
    XFlush(display);
}

}  // namespace x11_helpers

#endif  // OS_LINUX
#endif  // X11_HELPERS_H_
