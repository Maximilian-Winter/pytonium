//#include <windows.h>

//#include "include/cef_app.h"
#include "include/cef_command_line.h"
//#include "include/cef_sandbox_win.h"
#include "src/pytonium_library/cef_wrapper_app.h"
#include "src/pytonium_library/javascript_binding.h"


#if defined(CEF_USE_SANDBOX)
// The cef_sandbox.lib static library may not link successfully with all VS
// versions.
#pragma comment(lib, "cef_sandbox.lib")
#endif


int main(int argc, char* argv[]) {
  //CefEnableHighDPISupport();

  void* sandbox_info = nullptr;


  CefMainArgs main_args(argc, argv);
  std::vector<JavascriptBinding>placeHolder;
  std::vector<JavascriptPythonBinding>placeHolderPython;
  CefRefPtr<CefWrapperApp> app(new CefWrapperApp("", placeHolder, placeHolderPython));

  CefExecuteProcess(main_args, app.get(), sandbox_info);

  return 0;
}
