#include "osr_render_handler_dispatcher.h"

#if defined(_WIN32)

void OsrRenderHandlerDispatcher::RegisterWindow(int browserId,
                                                  CefRefPtr<OsrWindowWin> window) {
    m_Windows[browserId] = window;
}

void OsrRenderHandlerDispatcher::UnregisterWindow(int browserId) {
    m_Windows.erase(browserId);
}

void OsrRenderHandlerDispatcher::GetViewRect(CefRefPtr<CefBrowser> browser,
                                              CefRect& rect) {
    auto it = m_Windows.find(browser->GetIdentifier());
    if (it != m_Windows.end()) {
        it->second->GetViewRect(browser, rect);
    } else {
        // Fallback: return a default size
        rect.Set(0, 0, 1, 1);
    }
}

void OsrRenderHandlerDispatcher::OnPaint(CefRefPtr<CefBrowser> browser,
                                          PaintElementType type,
                                          const RectList& dirtyRects,
                                          const void* buffer,
                                          int width, int height) {
    auto it = m_Windows.find(browser->GetIdentifier());
    if (it != m_Windows.end()) {
        it->second->OnPaint(browser, type, dirtyRects, buffer, width, height);
    }
}

#endif // _WIN32
