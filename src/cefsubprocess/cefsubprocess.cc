#include <windows.h>

#include "include/cef_app.h"
#include "include/cef_command_line.h"
#include "include/cef_sandbox_win.h"
#include "src/cefwrapper/cef_wrapper_app.h"
#include "src/cefwrapper/javascript_binding.h"


#if defined(CEF_USE_SANDBOX)
// The cef_sandbox.lib static library may not link successfully with all VS
// versions.
#pragma comment(lib, "cef_sandbox.lib")
#endif


int APIENTRY wWinMain(HINSTANCE hInstance,
                      HINSTANCE hPrevInstance,
                      LPTSTR lpCmdLine,
                      int nCmdShow) {
  UNREFERENCED_PARAMETER(hPrevInstance);
  UNREFERENCED_PARAMETER(lpCmdLine);


  CefEnableHighDPISupport();

  void* sandbox_info = nullptr;


  CefMainArgs main_args(hInstance);
  std::vector<JavascriptBinding>placeHolder;
  std::vector<JavascriptPythonBinding>placeHolderPython;
  CefRefPtr<CefWrapperApp> app(new CefWrapperApp("", placeHolder, placeHolderPython));

  CefExecuteProcess(main_args, app.get(), sandbox_info);

  return 0;
}
