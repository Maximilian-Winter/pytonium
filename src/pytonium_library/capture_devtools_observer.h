#ifndef CAPTURE_DEVTOOLS_OBSERVER_H_
#define CAPTURE_DEVTOOLS_OBSERVER_H_

#include <cstddef>
#include <string>
#include <unordered_map>

#include "include/cef_browser.h"
#include "include/cef_devtools_message_observer.h"
#include "include/cef_registration.h"

using screenshot_result_callback_ptr = void (*)(
    void* user_data, int request_id, bool success,
    const void* data, size_t data_size, const char* error);

using screencast_frame_callback_ptr = void (*)(
    void* user_data, const void* data, size_t data_size,
    int width, int height);

using capture_error_callback_ptr = void (*)(void* user_data, const char* error);

// Bridges CEF's asynchronous DevTools Page capture APIs to the public
// Pytonium callbacks. One observer is owned by each PytoniumLibrary/browser.
class CaptureDevToolsObserver : public CefDevToolsMessageObserver {
public:
    explicit CaptureDevToolsObserver(CefRefPtr<CefBrowser> browser);

    bool Attach();
    void Detach();

    int CaptureScreenshot(screenshot_result_callback_ptr callback,
                          void* user_data);
    bool StartScreencast(int quality,
                         screencast_frame_callback_ptr frame_callback,
                         capture_error_callback_ptr error_callback,
                         void* user_data);
    void StopScreencast();
    bool IsScreencasting() const { return m_ScreencastRequested; }

    void OnDevToolsMethodResult(CefRefPtr<CefBrowser> browser,
                                int message_id, bool success,
                                const void* result,
                                size_t result_size) override;
    void OnDevToolsEvent(CefRefPtr<CefBrowser> browser,
                         const CefString& method,
                         const void* params,
                         size_t params_size) override;
    void OnDevToolsAgentDetached(CefRefPtr<CefBrowser> browser) override;

private:
    struct ScreenshotRequest {
        screenshot_result_callback_ptr callback = nullptr;
        void* user_data = nullptr;
    };

    void ReportCaptureError(const std::string& error);
    void FailPendingScreenshots(const std::string& error);

    CefRefPtr<CefBrowser> m_Browser;
    CefRefPtr<CefRegistration> m_Registration;
    std::unordered_map<int, ScreenshotRequest> m_ScreenshotRequests;

    int m_StartScreencastRequestId = 0;
    bool m_ScreencastRequested = false;
    screencast_frame_callback_ptr m_FrameCallback = nullptr;
    capture_error_callback_ptr m_ErrorCallback = nullptr;
    void* m_ScreencastUserData = nullptr;

    IMPLEMENT_REFCOUNTING(CaptureDevToolsObserver);
};

#endif  // CAPTURE_DEVTOOLS_OBSERVER_H_
