//
// Created by maxim on 11.10.2022.
//

#include "../cefwrapper/library.h"
#include <iostream>
#include <filesystem>

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

void testfunc4(void* python_callback_object, int size, CefValueWrapper* args)
{
  std::cout << "I FOUGHT THE LAW AND I WON!"<< size << std::endl;
}

int main()
{
  CefWrapper cefSimpleWrapper;
  cefSimpleWrapper.AddJavascriptPythonBinding("testfunc", testfunc4, nullptr, "test_binding_python_function");
  cefSimpleWrapper.AddJavascriptBinding("TestOne", testfunc, "test_binding_python_object_methods");
  cefSimpleWrapper.AddJavascriptBinding("TestTwo", testfunc2, "test_binding_python_object_methods");
  cefSimpleWrapper.AddJavascriptBinding("TestThree", testfunc3, "test_binding_python_object_methods");
  std::string currentPath = std::filesystem::current_path().string();
  cefSimpleWrapper.SetCustomIconPath("radioactive.ico");
  cefSimpleWrapper.InitCefSimple(currentPath + R"(\index.html)", 1920, 1080);

  long long counter = 0;
  while (cefSimpleWrapper.IsRunning())
  {
	  Sleep(10);
	  cefSimpleWrapper.DoCefMessageLoopWork();
          std::stringstream ss;
          ss << "window.state.setTicker(" << counter++ << ")";
          cefSimpleWrapper.ExecuteJavascript(ss.str());
  }

  //cefSimpleWrapper.ShutdownCefSimple();
  return 0;
}


