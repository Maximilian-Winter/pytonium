#ifndef OSR_WINDOW_X11_H_
#define OSR_WINDOW_X11_H_

#if defined(OS_LINUX)

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XShm.h>
#include "include/cef_render_handler.h"
#include "include/cef_browser.h"

// X11 off-screen rendering window for transparent Pytonium windows on Linux.
// Creates a 32-bit ARGB X11 window (requires a running compositor for transparency).
// Mirrors the OsrWindowWin structure for consistency.
class OsrWindowX11 : public CefRenderHandler {
public:
    OsrWindowX11(int width, int height, bool click_through, bool show_in_taskbar = false);
    ~OsrWindowX11() override;

    // Create the X11 window. Returns the X11 Window handle (or None on failure).
    ::Window Create();

    // Destroy the window and release resources.
    void Destroy();

    ::Window GetWindow() const { return m_Window; }

    // Assign the CEF browser after CreateBrowserSync.
    void SetBrowser(CefRefPtr<CefBrowser> browser);

    // Process pending X11 events (call from UpdateMessageLoop).
    void ProcessEvents();

    // CefRenderHandler overrides
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser, PaintElementType type,
                 const RectList& dirtyRects, const void* buffer,
                 int width, int height) override;

    // Window property setters
    void SetAlwaysOnTop(bool on_top);
    void SetClickThrough(bool click_through);
    void SetPosition(int x, int y);
    void SetSize(int width, int height);

private:
    ::Display* m_Display;
    ::Window m_Window;
    int m_Width;
    int m_Height;
    bool m_ClickThrough;
    bool m_ShowInTaskbar;
    CefRefPtr<CefBrowser> m_Browser;

    // Rendering
    GC m_GC;
    XImage* m_Image;
    char* m_ImageBuffer;
    bool m_UseShm;
    XShmSegmentInfo* m_ShmInfo;

    // 32-bit ARGB visual for transparency
    Visual* m_Visual;
    int m_Depth;
    Colormap m_Colormap;
    bool m_HasArgbVisual;

    // Find a 32-bit TrueColor visual for per-pixel alpha
    bool FindArgbVisual();

    // Update the window contents from the pixel buffer
    void UpdateWindowImage(const void* buffer, int width, int height);

    // Input forwarding helpers
    void ForwardMouseEvent(XEvent& event);
    void ForwardKeyEvent(XEvent& event);
    uint32_t GetCefModifiers(unsigned int x11_state);

    // Initialize/cleanup MIT-SHM
    bool InitShm(int width, int height);
    void CleanupShm();

    IMPLEMENT_REFCOUNTING(OsrWindowX11);
};

#endif // OS_LINUX
#endif // OSR_WINDOW_X11_H_
