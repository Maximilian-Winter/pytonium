//
// Created by maxim on 19.10.2022.
//
#include "custom_protocol_scheme_handler.h"
#include "file_util.h"
#include "include/cef_parser.h"
#include "include/cef_resource_handler.h"
#include "include/cef_scheme.h"
#include "include/wrapper/cef_helpers.h"
#include <iostream>

class ClientSchemeHandler : public CefResourceHandler {
public:
  ClientSchemeHandler() : offset_(0) {}

  bool ProcessRequest(CefRefPtr<CefRequest> request,
                      CefRefPtr<CefCallback> callback) override {
    CEF_REQUIRE_IO_THREAD();

    bool handled = false;

    std::string url = request->GetURL();

    if (url.starts_with("zen://")) {

      std::string filePath = url.substr(6);
      size_t sep = filePath.find_last_of('.');
      if (sep != std::string::npos) {
        mime_type_ = CefGetMimeType(filePath.substr(sep + 1));
      }

      if (sep == std::string::npos || mime_type_.empty()) {
        handled = true;
        data_ = "Error: Mime type not found!";
        mime_type_ = "text/html";
        status_ = 500;
      } else {
        std::string absoluteFilePath = contentRootFolder + filePath;
        data_ = file_contents_binary(absoluteFilePath);
        handled = true;
        status_ = 200;
      }
    }

    if (handled) {
      // Indicate that the headers are available.
      callback->Continue();
      return true;
    }

    return false;
  }

  void GetResponseHeaders(CefRefPtr<CefResponse> response,
                          int64 &response_length,
                          CefString &redirectUrl) override {
    CEF_REQUIRE_IO_THREAD();

    DCHECK(!data_.empty());

    response->SetMimeType(mime_type_);
    response->SetStatus(status_);
    response->SetHeaderByName("Access-Control-Allow-Origin", "null", true);
    // Set the resulting response length.
    response_length = data_.length();
  }

  void Cancel() override { CEF_REQUIRE_IO_THREAD(); }

  bool ReadResponse(void *data_out, int bytes_to_read, int &bytes_read,
                    CefRefPtr<CefCallback> callback) override {
    CEF_REQUIRE_IO_THREAD();

    bool has_data = false;
    bytes_read = 0;

    if (offset_ < data_.length()) {
      // Copy the next block of data into the buffer.
      int transfer_size =
          std::min(bytes_to_read, static_cast<int>(data_.length() - offset_));
      memcpy(data_out, data_.c_str() + offset_, transfer_size);
      offset_ += transfer_size;

      bytes_read = transfer_size;
      has_data = true;
    }

    return has_data;
  }

private:
  std::string data_;
  std::string mime_type_;
  size_t offset_;
  int status_;
  std::string contentRootFolder = "C:\\ZenDraft\\ZenDraft\\build\\";

  IMPLEMENT_REFCOUNTING(ClientSchemeHandler);
  DISALLOW_COPY_AND_ASSIGN(ClientSchemeHandler);
};

// Implementation of the factory for creating scheme handlers.
class ClientSchemeHandlerFactory : public CefSchemeHandlerFactory {
public:
  ClientSchemeHandlerFactory() {}

  // Return a new scheme handler instance to handle the request.
  CefRefPtr<CefResourceHandler> Create(CefRefPtr<CefBrowser> browser,
                                       CefRefPtr<CefFrame> frame,
                                       const CefString &scheme_name,
                                       CefRefPtr<CefRequest> request) override {
    CEF_REQUIRE_IO_THREAD();
    return new ClientSchemeHandler();
  }

private:
  IMPLEMENT_REFCOUNTING(ClientSchemeHandlerFactory);
  DISALLOW_COPY_AND_ASSIGN(ClientSchemeHandlerFactory);
};

void RegisterSchemeHandlerFactory() {
  CefRegisterSchemeHandlerFactory("zen", "", new ClientSchemeHandlerFactory());
}
