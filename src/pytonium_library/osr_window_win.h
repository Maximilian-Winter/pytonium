#ifndef OSR_WINDOW_WIN_H_
#define OSR_WINDOW_WIN_H_

#if defined(_WIN32)

#include <Windows.h>
#include "include/cef_render_handler.h"
#include "include/cef_browser.h"

class OsrWindowWin : public CefRenderHandler {
public:
    OsrWindowWin(int width, int height, bool click_through);
    ~OsrWindowWin() override;

    // Create the layered Win32 window. Returns the HWND.
    HWND Create(HWND parent = nullptr);

    // Destroy the window and release resources.
    void Destroy();

    HWND GetHwnd() const { return m_Hwnd; }

    // Assign the CEF browser after CreateBrowserSync.
    void SetBrowser(CefRefPtr<CefBrowser> browser);

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
    static const wchar_t* kWindowClass;
    static bool s_ClassRegistered;

    HWND m_Hwnd;
    int m_Width;
    int m_Height;
    bool m_ClickThrough;
    CefRefPtr<CefBrowser> m_Browser;

    // Off-screen rendering DIB
    HDC m_MemDC;
    HBITMAP m_Bitmap;
    void* m_BitmapBits;

    static void RegisterWindowClass();
    static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);

    void UpdateLayeredBitmap(const void* buffer, int width, int height);
    void ForwardMouseEvent(UINT msg, WPARAM wParam, LPARAM lParam);
    void ForwardKeyEvent(UINT msg, WPARAM wParam, LPARAM lParam);

    // Helper to get mouse modifiers from wParam
    static uint32_t GetCefMouseModifiers(WPARAM wParam);
    // Helper to get keyboard modifiers
    static uint32_t GetCefKeyboardModifiers(WPARAM wParam, LPARAM lParam);

    IMPLEMENT_REFCOUNTING(OsrWindowWin);
};

#endif // _WIN32
#endif // OSR_WINDOW_WIN_H_
