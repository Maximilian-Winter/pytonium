#ifndef OSR_RENDER_HANDLER_DISPATCHER_H_
#define OSR_RENDER_HANDLER_DISPATCHER_H_

#if defined(_WIN32)

#include <unordered_map>
#include "include/cef_render_handler.h"
#include "osr_window_win.h"

// Dispatches CefRenderHandler calls to per-browser OsrWindowWin instances.
// CEF's CefClient::GetRenderHandler() returns ONE handler for ALL browsers,
// so this dispatcher routes by browser ID.
class OsrRenderHandlerDispatcher : public CefRenderHandler {
public:
    void RegisterWindow(int browserId, CefRefPtr<OsrWindowWin> window);
    void UnregisterWindow(int browserId);

    // CefRenderHandler overrides — route to per-browser OsrWindowWin
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser, PaintElementType type,
                 const RectList& dirtyRects, const void* buffer,
                 int width, int height) override;

private:
    std::unordered_map<int, CefRefPtr<OsrWindowWin>> m_Windows;

    IMPLEMENT_REFCOUNTING(OsrRenderHandlerDispatcher);
};

#endif // _WIN32
#endif // OSR_RENDER_HANDLER_DISPATCHER_H_
