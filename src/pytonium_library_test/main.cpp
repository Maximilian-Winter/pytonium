//
// Created by maxim on 11.10.2022.
//

#include "../pytonium_library/pytonium_library.h"
#include "../pytonium_library/cef_value_wrapper.h"
#include <filesystem>
#include <iostream>
#include <thread>


PytoniumLibrary cefSimpleWrapper;

void testfunc42(void *python_callback_object, std::string stateNamespace, std::string key, CefValueWrapper valueWrapper)
{
    std::cout << "I FOUGHT THE LAW AND I WON!" << stateNamespace << " Key:" << key << std::endl;
}

void testfuncReturn(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
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

void context_menu_test(void *python_callback_object, std::string entryNamespace, int command_id)
{
    std::cout << "Context Menu Namespace" << entryNamespace << " Context Menu Id" << command_id << std::endl;
    cefSimpleWrapper.SetCurrentContextMenuNamespace("test");
}
void context_menu_test2(void *python_callback_object, std::string entryNamespace, int command_id)
{
    std::cout << "Context Menu Namespace" << entryNamespace << " Context Menu Id" << command_id << std::endl;
    cefSimpleWrapper.SetShowDebugContextMenu(true);
}
void testfuncNoReturn(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
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
    mapo["Answer"] = wrap_it;
    mapo["Test2"] = wrap_it2;
    mapo["Test3"] = wrap_it3;
    mapo["Test4"] = wrap_it4;

    wrap_it5.SetObject(mapo);
    cefSimpleWrapper.ReturnValueToJavascript(message_id, wrap_it5);
}
int main()
{
    std::vector<std::string> namespacesToSubscribe;

    namespacesToSubscribe.emplace_back("user");
    cefSimpleWrapper.AddJavascriptPythonBinding("testfunc", testfuncReturn, nullptr, "test_function_binding", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("test_one", testfuncReturn, nullptr, "test_class_methods_binding", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("test_two", testfuncNoReturn, nullptr, "test_class_methods_binding", false);
    cefSimpleWrapper.AddStateHandlerPythonBinding(testfunc42, nullptr, namespacesToSubscribe);
    cefSimpleWrapper.AddContextMenuEntry(context_menu_test, nullptr, "app", "TESTUS", 0);
    cefSimpleWrapper.AddContextMenuEntry(context_menu_test2, nullptr, "test", "42", 0);

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

        if(counter == 500)
        {
            CefValueWrapper valueWrapper;
            valueWrapper.SetInt(123);
            cefSimpleWrapper.SetState("user", "age", valueWrapper);
        }
    }

    //cefSimpleWrapper.ShutdownPytonium();
    return 0;
}


