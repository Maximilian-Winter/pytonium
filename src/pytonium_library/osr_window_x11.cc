#include "osr_window_x11.h"

#if defined(OS_LINUX)

#include <X11/Xatom.h>
#include <X11/extensions/shape.h>
#include <cstring>
#include <iostream>

// MIT-SHM (shared memory) for fast pixel buffer transfer
#include <sys/shm.h>
#include <X11/extensions/XShm.h>

#include "x11_helpers.h"

extern "C" { Display* cef_get_xdisplay(); }

OsrWindowX11::OsrWindowX11(int width, int height, bool click_through, bool show_in_taskbar)
    : m_Display(nullptr),
      m_Window(None),
      m_Width(width),
      m_Height(height),
      m_ClickThrough(click_through),
      m_ShowInTaskbar(show_in_taskbar),
      m_GC(None),
      m_Image(nullptr),
      m_ImageBuffer(nullptr),
      m_UseShm(false),
      m_ShmInfo(nullptr),
      m_Visual(nullptr),
      m_Depth(0),
      m_Colormap(None),
      m_HasArgbVisual(false) {
}

OsrWindowX11::~OsrWindowX11() {
    Destroy();
}

bool OsrWindowX11::FindArgbVisual() {
    if (!m_Display) return false;

    int screen = DefaultScreen(m_Display);
    XVisualInfo tmpl;
    tmpl.screen = screen;
    tmpl.depth = 32;
    tmpl.c_class = TrueColor;

    int count = 0;
    XVisualInfo* visuals = XGetVisualInfo(m_Display,
        VisualScreenMask | VisualDepthMask | VisualClassMask,
        &tmpl, &count);

    if (!visuals || count == 0) {
        if (visuals) XFree(visuals);
        std::cerr << "OsrWindowX11: No 32-bit TrueColor visual found. "
                  << "Transparency requires a running compositor (picom/mutter/kwin)." << std::endl;
        return false;
    }

    // Use the first matching visual
    m_Visual = visuals[0].visual;
    m_Depth = visuals[0].depth;
    XFree(visuals);
    return true;
}

bool OsrWindowX11::InitShm(int width, int height) {
    // Check if MIT-SHM extension is available
    int major, minor;
    Bool pixmaps;
    if (!XShmQueryVersion(m_Display, &major, &minor, &pixmaps)) {
        return false;
    }

    m_ShmInfo = new XShmSegmentInfo();
    memset(m_ShmInfo, 0, sizeof(XShmSegmentInfo));

    m_Image = XShmCreateImage(m_Display, m_Visual, m_Depth, ZPixmap,
                               nullptr, m_ShmInfo, width, height);
    if (!m_Image) {
        delete m_ShmInfo;
        m_ShmInfo = nullptr;
        return false;
    }

    m_ShmInfo->shmid = shmget(IPC_PRIVATE,
                               m_Image->bytes_per_line * m_Image->height,
                               IPC_CREAT | 0600);
    if (m_ShmInfo->shmid < 0) {
        XDestroyImage(m_Image);
        m_Image = nullptr;
        delete m_ShmInfo;
        m_ShmInfo = nullptr;
        return false;
    }

    m_ShmInfo->shmaddr = static_cast<char*>(shmat(m_ShmInfo->shmid, nullptr, 0));
    if (m_ShmInfo->shmaddr == reinterpret_cast<char*>(-1)) {
        shmctl(m_ShmInfo->shmid, IPC_RMID, nullptr);
        XDestroyImage(m_Image);
        m_Image = nullptr;
        delete m_ShmInfo;
        m_ShmInfo = nullptr;
        return false;
    }

    m_Image->data = m_ShmInfo->shmaddr;
    m_ShmInfo->readOnly = False;

    if (!XShmAttach(m_Display, m_ShmInfo)) {
        shmdt(m_ShmInfo->shmaddr);
        shmctl(m_ShmInfo->shmid, IPC_RMID, nullptr);
        XDestroyImage(m_Image);
        m_Image = nullptr;
        delete m_ShmInfo;
        m_ShmInfo = nullptr;
        return false;
    }

    // Mark for removal on detach — automatically cleaned up
    shmctl(m_ShmInfo->shmid, IPC_RMID, nullptr);

    m_ImageBuffer = m_ShmInfo->shmaddr;
    m_UseShm = true;
    return true;
}

void OsrWindowX11::CleanupShm() {
    if (m_ShmInfo) {
        if (m_Display) {
            XShmDetach(m_Display, m_ShmInfo);
        }
        if (m_ShmInfo->shmaddr && m_ShmInfo->shmaddr != reinterpret_cast<char*>(-1)) {
            shmdt(m_ShmInfo->shmaddr);
        }
        delete m_ShmInfo;
        m_ShmInfo = nullptr;
    }
    if (m_Image) {
        // If using SHM, data was m_ShmInfo->shmaddr (already detached).
        // XDestroyImage would try to free it, so set to nullptr.
        if (m_UseShm) {
            m_Image->data = nullptr;
        }
        XDestroyImage(m_Image);
        m_Image = nullptr;
    }
    m_ImageBuffer = nullptr;
    m_UseShm = false;
}

::Window OsrWindowX11::Create() {
    m_Display = cef_get_xdisplay();
    if (!m_Display) {
        std::cerr << "OsrWindowX11: Failed to get X11 display!" << std::endl;
        return None;
    }

    int screen = DefaultScreen(m_Display);
    ::Window root = RootWindow(m_Display, screen);

    // Try to find a 32-bit ARGB visual for transparency
    m_HasArgbVisual = FindArgbVisual();

    if (m_HasArgbVisual) {
        m_Colormap = XCreateColormap(m_Display, root, m_Visual, AllocNone);
    } else {
        // Fallback: use default visual (no transparency)
        m_Visual = DefaultVisual(m_Display, screen);
        m_Depth = DefaultDepth(m_Display, screen);
        m_Colormap = DefaultColormap(m_Display, screen);
        std::cerr << "OsrWindowX11: Using default visual (no per-pixel transparency)." << std::endl;
    }

    XSetWindowAttributes attrs;
    memset(&attrs, 0, sizeof(attrs));
    attrs.colormap = m_Colormap;
    attrs.border_pixel = 0;
    attrs.background_pixel = 0;  // Transparent background
    attrs.override_redirect = False;
    attrs.event_mask = ExposureMask | KeyPressMask | KeyReleaseMask |
                       ButtonPressMask | ButtonReleaseMask |
                       PointerMotionMask | StructureNotifyMask |
                       EnterWindowMask | LeaveWindowMask |
                       FocusChangeMask;

    unsigned long mask = CWColormap | CWBorderPixel | CWBackPixel |
                         CWOverrideRedirect | CWEventMask;

    m_Window = XCreateWindow(m_Display, root,
                              0, 0, m_Width, m_Height,
                              0, m_Depth, InputOutput, m_Visual,
                              mask, &attrs);

    if (m_Window == None) {
        std::cerr << "OsrWindowX11: XCreateWindow failed!" << std::endl;
        return None;
    }

    // Remove window decorations (frameless)
    x11_helpers::SetMotifWmHints(m_Display, m_Window, false);

    // Set window type to normal (so WMs treat it properly)
    Atom windowType = XInternAtom(m_Display, "_NET_WM_WINDOW_TYPE", False);
    Atom windowTypeNormal = XInternAtom(m_Display, "_NET_WM_WINDOW_TYPE_NORMAL", False);
    XChangeProperty(m_Display, m_Window, windowType, XA_ATOM, 32,
                    PropModeReplace, reinterpret_cast<unsigned char*>(&windowTypeNormal), 1);

    // Hide from taskbar if requested
    if (!m_ShowInTaskbar) {
        Atom skipTaskbar = XInternAtom(m_Display, "_NET_WM_STATE_SKIP_TASKBAR", False);
        Atom skipPager = XInternAtom(m_Display, "_NET_WM_STATE_SKIP_PAGER", False);
        Atom wmState = XInternAtom(m_Display, "_NET_WM_STATE", False);
        Atom states[2] = { skipTaskbar, skipPager };
        XChangeProperty(m_Display, m_Window, wmState, XA_ATOM, 32,
                        PropModeReplace, reinterpret_cast<unsigned char*>(states), 2);
    }

    // Set window title
    XStoreName(m_Display, m_Window, "PytoniumOSR");

    // Set WM_DELETE_WINDOW protocol
    Atom wmDelete = XInternAtom(m_Display, "WM_DELETE_WINDOW", False);
    XSetWMProtocols(m_Display, m_Window, &wmDelete, 1);

    // Create GC
    m_GC = XCreateGC(m_Display, m_Window, 0, nullptr);

    // Try MIT-SHM first, fall back to regular XImage
    if (!InitShm(m_Width, m_Height)) {
        std::cout << "OsrWindowX11: MIT-SHM not available, using XPutImage fallback." << std::endl;
        // Create regular XImage
        m_ImageBuffer = static_cast<char*>(malloc(m_Width * m_Height * 4));
        if (m_ImageBuffer) {
            m_Image = XCreateImage(m_Display, m_Visual, m_Depth, ZPixmap, 0,
                                    m_ImageBuffer, m_Width, m_Height, 32, 0);
        }
    }

    // Apply click-through if requested (using XShape extension)
    if (m_ClickThrough) {
        SetClickThrough(true);
    }

    // Show the window
    XMapWindow(m_Display, m_Window);
    XFlush(m_Display);

    return m_Window;
}

void OsrWindowX11::Destroy() {
    if (m_Display && m_GC) {
        XFreeGC(m_Display, m_GC);
        m_GC = None;
    }

    if (m_UseShm) {
        CleanupShm();
    } else {
        if (m_Image) {
            // XDestroyImage frees m_Image->data (which is m_ImageBuffer)
            XDestroyImage(m_Image);
            m_Image = nullptr;
            m_ImageBuffer = nullptr;
        }
    }

    if (m_Display && m_Window != None) {
        XDestroyWindow(m_Display, m_Window);
        m_Window = None;
    }

    if (m_Display && m_HasArgbVisual && m_Colormap != None) {
        XFreeColormap(m_Display, m_Colormap);
        m_Colormap = None;
    }

    // Don't close the display — it's shared with CEF
    m_Display = nullptr;
}

void OsrWindowX11::SetBrowser(CefRefPtr<CefBrowser> browser) {
    m_Browser = browser;
}

void OsrWindowX11::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {
    rect.Set(0, 0, m_Width, m_Height);
}

void OsrWindowX11::OnPaint(CefRefPtr<CefBrowser> browser,
                            PaintElementType type,
                            const RectList& dirtyRects,
                            const void* buffer,
                            int width, int height) {
    if (m_Window == None || !m_Display)
        return;

    // If size changed, recreate the image buffer
    if (width != m_Width || height != m_Height) {
        m_Width = width;
        m_Height = height;

        if (m_UseShm) {
            CleanupShm();
            if (!InitShm(m_Width, m_Height)) {
                // Fallback to non-SHM
                m_ImageBuffer = static_cast<char*>(malloc(m_Width * m_Height * 4));
                if (m_ImageBuffer) {
                    m_Image = XCreateImage(m_Display, m_Visual, m_Depth, ZPixmap, 0,
                                            m_ImageBuffer, m_Width, m_Height, 32, 0);
                }
            }
        } else {
            if (m_Image) {
                XDestroyImage(m_Image);
                m_Image = nullptr;
                m_ImageBuffer = nullptr;
            }
            m_ImageBuffer = static_cast<char*>(malloc(m_Width * m_Height * 4));
            if (m_ImageBuffer) {
                m_Image = XCreateImage(m_Display, m_Visual, m_Depth, ZPixmap, 0,
                                        m_ImageBuffer, m_Width, m_Height, 32, 0);
            }
        }

        // Resize the X11 window to match
        XResizeWindow(m_Display, m_Window, m_Width, m_Height);
    }

    if (!m_Image || !m_ImageBuffer)
        return;

    // Copy CEF's BGRA buffer into our image buffer.
    // CEF BGRA on little-endian x86 matches X11 32-bit ARGB visual byte order:
    // Memory: B G R A  →  X11 reads as 0xAARRGGBB (native ARGB)
    memcpy(m_ImageBuffer, buffer, width * height * 4);

    UpdateWindowImage(buffer, width, height);
}

void OsrWindowX11::UpdateWindowImage(const void* buffer, int width, int height) {
    if (!m_Display || m_Window == None || !m_Image)
        return;

    if (m_UseShm && m_ShmInfo) {
        XShmPutImage(m_Display, m_Window, m_GC, m_Image,
                     0, 0, 0, 0, width, height, False);
    } else {
        XPutImage(m_Display, m_Window, m_GC, m_Image,
                  0, 0, 0, 0, width, height);
    }
    XFlush(m_Display);
}

uint32_t OsrWindowX11::GetCefModifiers(unsigned int x11_state) {
    uint32_t modifiers = 0;
    if (x11_state & ShiftMask)   modifiers |= EVENTFLAG_SHIFT_DOWN;
    if (x11_state & ControlMask) modifiers |= EVENTFLAG_CONTROL_DOWN;
    if (x11_state & Mod1Mask)    modifiers |= EVENTFLAG_ALT_DOWN;
    if (x11_state & Button1Mask) modifiers |= EVENTFLAG_LEFT_MOUSE_BUTTON;
    if (x11_state & Button2Mask) modifiers |= EVENTFLAG_MIDDLE_MOUSE_BUTTON;
    if (x11_state & Button3Mask) modifiers |= EVENTFLAG_RIGHT_MOUSE_BUTTON;
    return modifiers;
}

void OsrWindowX11::ForwardMouseEvent(XEvent& event) {
    if (!m_Browser) return;

    CefMouseEvent cef_event;

    switch (event.type) {
        case MotionNotify:
            cef_event.x = event.xmotion.x;
            cef_event.y = event.xmotion.y;
            cef_event.modifiers = GetCefModifiers(event.xmotion.state);
            m_Browser->GetHost()->SendMouseMoveEvent(cef_event, false);
            break;

        case ButtonPress: {
            cef_event.x = event.xbutton.x;
            cef_event.y = event.xbutton.y;
            cef_event.modifiers = GetCefModifiers(event.xbutton.state);

            CefBrowserHost::MouseButtonType btn = MBT_LEFT;
            if (event.xbutton.button == Button1) btn = MBT_LEFT;
            else if (event.xbutton.button == Button2) btn = MBT_MIDDLE;
            else if (event.xbutton.button == Button3) btn = MBT_RIGHT;
            else if (event.xbutton.button == Button4 || event.xbutton.button == Button5) {
                // Scroll wheel
                int delta = (event.xbutton.button == Button4) ? 120 : -120;
                m_Browser->GetHost()->SendMouseWheelEvent(cef_event, 0, delta);
                return;
            }

            m_Browser->GetHost()->SendMouseClickEvent(cef_event, btn, false, 1);
            break;
        }

        case ButtonRelease: {
            cef_event.x = event.xbutton.x;
            cef_event.y = event.xbutton.y;
            cef_event.modifiers = GetCefModifiers(event.xbutton.state);

            CefBrowserHost::MouseButtonType btn = MBT_LEFT;
            if (event.xbutton.button == Button1) btn = MBT_LEFT;
            else if (event.xbutton.button == Button2) btn = MBT_MIDDLE;
            else if (event.xbutton.button == Button3) btn = MBT_RIGHT;
            else return;  // Ignore scroll button releases

            m_Browser->GetHost()->SendMouseClickEvent(cef_event, btn, true, 1);
            break;
        }

        case LeaveNotify:
            cef_event.x = event.xcrossing.x;
            cef_event.y = event.xcrossing.y;
            cef_event.modifiers = GetCefModifiers(event.xcrossing.state);
            m_Browser->GetHost()->SendMouseMoveEvent(cef_event, true);
            break;
    }
}

void OsrWindowX11::ForwardKeyEvent(XEvent& event) {
    if (!m_Browser) return;

    CefKeyEvent cef_event;
    cef_event.modifiers = GetCefModifiers(event.xkey.state);
    cef_event.is_system_key = false;

    // Get the keysym
    KeySym keysym = XLookupKeysym(&event.xkey, 0);
    cef_event.native_key_code = event.xkey.keycode;

    // Map X11 keysym to a windows virtual key code (CEF uses windows key codes)
    // For most keys, the keysym IS the character code for basic ASCII
    if (keysym >= 0x20 && keysym <= 0x7e) {
        // Printable ASCII
        cef_event.windows_key_code = static_cast<int>(keysym);
    } else {
        // Map common non-printable keys
        switch (keysym) {
            case XK_Return:     cef_event.windows_key_code = 0x0D; break;  // VK_RETURN
            case XK_Escape:     cef_event.windows_key_code = 0x1B; break;  // VK_ESCAPE
            case XK_Tab:        cef_event.windows_key_code = 0x09; break;  // VK_TAB
            case XK_BackSpace:  cef_event.windows_key_code = 0x08; break;  // VK_BACK
            case XK_Delete:     cef_event.windows_key_code = 0x2E; break;  // VK_DELETE
            case XK_Left:       cef_event.windows_key_code = 0x25; break;  // VK_LEFT
            case XK_Right:      cef_event.windows_key_code = 0x27; break;  // VK_RIGHT
            case XK_Up:         cef_event.windows_key_code = 0x26; break;  // VK_UP
            case XK_Down:       cef_event.windows_key_code = 0x28; break;  // VK_DOWN
            case XK_Home:       cef_event.windows_key_code = 0x24; break;  // VK_HOME
            case XK_End:        cef_event.windows_key_code = 0x23; break;  // VK_END
            case XK_Page_Up:    cef_event.windows_key_code = 0x21; break;  // VK_PRIOR
            case XK_Page_Down:  cef_event.windows_key_code = 0x22; break;  // VK_NEXT
            case XK_Insert:     cef_event.windows_key_code = 0x2D; break;  // VK_INSERT
            case XK_Shift_L:
            case XK_Shift_R:    cef_event.windows_key_code = 0x10; break;  // VK_SHIFT
            case XK_Control_L:
            case XK_Control_R:  cef_event.windows_key_code = 0x11; break;  // VK_CONTROL
            case XK_Alt_L:
            case XK_Alt_R:      cef_event.windows_key_code = 0x12; break;  // VK_MENU
            default:
                cef_event.windows_key_code = static_cast<int>(keysym & 0xFFFF);
                break;
        }
    }

    if (event.type == KeyPress) {
        cef_event.type = KEYEVENT_RAWKEYDOWN;
        m_Browser->GetHost()->SendKeyEvent(cef_event);

        // Also send a CHAR event for printable characters
        char buf[8];
        int len = XLookupString(&event.xkey, buf, sizeof(buf), nullptr, nullptr);
        if (len > 0) {
            CefKeyEvent char_event;
            char_event.type = KEYEVENT_CHAR;
            char_event.windows_key_code = static_cast<int>(buf[0]);
            char_event.native_key_code = event.xkey.keycode;
            char_event.modifiers = cef_event.modifiers;
            char_event.is_system_key = false;
            m_Browser->GetHost()->SendKeyEvent(char_event);
        }
    } else if (event.type == KeyRelease) {
        cef_event.type = KEYEVENT_KEYUP;
        m_Browser->GetHost()->SendKeyEvent(cef_event);
    }
}

void OsrWindowX11::ProcessEvents() {
    if (!m_Display || m_Window == None) return;

    while (XPending(m_Display)) {
        XEvent event;
        XNextEvent(m_Display, &event);

        // Filter events for our window
        if (event.xany.window != m_Window)
            continue;

        switch (event.type) {
            case Expose:
                // Repaint on expose
                if (m_Image) {
                    UpdateWindowImage(m_ImageBuffer, m_Width, m_Height);
                }
                break;

            case MotionNotify:
            case ButtonPress:
            case ButtonRelease:
            case LeaveNotify:
                ForwardMouseEvent(event);
                break;

            case KeyPress:
            case KeyRelease:
                ForwardKeyEvent(event);
                break;

            case FocusIn:
                if (m_Browser)
                    m_Browser->GetHost()->SetFocus(true);
                break;

            case FocusOut:
                if (m_Browser)
                    m_Browser->GetHost()->SetFocus(false);
                break;

            case ConfigureNotify: {
                int newWidth = event.xconfigure.width;
                int newHeight = event.xconfigure.height;
                if (newWidth != m_Width || newHeight != m_Height) {
                    m_Width = newWidth;
                    m_Height = newHeight;
                    if (m_Browser)
                        m_Browser->GetHost()->WasResized();
                }
                break;
            }

            case ClientMessage: {
                Atom wmDelete = XInternAtom(m_Display, "WM_DELETE_WINDOW", False);
                if (static_cast<Atom>(event.xclient.data.l[0]) == wmDelete) {
                    if (m_Browser) {
                        m_Browser->GetHost()->CloseBrowser(false);
                    }
                }
                break;
            }

            default:
                break;
        }
    }
}

void OsrWindowX11::SetAlwaysOnTop(bool on_top) {
    if (!m_Display || m_Window == None) return;
    Atom above = XInternAtom(m_Display, "_NET_WM_STATE_ABOVE", False);
    x11_helpers::SendNetWmStateEvent(m_Display, m_Window, on_top ? 1 : 0, above);
}

void OsrWindowX11::SetClickThrough(bool click_through) {
    if (!m_Display || m_Window == None) return;
    m_ClickThrough = click_through;

    if (click_through) {
        // Set empty input shape — all clicks pass through
        XRectangle rect = {0, 0, 0, 0};
        XShapeCombineRectangles(m_Display, m_Window, ShapeInput,
                                 0, 0, &rect, 0, ShapeSet, 0);
    } else {
        // Reset input shape to full window
        XShapeCombineMask(m_Display, m_Window, ShapeInput,
                          0, 0, None, ShapeSet);
    }
    XFlush(m_Display);
}

void OsrWindowX11::SetPosition(int x, int y) {
    if (!m_Display || m_Window == None) return;
    XMoveWindow(m_Display, m_Window, x, y);
    XFlush(m_Display);
}

void OsrWindowX11::SetSize(int width, int height) {
    if (!m_Display || m_Window == None) return;
    m_Width = width;
    m_Height = height;
    XResizeWindow(m_Display, m_Window, width, height);
    XFlush(m_Display);

    if (m_Browser) {
        m_Browser->GetHost()->WasResized();
    }
}

#endif // OS_LINUX
