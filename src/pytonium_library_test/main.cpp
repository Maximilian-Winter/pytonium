//
// Created by maxim on 11.10.2022.
//

#include "../pytonium_library/pytonium_library.h"
#include <filesystem>
#include <iostream>
#include <thread>

void testfunc(int size, CefValueWrapper* args)
{
  std::cout << "I FOUGHT THE LAW AND I WON!"<< size << std::endl;
}

void testfunc2(int size, CefValueWrapper* args)
{
    std::cout << "I FOUGHT THE LAW AND I WON!" << size << std::endl;
}

void testfunc3(int size, CefValueWrapper* args)
{
    std::cout << "I FOUGHT THE LAW AND I WON!" << size << std::endl;
}
PytoniumLibrary cefSimpleWrapper;
void testfunc4(void* python_callback_object, int size, CefValueWrapper* args, int message_id)
{
  std::cout << "I FOUGHT THE LAW AND I WON!"<< size << " MSG ID:" << message_id<< std::endl;
  CefValueWrapper wrap_it;
    wrap_it.SetBool(false);
  cefSimpleWrapper.ReturnValueToJavascript(message_id, wrap_it);
}

int main()
{

  cefSimpleWrapper.AddJavascriptPythonBinding("testfunc", testfunc4, nullptr, "test_binding_python_function");
  cefSimpleWrapper.AddJavascriptBinding("TestOne", testfunc, "test_binding_python_object_methods");
  cefSimpleWrapper.AddJavascriptBinding("TestTwo", testfunc2, "test_binding_python_object_methods");
  cefSimpleWrapper.AddJavascriptBinding("TestThree", testfunc3, "test_binding_python_object_methods");
  std::filesystem::path entryPoint = std::filesystem::current_path() / "index.html";
  cefSimpleWrapper.SetCustomIconPath("radioactive.ico");
  cefSimpleWrapper.InitPytonium("file://" + entryPoint.string(), 1920, 1080);

  long long counter = 0;
  while (cefSimpleWrapper.IsRunning())
  {
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    cefSimpleWrapper.UpdateMessageLoop();
    std::stringstream ss;
    ss << "CallFromPythonExample.setTicker(" << counter++ << ")";
    cefSimpleWrapper.ExecuteJavascript(ss.str());
  }

  //cefSimpleWrapper.ShutdownPytonium();
  return 0;
}


