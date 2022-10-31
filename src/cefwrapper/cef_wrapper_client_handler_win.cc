#include "cef_wrapper_client_handler.h"

#include <windows.h>
#include <string>

#include "include/cef_browser.h"

void CefWrapperClientHandler::PlatformTitleChange(CefRefPtr<CefBrowser> browser,
                                        const CefString& title) {
  CefWindowHandle hwnd = browser->GetHost()->GetWindowHandle();
  if (hwnd)
    SetWindowText(hwnd, reinterpret_cast<LPCWSTR>(title.c_str()));
}
