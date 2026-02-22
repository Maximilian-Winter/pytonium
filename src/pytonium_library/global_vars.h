#ifndef GLOBAL_VARS_H
#define GLOBAL_VARS_H

#include <atomic>

inline std::atomic<int> g_BrowserCount{0};
inline bool g_CefInitialized = false;

#endif // GLOBAL_VARS_H
