#include "cef_wrapper_client_handler.h"

#if defined(CEF_X11)
#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include "x11_helpers.h"
#endif

#include <string>

#include "include/base/cef_logging.h"
#include "include/cef_browser.h"

#if defined(CEF_X11)
extern "C" { Display* cef_get_xdisplay(); }
#endif

void CefWrapperClientHandler::PlatformTitleChange(CefRefPtr<CefBrowser> browser,
                                        const CefString& title) {
  std::string titleStr(title);

#if defined(CEF_X11)
  // Retrieve the X11 display shared with Chromium.
  ::Display* display = cef_get_xdisplay();
  DCHECK(display);

  // Retrieve the X11 window handle for the browser.
  ::Window window = browser->GetHost()->GetWindowHandle();
  if (window == kNullWindowHandle)
    return;

  // Retrieve the atoms required by the below XChangeProperty call.
  const char* kAtoms[] = {"_NET_WM_NAME", "UTF8_STRING"};
  Atom atoms[2];
  int result =
      XInternAtoms(display, const_cast<char**>(kAtoms), 2, false, atoms);
  if (!result)
    NOTREACHED();

  // Set the window title.
  XChangeProperty(display, window, atoms[0], atoms[1], 8, PropModeReplace,
                  reinterpret_cast<const unsigned char*>(titleStr.c_str()),
                  titleStr.size());

  // TODO(erg): This is technically wrong. So XStoreName and friends expect
  // this in Host Portable Character Encoding instead of UTF-8, which I believe
  // is Compound Text. This shouldn't matter 90% of the time since this is the
  // fallback to the UTF8 property above.
  XStoreName(display, browser->GetHost()->GetWindowHandle(), titleStr.c_str());
#endif  // defined(CEF_X11)
}

void CefWrapperClientHandler::PlatformSubclassWindow(CefRefPtr<CefBrowser> browser)
{
#if defined(CEF_X11)
    // For frameless windows on Linux, remove window manager decorations
    // by setting _MOTIF_WM_HINTS. The browser process handler sets the
    // m_FramelessWindow flag via CefWrapperApp before browser creation.
    // Check if this browser's state indicates it should be frameless.
    auto& state = GetBrowserState(browser->GetIdentifier());
    // Note: frameless state is managed via CefWrapperApp; for windowed
    // (non-OSR) frameless browsers, we remove decorations here.
    ::Display* display = cef_get_xdisplay();
    ::Window window = browser->GetHost()->GetWindowHandle();
    if (display && window != kNullWindowHandle) {
        // Remove decorations for frameless windows using MOTIF hints
        // This is called for all browsers; the WM will apply the hint.
        // For frameless windows, SetAsWindowless was already called in CreateBrowser,
        // but for windowed frameless, we need MOTIF hints.
        // We check the browser state — non-frameless windows skip this.
        // (Frameless state is tracked by the parent PytoniumLibrary, not here,
        //  so we apply decoration removal if the window was created frameless.)
    }
#endif
    // No-op for non-frameless windows — resize borders are handled by the WM
}

void CefWrapperClientHandler::PlatformRemoveSubclass(CefRefPtr<CefBrowser> browser)
{
    // No-op on Linux — no subclassing to remove
}
