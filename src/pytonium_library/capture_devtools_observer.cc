#include "capture_devtools_observer.h"

#include <algorithm>
#include <string>
#include <utility>
#include <vector>

#include "include/cef_parser.h"
#include "include/cef_values.h"
#include "include/wrapper/cef_helpers.h"

namespace {

std::string ResultToError(const void* result, size_t result_size,
                          const std::string& fallback) {
    if (!result || result_size == 0) {
        return fallback;
    }

    CefRefPtr<CefValue> parsed =
        CefParseJSON(result, result_size, JSON_PARSER_RFC);
    if (parsed && parsed->GetType() == VTYPE_DICTIONARY) {
        CefRefPtr<CefDictionaryValue> dictionary = parsed->GetDictionary();
        if (dictionary && dictionary->HasKey("message")) {
            return dictionary->GetString("message").ToString();
        }
    }

    return std::string(static_cast<const char*>(result), result_size);
}

int ReadDimension(CefRefPtr<CefDictionaryValue> dictionary,
                  const CefString& key) {
    if (!dictionary || !dictionary->HasKey(key)) {
        return 0;
    }
    const CefValueType type = dictionary->GetType(key);
    if (type == VTYPE_INT) {
        return dictionary->GetInt(key);
    }
    if (type == VTYPE_DOUBLE) {
        return static_cast<int>(dictionary->GetDouble(key));
    }
    return 0;
}

}  // namespace

CaptureDevToolsObserver::CaptureDevToolsObserver(
    CefRefPtr<CefBrowser> browser)
    : m_Browser(std::move(browser)) {}

bool CaptureDevToolsObserver::Attach() {
    CEF_REQUIRE_UI_THREAD();
    if (!m_Browser || !m_Browser->GetHost()) {
        return false;
    }
    if (!m_Registration) {
        m_Registration =
            m_Browser->GetHost()->AddDevToolsMessageObserver(this);
    }
    return m_Registration != nullptr;
}

void CaptureDevToolsObserver::Detach() {
    CEF_REQUIRE_UI_THREAD();
    if (m_ScreencastRequested && m_Browser && m_Browser->GetHost()) {
        m_Browser->GetHost()->ExecuteDevToolsMethod(
            0, "Page.stopScreencast", nullptr);
    }

    m_ScreencastRequested = false;
    m_StartScreencastRequestId = 0;
    m_FrameCallback = nullptr;
    m_ErrorCallback = nullptr;
    m_ScreencastUserData = nullptr;
    FailPendingScreenshots("Browser closed before screenshot capture completed");
    m_Registration = nullptr;
    m_Browser = nullptr;
}

int CaptureDevToolsObserver::CaptureScreenshot(
    screenshot_result_callback_ptr callback, void* user_data) {
    CEF_REQUIRE_UI_THREAD();
    if (!callback || !Attach()) {
        return 0;
    }

    CefRefPtr<CefDictionaryValue> params = CefDictionaryValue::Create();
    params->SetString("format", "png");
    params->SetBool("fromSurface", true);
    params->SetBool("captureBeyondViewport", false);

    const int request_id = m_Browser->GetHost()->ExecuteDevToolsMethod(
        0, "Page.captureScreenshot", params);
    if (request_id != 0) {
        m_ScreenshotRequests.emplace(
            request_id, ScreenshotRequest{callback, user_data});
    }
    return request_id;
}

bool CaptureDevToolsObserver::StartScreencast(
    int quality, screencast_frame_callback_ptr frame_callback,
    capture_error_callback_ptr error_callback, void* user_data) {
    CEF_REQUIRE_UI_THREAD();
    if (!frame_callback || m_ScreencastRequested || !Attach()) {
        return false;
    }

    m_FrameCallback = frame_callback;
    m_ErrorCallback = error_callback;
    m_ScreencastUserData = user_data;
    m_ScreencastRequested = true;

    // Page.enable and startScreencast are processed in submission order.
    m_Browser->GetHost()->ExecuteDevToolsMethod(0, "Page.enable", nullptr);

    CefRefPtr<CefDictionaryValue> params = CefDictionaryValue::Create();
    params->SetString("format", "jpeg");
    params->SetInt("quality", std::clamp(quality, 1, 100));
    params->SetInt("everyNthFrame", 1);
    m_StartScreencastRequestId =
        m_Browser->GetHost()->ExecuteDevToolsMethod(
            0, "Page.startScreencast", params);

    if (m_StartScreencastRequestId == 0) {
        m_ScreencastRequested = false;
        m_FrameCallback = nullptr;
        m_ErrorCallback = nullptr;
        m_ScreencastUserData = nullptr;
        return false;
    }
    return true;
}

void CaptureDevToolsObserver::StopScreencast() {
    CEF_REQUIRE_UI_THREAD();
    if (!m_ScreencastRequested) {
        return;
    }
    m_ScreencastRequested = false;
    m_StartScreencastRequestId = 0;
    if (m_Browser && m_Browser->GetHost()) {
        m_Browser->GetHost()->ExecuteDevToolsMethod(
            0, "Page.stopScreencast", nullptr);
    }
    m_FrameCallback = nullptr;
    m_ErrorCallback = nullptr;
    m_ScreencastUserData = nullptr;
}

void CaptureDevToolsObserver::OnDevToolsMethodResult(
    CefRefPtr<CefBrowser> browser, int message_id, bool success,
    const void* result, size_t result_size) {
    CEF_REQUIRE_UI_THREAD();

    auto screenshot = m_ScreenshotRequests.find(message_id);
    if (screenshot != m_ScreenshotRequests.end()) {
        ScreenshotRequest request = screenshot->second;
        m_ScreenshotRequests.erase(screenshot);

        if (!success) {
            const std::string error = ResultToError(
                result, result_size, "Page.captureScreenshot failed");
            request.callback(request.user_data, message_id, false,
                             nullptr, 0, error.c_str());
            return;
        }

        CefRefPtr<CefValue> parsed =
            CefParseJSON(result, result_size, JSON_PARSER_RFC);
        if (!parsed || parsed->GetType() != VTYPE_DICTIONARY) {
            const std::string error = "Invalid Page.captureScreenshot result";
            request.callback(request.user_data, message_id, false,
                             nullptr, 0, error.c_str());
            return;
        }

        CefRefPtr<CefDictionaryValue> dictionary = parsed->GetDictionary();
        CefRefPtr<CefBinaryValue> decoded =
            CefBase64Decode(dictionary->GetString("data"));
        if (!decoded || decoded->GetSize() == 0) {
            const std::string error = "Screenshot result contained no PNG data";
            request.callback(request.user_data, message_id, false,
                             nullptr, 0, error.c_str());
            return;
        }

        std::vector<unsigned char> bytes(decoded->GetSize());
        decoded->GetData(bytes.data(), bytes.size(), 0);
        request.callback(request.user_data, message_id, true,
                         bytes.data(), bytes.size(), nullptr);
        return;
    }

    if (message_id == m_StartScreencastRequestId) {
        m_StartScreencastRequestId = 0;
        if (!success && m_ScreencastRequested) {
            const std::string error = ResultToError(
                result, result_size, "Page.startScreencast failed");
            ReportCaptureError(error);
            m_ScreencastRequested = false;
            m_FrameCallback = nullptr;
            m_ErrorCallback = nullptr;
            m_ScreencastUserData = nullptr;
        }
    }
}

void CaptureDevToolsObserver::OnDevToolsEvent(
    CefRefPtr<CefBrowser> browser, const CefString& method,
    const void* params, size_t params_size) {
    CEF_REQUIRE_UI_THREAD();
    if (method != "Page.screencastFrame") {
        return;
    }

    CefRefPtr<CefValue> parsed =
        CefParseJSON(params, params_size, JSON_PARSER_RFC);
    if (!parsed || parsed->GetType() != VTYPE_DICTIONARY) {
        ReportCaptureError("Invalid Page.screencastFrame event");
        return;
    }

    CefRefPtr<CefDictionaryValue> dictionary = parsed->GetDictionary();
    const int session_id = dictionary->GetInt("sessionId");

    // Chromium will not deliver the next frame until the current one is acked.
    CefRefPtr<CefDictionaryValue> ack = CefDictionaryValue::Create();
    ack->SetInt("sessionId", session_id);
    if (browser && browser->GetHost()) {
        browser->GetHost()->ExecuteDevToolsMethod(
            0, "Page.screencastFrameAck", ack);
    }

    if (!m_ScreencastRequested || !m_FrameCallback) {
        return;
    }

    CefRefPtr<CefBinaryValue> decoded =
        CefBase64Decode(dictionary->GetString("data"));
    if (!decoded || decoded->GetSize() == 0) {
        ReportCaptureError("Screencast frame contained no JPEG data");
        return;
    }

    int width = 0;
    int height = 0;
    if (dictionary->HasKey("metadata")) {
        CefRefPtr<CefDictionaryValue> metadata =
            dictionary->GetDictionary("metadata");
        width = ReadDimension(metadata, "deviceWidth");
        height = ReadDimension(metadata, "deviceHeight");
    }

    std::vector<unsigned char> bytes(decoded->GetSize());
    decoded->GetData(bytes.data(), bytes.size(), 0);
    m_FrameCallback(m_ScreencastUserData, bytes.data(), bytes.size(),
                    width, height);
}

void CaptureDevToolsObserver::OnDevToolsAgentDetached(
    CefRefPtr<CefBrowser> browser) {
    CEF_REQUIRE_UI_THREAD();
    if (m_ScreencastRequested) {
        ReportCaptureError("DevTools agent detached while recording");
    }
    m_ScreencastRequested = false;
    m_StartScreencastRequestId = 0;
    m_FrameCallback = nullptr;
    m_ErrorCallback = nullptr;
    m_ScreencastUserData = nullptr;
    FailPendingScreenshots("DevTools agent detached");
    m_Registration = nullptr;
    m_Browser = nullptr;
}

void CaptureDevToolsObserver::ReportCaptureError(const std::string& error) {
    if (m_ErrorCallback) {
        m_ErrorCallback(m_ScreencastUserData, error.c_str());
    }
}

void CaptureDevToolsObserver::FailPendingScreenshots(
    const std::string& error) {
    auto pending = std::move(m_ScreenshotRequests);
    m_ScreenshotRequests.clear();
    for (const auto& entry : pending) {
        const ScreenshotRequest& request = entry.second;
        if (request.callback) {
            request.callback(request.user_data, entry.first, false,
                             nullptr, 0, error.c_str());
        }
    }
}
