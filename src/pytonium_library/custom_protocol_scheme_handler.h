//
// Created by maxim on 19.10.2022.
//

#ifndef CEF_WRAPPER_CUSTOM_PROTOCOL_SCHEME_HANDLER_H
#define CEF_WRAPPER_CUSTOM_PROTOCOL_SCHEME_HANDLER_H
#include <vector>
#include <unordered_map>
#include "cef_custom_scheme.h"
void RegisterSchemeHandlerFactory(const std::vector<CefCustomScheme>& customSchemes, const std::unordered_map<std::string, std::string>& mimeTypeMap);

#endif // CEF_WRAPPER_CUSTOM_PROTOCOL_SCHEME_HANDLER_H
