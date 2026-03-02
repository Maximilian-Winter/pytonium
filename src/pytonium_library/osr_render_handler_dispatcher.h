#ifndef OSR_RENDER_HANDLER_DISPATCHER_H_
#define OSR_RENDER_HANDLER_DISPATCHER_H_

#include <unordered_map>
#include "include/cef_render_handler.h"

// Dispatches CefRenderHandler calls to per-browser render handler instances.
// CEF's CefClient::GetRenderHandler() returns ONE handler for ALL browsers,
// so this dispatcher routes by browser ID.
//
// The map stores CefRefPtr<CefRenderHandler> — both OsrWindowWin and
// OsrWindowX11 inherit from CefRenderHandler, so this is platform-agnostic.
class OsrRenderHandlerDispatcher : public CefRenderHandler {
public:
    void RegisterWindow(int browserId, CefRefPtr<CefRenderHandler> window);
    void UnregisterWindow(int browserId);

    // CefRenderHandler overrides — route to per-browser handler
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser, PaintElementType type,
                 const RectList& dirtyRects, const void* buffer,
                 int width, int height) override;

private:
    std::unordered_map<int, CefRefPtr<CefRenderHandler>> m_Windows;

    IMPLEMENT_REFCOUNTING(OsrRenderHandlerDispatcher);
};

#endif // OSR_RENDER_HANDLER_DISPATCHER_H_
