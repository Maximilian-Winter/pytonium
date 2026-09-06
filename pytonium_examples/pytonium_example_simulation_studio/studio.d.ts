declare namespace Pytonium {
  export namespace studio {
    function command(action: string, args: any): object;
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