#include "cef_wrapper_client_handler.h"

#include <windows.h>
#include <string>

#include "include/cef_browser.h"

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
