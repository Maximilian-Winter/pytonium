declare namespace Pytonium {
  export namespace test_function_binding {
    function testfunc(): any;
  }
  export namespace test_class_methods_binding {
    function test_one(arg1: number): number;
    function test_two(arg1: string, arg2: number, arg3: number): void;
  }
  export namespace appState {
    function registerForStateUpdates(eventName: string, namespaces: string[], getUpdatesFromJavascript: boolean, getUpdatesFromPytonium: boolean): void;
    function setState(namespace: string, key: string, value: any): void;
    function getState(namespace: string, key: string): any;
    function removeState(namespace: string, key: string): void;
  }
}
interface Window {
  PytoniumReady: boolean;
}
interface WindowEventMap {
  PytoniumReady: Event;
}