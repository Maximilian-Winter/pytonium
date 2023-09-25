//
// Created by maxim on 11.10.2022.
//

#include "../pytonium_library/pytonium_library.h"
#include "../pytonium_library/cef_value_wrapper.h"
#include <filesystem>
#include <iostream>
#include <thread>


PytoniumLibrary cefSimpleWrapper;

void testfunc4(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "I FOUGHT THE LAW AND I WON!" << size << " MSG ID:" << message_id << std::endl;
    CefValueWrapper wrap_it;
    wrap_it.SetBool(false);
    CefValueWrapper wrap_it2;
    wrap_it2.SetBool(true);
    CefValueWrapper wrap_it3;
    wrap_it3.SetInt(42);
    CefValueWrapper wrap_it4;
    wrap_it4.SetDouble(24.24);
    CefValueWrapper wrap_it5;
    std::map<std::string, CefValueWrapper> mapo;
    mapo["Test"] = wrap_it;
    mapo["Test2"] = wrap_it2;
    mapo["Test3"] = wrap_it3;
    mapo["Test4"] = wrap_it4;

    wrap_it5.SetObject(mapo);
    cefSimpleWrapper.ReturnValueToJavascript(message_id, wrap_it5);
}

int main()
{

    cefSimpleWrapper.AddJavascriptPythonBinding("testfunc", testfunc4, nullptr, "test_binding_python_function", true);
    //std::string jsDoc = JavascriptPythonBindingHelper::GenerateJSDoc(cefSimpleWrapper.m_Javascript_Python_Bindings);
    //std::cout << jsDoc << std::endl;
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


