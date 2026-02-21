declare namespace Pytonium {
  export namespace test_function_binding {
    function testfunc(): any;
  }
  export namespace test_class_methods_binding {
    function test_one(arg1: number): number;
    function test_two(arg1: string, arg2: number, arg3: number): void;
  }
  export namespace window {
    function isMaximized(): boolean;
    function getPosition(): object;
    function getSize(): object;
    function minimize(): void;
    function maximize(): void;
    function close(): void;
    function drag(delta_x: number, delta_y: number): void;
    function setPosition(x: number, y: number): void;
    function setSize(width: number, height: number): void;
    function resize(new_width: number, new_height: number, anchor: number): void;
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