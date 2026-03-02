#ifndef OSR_WINDOW_HEADLESS_H_
#define OSR_WINDOW_HEADLESS_H_

#include <cstdlib>
#include <cstring>
#include "include/cef_render_handler.h"
#include "include/cef_browser.h"

// Callback type for paint notifications.
// user_data: opaque pointer passed through from SetPaintCallback
// buffer: BGRA pixel data, width*height*4 bytes, valid ONLY during callback
// width, height: dimensions in pixels
using headless_paint_callback_ptr = void (*)(void* user_data,
                                             const void* buffer,
                                             int width, int height);

// Platform-agnostic headless off-screen rendering handler.
// No OS window is created. CEF renders to an internal buffer which is
// delivered via a user-registered callback and/or polled via GetBuffer().
//
// This enables embedding Pytonium's rendered output into external renderers
// (e.g. Vulkan, OpenGL, DirectX) as a texture overlay.
class OsrWindowHeadless : public CefRenderHandler {
public:
    OsrWindowHeadless(int width, int height);
    ~OsrWindowHeadless() override;

    // Assign the CEF browser after CreateBrowserSync.
    void SetBrowser(CefRefPtr<CefBrowser> browser);

    // Register a paint callback. Called on CEF's render thread each frame.
    // The buffer pointer is valid ONLY for the duration of the callback.
    void SetPaintCallback(headless_paint_callback_ptr callback, void* user_data);

    // Resize the virtual viewport. Reallocs the internal buffer and
    // notifies CEF via WasResized().
    void SetSize(int width, int height);

    // Poll the last rendered frame (zero-copy read).
    // Returns nullptr if no frame has been rendered yet.
    // The returned pointer is valid until the next OnPaint or SetSize call.
    const void* GetBuffer() const { return m_Buffer; }
    int GetWidth() const { return m_Width; }
    int GetHeight() const { return m_Height; }
    bool HasFrame() const { return m_HasFrame; }

    // CefRenderHandler overrides
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser, PaintElementType type,
                 const RectList& dirtyRects, const void* buffer,
                 int width, int height) override;

private:
    int m_Width;
    int m_Height;
    void* m_Buffer;          // malloc'd BGRA buffer, width*height*4 bytes
    bool m_HasFrame;         // true after first OnPaint
    CefRefPtr<CefBrowser> m_Browser;

    // User callback
    headless_paint_callback_ptr m_PaintCallback;
    void* m_PaintCallbackUserData;

    IMPLEMENT_REFCOUNTING(OsrWindowHeadless);
};

#endif // OSR_WINDOW_HEADLESS_H_
