#include "osr_window_win.h"

#if defined(_WIN32)

#include <iostream>

const wchar_t* OsrWindowWin::kWindowClass = L"PytoniumOsrWindow";
bool OsrWindowWin::s_ClassRegistered = false;

OsrWindowWin::OsrWindowWin(int width, int height, bool click_through)
    : m_Hwnd(nullptr),
      m_Width(width),
      m_Height(height),
      m_ClickThrough(click_through),
      m_MemDC(nullptr),
      m_Bitmap(nullptr),
      m_BitmapBits(nullptr) {
}

OsrWindowWin::~OsrWindowWin() {
    Destroy();
}

void OsrWindowWin::RegisterWindowClass() {
    if (s_ClassRegistered)
        return;

    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.cbClsExtra = 0;
    wcex.cbWndExtra = sizeof(LONG_PTR);  // store 'this' pointer
    wcex.hInstance = GetModuleHandle(nullptr);
    wcex.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground = nullptr;  // no background for layered window
    wcex.lpszClassName = kWindowClass;

    if (RegisterClassExW(&wcex)) {
        s_ClassRegistered = true;
    }
}

HWND OsrWindowWin::Create(HWND parent) {
    RegisterWindowClass();

    DWORD ex_style = WS_EX_LAYERED | WS_EX_TOOLWINDOW;
    if (m_ClickThrough) {
        ex_style |= WS_EX_TRANSPARENT;
    }

    m_Hwnd = CreateWindowExW(
        ex_style,
        kWindowClass,
        L"PytoniumOSR",
        WS_POPUP,
        CW_USEDEFAULT, CW_USEDEFAULT,
        m_Width, m_Height,
        parent,
        nullptr,
        GetModuleHandle(nullptr),
        this  // pass 'this' to WM_CREATE
    );

    if (!m_Hwnd) {
        std::cerr << "OsrWindowWin: CreateWindowExW failed! Error: "
                  << GetLastError() << std::endl;
        return nullptr;
    }

    // Create the memory DC and DIB section for compositing
    HDC screenDC = GetDC(nullptr);
    m_MemDC = CreateCompatibleDC(screenDC);
    ReleaseDC(nullptr, screenDC);

    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = m_Width;
    bmi.bmiHeader.biHeight = -m_Height;  // top-down
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    m_Bitmap = CreateDIBSection(m_MemDC, &bmi, DIB_RGB_COLORS,
                                 &m_BitmapBits, nullptr, 0);
    SelectObject(m_MemDC, m_Bitmap);

    ShowWindow(m_Hwnd, SW_SHOWNOACTIVATE);

    return m_Hwnd;
}

void OsrWindowWin::Destroy() {
    if (m_Bitmap) {
        DeleteObject(m_Bitmap);
        m_Bitmap = nullptr;
        m_BitmapBits = nullptr;
    }
    if (m_MemDC) {
        DeleteDC(m_MemDC);
        m_MemDC = nullptr;
    }
    if (m_Hwnd) {
        DestroyWindow(m_Hwnd);
        m_Hwnd = nullptr;
    }
}

void OsrWindowWin::SetBrowser(CefRefPtr<CefBrowser> browser) {
    m_Browser = browser;
}

void OsrWindowWin::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {
    rect.Set(0, 0, m_Width, m_Height);
}

void OsrWindowWin::OnPaint(CefRefPtr<CefBrowser> browser,
                            PaintElementType type,
                            const RectList& dirtyRects,
                            const void* buffer,
                            int width, int height) {
    if (!m_Hwnd || !m_MemDC || !m_BitmapBits)
        return;

    // If the size changed, recreate the DIB
    if (width != m_Width || height != m_Height) {
        m_Width = width;
        m_Height = height;

        if (m_Bitmap) {
            DeleteObject(m_Bitmap);
        }

        BITMAPINFO bmi = {};
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        bmi.bmiHeader.biWidth = m_Width;
        bmi.bmiHeader.biHeight = -m_Height;  // top-down
        bmi.bmiHeader.biPlanes = 1;
        bmi.bmiHeader.biBitCount = 32;
        bmi.bmiHeader.biCompression = BI_RGB;

        m_Bitmap = CreateDIBSection(m_MemDC, &bmi, DIB_RGB_COLORS,
                                     &m_BitmapBits, nullptr, 0);
        SelectObject(m_MemDC, m_Bitmap);
    }

    // Copy CEF's BGRA buffer to our DIB
    memcpy(m_BitmapBits, buffer, width * height * 4);

    UpdateLayeredBitmap(buffer, width, height);
}

void OsrWindowWin::UpdateLayeredBitmap(const void* buffer, int width, int height) {
    if (!m_Hwnd || !m_MemDC)
        return;

    POINT ptSrc = {0, 0};
    SIZE sizeWnd = {width, height};

    BLENDFUNCTION blend = {};
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;

    // Get current window position
    RECT rect;
    GetWindowRect(m_Hwnd, &rect);
    POINT ptDst = {rect.left, rect.top};

    UpdateLayeredWindow(m_Hwnd, nullptr, &ptDst, &sizeWnd,
                        m_MemDC, &ptSrc, 0, &blend, ULW_ALPHA);
}

void OsrWindowWin::SetAlwaysOnTop(bool on_top) {
    if (!m_Hwnd) return;
    SetWindowPos(m_Hwnd,
                 on_top ? HWND_TOPMOST : HWND_NOTOPMOST,
                 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
}

void OsrWindowWin::SetClickThrough(bool click_through) {
    if (!m_Hwnd) return;
    m_ClickThrough = click_through;

    LONG_PTR ex_style = GetWindowLongPtrW(m_Hwnd, GWL_EXSTYLE);
    if (click_through) {
        ex_style |= WS_EX_TRANSPARENT;
    } else {
        ex_style &= ~WS_EX_TRANSPARENT;
    }
    SetWindowLongPtrW(m_Hwnd, GWL_EXSTYLE, ex_style);
}

void OsrWindowWin::SetPosition(int x, int y) {
    if (!m_Hwnd) return;
    SetWindowPos(m_Hwnd, nullptr, x, y, 0, 0,
                 SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

void OsrWindowWin::SetSize(int width, int height) {
    if (!m_Hwnd) return;
    m_Width = width;
    m_Height = height;
    SetWindowPos(m_Hwnd, nullptr, 0, 0, width, height,
                 SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);

    if (m_Browser) {
        m_Browser->GetHost()->WasResized();
    }
}

uint32_t OsrWindowWin::GetCefMouseModifiers(WPARAM wParam) {
    uint32_t modifiers = 0;
    if (wParam & MK_CONTROL) modifiers |= EVENTFLAG_CONTROL_DOWN;
    if (wParam & MK_SHIFT)   modifiers |= EVENTFLAG_SHIFT_DOWN;
    if (wParam & MK_LBUTTON) modifiers |= EVENTFLAG_LEFT_MOUSE_BUTTON;
    if (wParam & MK_MBUTTON) modifiers |= EVENTFLAG_MIDDLE_MOUSE_BUTTON;
    if (wParam & MK_RBUTTON) modifiers |= EVENTFLAG_RIGHT_MOUSE_BUTTON;
    if (GetKeyState(VK_MENU) & 0x8000) modifiers |= EVENTFLAG_ALT_DOWN;
    return modifiers;
}

uint32_t OsrWindowWin::GetCefKeyboardModifiers(WPARAM wParam, LPARAM lParam) {
    uint32_t modifiers = 0;
    if (GetKeyState(VK_SHIFT) & 0x8000)   modifiers |= EVENTFLAG_SHIFT_DOWN;
    if (GetKeyState(VK_CONTROL) & 0x8000) modifiers |= EVENTFLAG_CONTROL_DOWN;
    if (GetKeyState(VK_MENU) & 0x8000)    modifiers |= EVENTFLAG_ALT_DOWN;

    if (HIWORD(lParam) & KF_EXTENDED) modifiers |= EVENTFLAG_IS_KEY_PAD;

    // Distinguish left/right keys
    switch (wParam) {
        case VK_SHIFT:
            if (GetKeyState(VK_LSHIFT) & 0x8000) modifiers |= EVENTFLAG_IS_LEFT;
            if (GetKeyState(VK_RSHIFT) & 0x8000) modifiers |= EVENTFLAG_IS_RIGHT;
            break;
        case VK_CONTROL:
            if (GetKeyState(VK_LCONTROL) & 0x8000) modifiers |= EVENTFLAG_IS_LEFT;
            if (GetKeyState(VK_RCONTROL) & 0x8000) modifiers |= EVENTFLAG_IS_RIGHT;
            break;
        case VK_MENU:
            if (GetKeyState(VK_LMENU) & 0x8000) modifiers |= EVENTFLAG_IS_LEFT;
            if (GetKeyState(VK_RMENU) & 0x8000) modifiers |= EVENTFLAG_IS_RIGHT;
            break;
    }

    return modifiers;
}

void OsrWindowWin::ForwardMouseEvent(UINT msg, WPARAM wParam, LPARAM lParam) {
    if (!m_Browser) return;

    CefMouseEvent event;
    event.x = LOWORD(lParam);
    event.y = HIWORD(lParam);
    event.modifiers = GetCefMouseModifiers(wParam);

    switch (msg) {
        case WM_MOUSEMOVE:
            m_Browser->GetHost()->SendMouseMoveEvent(event, false);
            break;
        case WM_LBUTTONDOWN:
            SetCapture(m_Hwnd);
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_LEFT, false, 1);
            break;
        case WM_LBUTTONUP:
            ReleaseCapture();
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_LEFT, true, 1);
            break;
        case WM_LBUTTONDBLCLK:
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_LEFT, false, 2);
            break;
        case WM_RBUTTONDOWN:
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_RIGHT, false, 1);
            break;
        case WM_RBUTTONUP:
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_RIGHT, true, 1);
            break;
        case WM_MBUTTONDOWN:
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_MIDDLE, false, 1);
            break;
        case WM_MBUTTONUP:
            m_Browser->GetHost()->SendMouseClickEvent(event, MBT_MIDDLE, true, 1);
            break;
        case WM_MOUSEWHEEL: {
            int delta = GET_WHEEL_DELTA_WPARAM(wParam);
            // Convert screen coords to client coords for wheel
            POINT pt = {LOWORD(lParam), HIWORD(lParam)};
            ScreenToClient(m_Hwnd, &pt);
            event.x = pt.x;
            event.y = pt.y;
            m_Browser->GetHost()->SendMouseWheelEvent(event, 0, delta);
            break;
        }
        case WM_MOUSELEAVE:
            m_Browser->GetHost()->SendMouseMoveEvent(event, true);
            break;
    }
}

void OsrWindowWin::ForwardKeyEvent(UINT msg, WPARAM wParam, LPARAM lParam) {
    if (!m_Browser) return;

    CefKeyEvent event;
    event.windows_key_code = static_cast<int>(wParam);
    event.native_key_code = static_cast<int>(lParam);
    event.modifiers = GetCefKeyboardModifiers(wParam, lParam);
    event.is_system_key = (msg == WM_SYSCHAR || msg == WM_SYSKEYDOWN || msg == WM_SYSKEYUP);

    switch (msg) {
        case WM_KEYDOWN:
        case WM_SYSKEYDOWN:
            event.type = KEYEVENT_RAWKEYDOWN;
            break;
        case WM_KEYUP:
        case WM_SYSKEYUP:
            event.type = KEYEVENT_KEYUP;
            break;
        case WM_CHAR:
        case WM_SYSCHAR:
            event.type = KEYEVENT_CHAR;
            break;
        default:
            return;
    }

    m_Browser->GetHost()->SendKeyEvent(event);
}

LRESULT CALLBACK OsrWindowWin::WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    OsrWindowWin* self = nullptr;

    if (msg == WM_NCCREATE) {
        auto* cs = reinterpret_cast<CREATESTRUCTW*>(lParam);
        self = static_cast<OsrWindowWin*>(cs->lpCreateParams);
        SetWindowLongPtrW(hwnd, 0, reinterpret_cast<LONG_PTR>(self));
    } else {
        self = reinterpret_cast<OsrWindowWin*>(GetWindowLongPtrW(hwnd, 0));
    }

    if (self) {
        switch (msg) {
            case WM_MOUSEMOVE:
            case WM_LBUTTONDOWN:
            case WM_LBUTTONUP:
            case WM_LBUTTONDBLCLK:
            case WM_RBUTTONDOWN:
            case WM_RBUTTONUP:
            case WM_MBUTTONDOWN:
            case WM_MBUTTONUP:
            case WM_MOUSEWHEEL:
            case WM_MOUSELEAVE:
                self->ForwardMouseEvent(msg, wParam, lParam);
                return 0;

            case WM_KEYDOWN:
            case WM_KEYUP:
            case WM_CHAR:
            case WM_SYSKEYDOWN:
            case WM_SYSKEYUP:
            case WM_SYSCHAR:
                self->ForwardKeyEvent(msg, wParam, lParam);
                return 0;

            case WM_SETFOCUS:
                if (self->m_Browser)
                    self->m_Browser->GetHost()->SetFocus(true);
                return 0;

            case WM_KILLFOCUS:
                if (self->m_Browser)
                    self->m_Browser->GetHost()->SetFocus(false);
                return 0;

            case WM_SIZE: {
                int w = LOWORD(lParam);
                int h = HIWORD(lParam);
                if (w > 0 && h > 0) {
                    self->m_Width = w;
                    self->m_Height = h;
                    if (self->m_Browser)
                        self->m_Browser->GetHost()->WasResized();
                }
                return 0;
            }

            case WM_ERASEBKGND:
                return 1;  // no background erase needed

            case WM_CLOSE:
                if (self->m_Browser) {
                    self->m_Browser->GetHost()->CloseBrowser(false);
                    return 0;  // let CEF handle it
                }
                break;

            case WM_DESTROY:
                self->m_Hwnd = nullptr;
                return 0;
        }
    }

    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

#endif // _WIN32
