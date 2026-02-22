//
// Created by maxim on 19.10.2022.
//
#include "custom_protocol_scheme_handler.h"
#include "file_util.h"
#include "include/cef_parser.h"
#include "include/cef_resource_handler.h"
#include "include/cef_scheme.h"
#include "include/wrapper/cef_helpers.h"
#include "cef_custom_scheme.h"
#include <iostream>
#include <utility>

class ClientSchemeHandler : public CefResourceHandler {
public:
  explicit ClientSchemeHandler(std::string schemeRootFolder, std::string schemeIdent, std::unordered_map<std::string, std::string> mimeTypeMap) :
  offset_(0), status_(0), contentRootFolder(std::move(schemeRootFolder)), schemeIdentifier(std::move(schemeIdent)), m_MimeTypeMap(std::move(mimeTypeMap)){

  }

  bool ProcessRequest(CefRefPtr<CefRequest> request,
                      CefRefPtr<CefCallback> callback) override {
    CEF_REQUIRE_IO_THREAD();

    bool handled = false;

    std::string url = request->GetURL();

    if(url.ends_with("/"))
    {
        url = url.substr(0, url.length() - 1);
    }

    if (url.starts_with(schemeIdentifier + "://")) {

      std::string filePath = url.substr(schemeIdentifier.length() + 3);
      size_t sep = filePath.find_last_of('.');
      if (sep != std::string::npos) {
        mime_type_ = CefGetMimeType(filePath.substr(sep + 1));
      }
      if(mime_type_.empty() && m_MimeTypeMap.contains(filePath.substr(sep + 1)))
      {
          mime_type_ = m_MimeTypeMap[filePath.substr(sep + 1)];
      }
      if (sep == std::string::npos || mime_type_.empty()) {
        handled = true;
        data_ = "Error: Mime type not found!";
        mime_type_ = "text/html";
        status_ = 500;
      } else {
        // Use std::filesystem::path for cross-platform path handling
        std::filesystem::path rootPath = std::filesystem::path(contentRootFolder).lexically_normal();
        std::filesystem::path resolvedPath = (rootPath / filePath).lexically_normal();

        // Path traversal check: resolved path must stay within root
        std::string rootStr = rootPath.string();
        std::string resolvedStr = resolvedPath.string();

        if (resolvedStr.find(rootStr) != 0) {
            // Path escape attempt blocked
            handled = true;
            data_ = "Error: Access denied!";
            mime_type_ = "text/html";
            status_ = 403;
        } else if (std::filesystem::exists(resolvedPath)) {
            // File size limit: 100MB
            constexpr std::uintmax_t MAX_FILE_SIZE = 100 * 1024 * 1024;
            auto fileSize = std::filesystem::file_size(resolvedPath);
            if (fileSize > MAX_FILE_SIZE) {
                handled = true;
                data_ = "Error: File too large!";
                mime_type_ = "text/html";
                status_ = 413;
            } else {
                data_ = file_contents_binary(resolvedPath);
                handled = true;
                status_ = 200;
            }
        } else {
            handled = true;
            data_ = "Error: File not found!";
            mime_type_ = "text/html";
            status_ = 500;
        }
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
                          int64_t &response_length,
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
  std::string contentRootFolder;
    std::string schemeIdentifier;
    std::unordered_map<std::string, std::string> m_MimeTypeMap;
  IMPLEMENT_REFCOUNTING(ClientSchemeHandler);
  DISALLOW_COPY_AND_ASSIGN(ClientSchemeHandler);
};

// Implementation of the factory for creating scheme handlers.
class ClientSchemeHandlerFactory : public CefSchemeHandlerFactory {
public:
  explicit ClientSchemeHandlerFactory(const CefCustomScheme& customScheme, std::unordered_map<std::string, std::string> mimeTypeMap)
  {
      m_SchemeContentRootFolder = customScheme.SchemeRootContent;
      m_MimeTypeMap = std::move(mimeTypeMap);
  }

  // Return a new scheme handler instance to handle the request.
  CefRefPtr<CefResourceHandler> Create(CefRefPtr<CefBrowser> browser,
                                       CefRefPtr<CefFrame> frame,
                                       const CefString &scheme_name,
                                       CefRefPtr<CefRequest> request) override {
    CEF_REQUIRE_IO_THREAD();

    return new ClientSchemeHandler(m_SchemeContentRootFolder, scheme_name, m_MimeTypeMap);
  }

private:
    std::unordered_map<std::string, std::string> m_MimeTypeMap;
    std::string m_SchemeContentRootFolder;
  IMPLEMENT_REFCOUNTING(ClientSchemeHandlerFactory);
  DISALLOW_COPY_AND_ASSIGN(ClientSchemeHandlerFactory);
};

void RegisterSchemeHandlerFactory(const std::vector<CefCustomScheme>& customSchemes, const std::unordered_map<std::string, std::string>& mimeTypeMap) {
    for (const auto& scheme: customSchemes)
    {
        CefRegisterSchemeHandlerFactory(scheme.SchemeIdentifier, "", new ClientSchemeHandlerFactory(scheme, mimeTypeMap));
    }

}
