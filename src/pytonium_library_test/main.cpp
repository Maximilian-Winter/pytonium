//
// Created by maxim on 11.10.2022.
//

#include "../pytonium_library/pytonium_library.h"
#include "../pytonium_library/cef_value_wrapper.h"
#include <filesystem>
#include <iostream>
#include <thread>
#include <iomanip>
#include <chrono>


PytoniumLibrary cefSimpleWrapper;

void testfunc42(void *python_callback_object, std::string stateNamespace, std::string key, CefValueWrapper valueWrapper)
{
    std::cout << "State update received! Namespace: " << stateNamespace << " Key: " << key << std::endl;
}

void testfuncReturn(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "testfuncReturn called! Args count: " << size << " MSG ID: " << message_id << std::endl;
    
    // Only return a value if message_id is valid (>= 0)
    if (message_id >= 0) {
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
}

void context_menu_test(void *python_callback_object, std::string entryNamespace, int command_id)
{
    std::cout << "Context Menu Namespace: " << entryNamespace << " Context Menu Id: " << command_id << std::endl;
    cefSimpleWrapper.SetCurrentContextMenuNamespace("test");
}

void context_menu_test2(void *python_callback_object, std::string entryNamespace, int command_id)
{
    std::cout << "Context Menu Namespace: " << entryNamespace << " Context Menu Id: " << command_id << std::endl;
    cefSimpleWrapper.SetShowDebugContextMenu(true);
}

void testfuncNoReturn(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "testfuncNoReturn called! Args count: " << size << " MSG ID: " << message_id << std::endl;
    
    // This function should NOT return a value since it was registered with returns_value=false
    // message_id will be -1, so we should NOT call ReturnValueToJavascript
    // Just print the arguments for debugging
    for (int i = 0; i < size; i++) {
        std::cout << "  Arg[" << i << "] type: " << args[i].Type << std::endl;
    }
}

// Window control callbacks for the custom title bar
void windowMinimize(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "Window minimize called" << std::endl;
    cefSimpleWrapper.MinimizeWindow();
}

void windowMaximize(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "Window maximize/restore called" << std::endl;
    if (cefSimpleWrapper.IsMaximized()) {
        cefSimpleWrapper.RestoreWindow();
    } else {
        cefSimpleWrapper.MaximizeWindow();
    }
}

void windowClose(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    std::cout << "Window close called" << std::endl;
    cefSimpleWrapper.CloseWindow();
}

void windowDrag(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    if (size >= 2) {
        int deltaX = args[0].GetInt();
        int deltaY = args[1].GetInt();
        cefSimpleWrapper.DragWindow(deltaX, deltaY);
    }
}

// Returns current window position as an object {x, y}
void windowGetPosition(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    int x = 0, y = 0;
    cefSimpleWrapper.GetWindowPosition(x, y);
    
    CefValueWrapper xVal, yVal, result;
    xVal.SetInt(x);
    yVal.SetInt(y);
    
    std::map<std::string, CefValueWrapper> posMap;
    posMap["x"] = xVal;
    posMap["y"] = yVal;
    result.SetObject(posMap);
    
    cefSimpleWrapper.ReturnValueToJavascript(message_id, result);
}

void windowSetPosition(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    if (size >= 2) {
        int x = args[0].GetInt();
        int y = args[1].GetInt();
        cefSimpleWrapper.SetWindowPosition(x, y);
    }
}

void windowIsMaximized(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    CefValueWrapper result;
    result.SetBool(cefSimpleWrapper.IsMaximized());
    cefSimpleWrapper.ReturnValueToJavascript(message_id, result);
}

void windowGetSize(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    int width = 0, height = 0;
    cefSimpleWrapper.GetWindowSize(width, height);
    
    CefValueWrapper wVal, hVal, result;
    wVal.SetInt(width);
    hVal.SetInt(height);
    
    std::map<std::string, CefValueWrapper> sizeMap;
    sizeMap["width"] = wVal;
    sizeMap["height"] = hVal;
    result.SetObject(sizeMap);
    
    cefSimpleWrapper.ReturnValueToJavascript(message_id, result);
}

// Resize with anchor - which corner/edge stays fixed
// anchor: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
void windowResize(void *python_callback_object, int size, CefValueWrapper *args, int message_id)
{
    if (size >= 3) {
        int newWidth = args[0].GetInt();
        int newHeight = args[1].GetInt();
        int anchor = args[2].GetInt(); // 0-3 for corners
        
        cefSimpleWrapper.ResizeWindow(newWidth, newHeight, anchor);
    }
}

int main()
{
    std::vector<std::string> namespacesToSubscribe;

    namespacesToSubscribe.emplace_back("user");
    
    // Enable frameless window - removes Chrome UI (tabs, menu bar, etc.)
    // Set to false if you want the standard window with title bar
    cefSimpleWrapper.SetFramelessWindow(true);
    
    // Register window control bindings for the custom title bar
    cefSimpleWrapper.AddJavascriptPythonBinding("minimize", windowMinimize, nullptr, "window", false);
    cefSimpleWrapper.AddJavascriptPythonBinding("maximize", windowMaximize, nullptr, "window", false);
    cefSimpleWrapper.AddJavascriptPythonBinding("close", windowClose, nullptr, "window", false);
    cefSimpleWrapper.AddJavascriptPythonBinding("drag", windowDrag, nullptr, "window", false);
    cefSimpleWrapper.AddJavascriptPythonBinding("getPosition", windowGetPosition, nullptr, "window", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("setPosition", windowSetPosition, nullptr, "window", false);
    cefSimpleWrapper.AddJavascriptPythonBinding("isMaximized", windowIsMaximized, nullptr, "window", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("getSize", windowGetSize, nullptr, "window", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("resize", windowResize, nullptr, "window", false);
    
    // Register JavaScript bindings
    // testfunc and test_one return values (true), test_two does not (false)
    cefSimpleWrapper.AddJavascriptPythonBinding("testfunc", testfuncReturn, nullptr, "test_function_binding", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("test_one", testfuncReturn, nullptr, "test_class_methods_binding", true);
    cefSimpleWrapper.AddJavascriptPythonBinding("test_two", testfuncNoReturn, nullptr, "test_class_methods_binding", false);
    
    // State handler binding
    cefSimpleWrapper.AddStateHandlerPythonBinding(testfunc42, nullptr, namespacesToSubscribe);
    
    // Context menu bindings
    cefSimpleWrapper.AddContextMenuEntry(context_menu_test, nullptr, "app", "TESTUS", 0);
    cefSimpleWrapper.AddContextMenuEntry(context_menu_test2, nullptr, "test", "42", 0);
    
    // MIME type and custom scheme
    cefSimpleWrapper.AddMimeTypeMapping("glb", "model/gltf-binary");
    cefSimpleWrapper.AddCustomScheme("pytonium-data", (std::filesystem::current_path() / "data").string());

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
        
        // Increment counter so state update happens at counter == 500
        counter++;
        
        // Update the date/time display every loop
        auto now = std::chrono::system_clock::now();
        auto time_t_now = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time_t_now), "%d.%m.%Y, %H:%M:%S");
        std::string date_time = ss.str();
        
        CefValueWrapper dateValue;
        dateValue.SetString(date_time);
        cefSimpleWrapper.SetState("app-general", "date", dateValue);

        // Set user age state when counter reaches 500
        if(counter == 500)
        {
            std::cout << "Setting user age to 123 (counter = 500)" << std::endl;
            CefValueWrapper valueWrapper;
            valueWrapper.SetInt(123);
            cefSimpleWrapper.SetState("user", "age", valueWrapper);
        }
    }

    //cefSimpleWrapper.ShutdownPytonium();
    return 0;
}
