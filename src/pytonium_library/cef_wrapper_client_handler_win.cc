#include "cef_wrapper_client_handler.h"

#include <windows.h>
#include <windowsx.h>
#include <string>

#include "include/cef_browser.h"

// Window subclass for handling resize borders in frameless windows
#define RESIZE_BORDER_WIDTH 8

static LRESULT CALLBACK WindowSubclassProc(HWND hWnd, UINT uMsg, WPARAM wParam, 
                                           LPARAM lParam, UINT_PTR uIdSubclass, 
                                           DWORD_PTR dwRefData)
{
    switch (uMsg)
    {
        case WM_NCHITTEST:
        {
            // Get mouse position in screen coordinates
            POINT pt = { GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) };
            RECT rect;
            GetWindowRect(hWnd, &rect);
            
            // Check if window is maximized - no resize when maximized
            if (IsZoomed(hWnd))
            {
                return HTCLIENT;
            }
            
            // Calculate edges
            bool onLeft = pt.x >= rect.left && pt.x < rect.left + RESIZE_BORDER_WIDTH;
            bool onRight = pt.x < rect.right && pt.x >= rect.right - RESIZE_BORDER_WIDTH;
            bool onTop = pt.y >= rect.top && pt.y < rect.top + RESIZE_BORDER_WIDTH;
            bool onBottom = pt.y < rect.bottom && pt.y >= rect.bottom - RESIZE_BORDER_WIDTH;
            
            // Return appropriate resize hit-test values
            if (onTop && onLeft) return HTTOPLEFT;
            if (onTop && onRight) return HTTOPRIGHT;
            if (onBottom && onLeft) return HTBOTTOMLEFT;
            if (onBottom && onRight) return HTBOTTOMRIGHT;
            if (onTop) return HTTOP;
            if (onBottom) return HTBOTTOM;
            if (onLeft) return HTLEFT;
            if (onRight) return HTRIGHT;
            
            // Not on a border - let CEF handle it
            break;
        }
        
        case WM_NCDESTROY:
            // Remove subclass when window is destroyed
            RemoveWindowSubclass(hWnd, WindowSubclassProc, uIdSubclass);
            break;
    }
    
    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

void CefWrapperClientHandler::PlatformTitleChange(CefRefPtr<CefBrowser> browser,
                                        const CefString& title) {
  CefWindowHandle hwnd = browser->GetHost()->GetWindowHandle();

  if (hwnd)
  {
    SetWindowText(hwnd, reinterpret_cast<LPCWSTR>(title.c_str()));
    //HICON hIcon = (HICON)LoadImage(NULL, L"appicon.ico", IMAGE_ICON, 32, 32, LR_LOADFROMFILE);
    //SendMessage(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hIcon);
  }
}

void CefWrapperClientHandler::PlatformSubclassWindow(CefRefPtr<CefBrowser> browser)
{
    CefWindowHandle hwnd = browser->GetHost()->GetWindowHandle();
    if (hwnd)
    {
        // Subclass the window to handle resize borders for frameless windows
        SetWindowSubclass(hwnd, WindowSubclassProc, 0, 0);
    }
}

void CefWrapperClientHandler::PlatformRemoveSubclass(CefRefPtr<CefBrowser> browser)
{
    CefWindowHandle hwnd = browser->GetHost()->GetWindowHandle();
    if (hwnd)
    {
        RemoveWindowSubclass(hwnd, WindowSubclassProc, 0);
    }
}
