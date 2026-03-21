#include "osr_window_headless.h"
#include "Logging.h"

OsrWindowHeadless::OsrWindowHeadless(int width, int height)
    : m_Width(width),
      m_Height(height),
      m_Buffer(nullptr),
      m_HasFrame(false),
      m_PaintCallback(nullptr),
      m_PaintCallbackUserData(nullptr) {
    if (m_Width > 0 && m_Height > 0) {
        m_Buffer = std::malloc(static_cast<size_t>(m_Width) * m_Height * 4);
        if (m_Buffer) {
            std::memset(m_Buffer, 0, static_cast<size_t>(m_Width) * m_Height * 4);
        }
    }
    //LOG_INFO("OsrWindowHeadless created: %dx%d", m_Width, m_Height);
}

OsrWindowHeadless::~OsrWindowHeadless() {
    if (m_Buffer) {
        std::free(m_Buffer);
        m_Buffer = nullptr;
    }
    //LOG_INFO("OsrWindowHeadless destroyed");
}

void OsrWindowHeadless::SetBrowser(CefRefPtr<CefBrowser> browser) {
    m_Browser = browser;
}

void OsrWindowHeadless::SetPaintCallback(headless_paint_callback_ptr callback,
                                          void* user_data) {
    m_PaintCallback = callback;
    m_PaintCallbackUserData = user_data;
}

void OsrWindowHeadless::SetSize(int width, int height) {
    if (width <= 0 || height <= 0) {
        //LOG_WARNING("OsrWindowHeadless::SetSize: invalid size %dx%d", width, height);
        return;
    }
    if (width == m_Width && height == m_Height) {
        return;  // no change
    }

    m_Width = width;
    m_Height = height;

    // Realloc the buffer
    if (m_Buffer) {
        std::free(m_Buffer);
    }
    m_Buffer = std::malloc(static_cast<size_t>(m_Width) * m_Height * 4);
    if (m_Buffer) {
        std::memset(m_Buffer, 0, static_cast<size_t>(m_Width) * m_Height * 4);
    }
    m_HasFrame = false;

    // Notify CEF that the viewport size changed
    if (m_Browser && m_Browser->GetHost()) {
        m_Browser->GetHost()->WasResized();
    }

    //LOG_INFO("OsrWindowHeadless resized: %dx%d", m_Width, m_Height);
}

void OsrWindowHeadless::GetViewRect(CefRefPtr<CefBrowser> browser,
                                     CefRect& rect) {
    rect = CefRect(0, 0, m_Width, m_Height);
}

void OsrWindowHeadless::OnPaint(CefRefPtr<CefBrowser> browser,
                                 PaintElementType type,
                                 const RectList& dirtyRects,
                                 const void* buffer,
                                 int width, int height) {
    if (type != PET_VIEW) {
        return;  // Ignore popup paint
    }

    // Copy the full frame into our internal buffer.
    // CEF's buffer is BGRA, top-down, width*height*4 bytes.
    const size_t bufferSize = static_cast<size_t>(width) * height * 4;

    // If CEF sends a different size than our viewport (can happen during
    // resize transitions), realloc to match.
    if (width != m_Width || height != m_Height) {
        m_Width = width;
        m_Height = height;
        if (m_Buffer) {
            std::free(m_Buffer);
        }
        m_Buffer = std::malloc(bufferSize);
    }

    if (!m_Buffer) {
        return;
    }

    std::memcpy(m_Buffer, buffer, bufferSize);
    m_HasFrame = true;

    // Fire the user callback if registered.
    // The CEF buffer pointer is still valid here, but we pass our internal
    // copy so the user can safely reference it after the callback returns
    // (until the next OnPaint or SetSize).
    if (m_PaintCallback) {
        m_PaintCallback(m_PaintCallbackUserData, m_Buffer, m_Width, m_Height);
    }
}
