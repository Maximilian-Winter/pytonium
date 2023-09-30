# Pytonium Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
    - [Initialization](#initialization)
    - [Message Loop](#message-loop)
4. [JavaScript and Python Interoperability](#javascript-and-python-interoperability)
    - [Binding Python Functions](#binding-python-functions)
    - [Promises in JavaScript](#promises-in-javascript)
    - [TypeScript Support](#typescript-support)
5. [Managing Application State](#managing-application-state)
    - [JavaScript State Management](#javascript-state-management)
    - [Python State Management](#python-state-management)
6. [Advanced Features](#advanced-features)
    - [Context Menus](#context-menus)
    - [Custom Window Icon](#custom-window-icon)
7. [Platform Support](#platform-support)
8. [Examples](#examples)
9. [Contact](#contact)

---

## Introduction

**Pytonium** is a Python framework designed to build desktop applications with GUIs based on web technologies like HTML, CSS, and JavaScript. It uses the Chromium Embedded Framework for rendering web pages and executing JavaScript code.

### Key Features

- Build UIs using HTML, CSS, and JavaScript.
- Call Python functions and methods from JavaScript and vice versa.
- Handle application state in both JavaScript and Python.
- Execute JavaScript from Python.
- Optional TypeScript support for better IDE integration.

---

## Installation

Pytonium can be installed via pip:

```bash
pip install Pytonium
```

---

## Getting Started

### Initialization

First, import the `Pytonium` class and initialize it. You can set the initial window dimensions and the URL or file path to be loaded.

```python
from Pytonium import Pytonium

pytonium = Pytonium()
pytonium.initialize("C:\TestSite\index.html", 1920, 1080)
```

### Message Loop

After initialization, it's crucial to update the Chromium Embedded Framework message loop regularly. You can do this using a while loop:

```python
import time

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

---

## JavaScript and Python Interoperability

### Binding Python Functions

You can expose Python functions to JavaScript by using decorators and binding methods.

```python
from Pytonium import returns_value_to_javascript

@returns_value_to_javascript("any")
def my_js_binding():
    return {"Answer": 42}

pytonium.bind_function_to_javascript("testfunc", my_js_binding, "test_function_binding")
```

### Promises in JavaScript

After binding, you can call the Python function in JavaScript and handle the returned value using Promises.

```javascript
let myPromise = Pytonium.test_function_binding.testfunc();
myPromise.then((resolvedValue) => {
    console.log("Answer:", resolvedValue.Answer);
});
```

### TypeScript Support

Pytonium allows you to generate TypeScript definitions for better code completion and type checking in IDEs.

```python
pytonium.generate_typescript_definitions("test.d.ts")
```

---

## Managing Application State

### JavaScript State Management

In JavaScript, you can register for state updates and manipulate the state.

```javascript
Pytonium.appState.registerForStateUpdates("ChangeDate", ["app-general"]);
Pytonium.appState.setState("user", "age", 64);
```

### Python State Management

In Python, implement a state handler class with an `update_state` method to receive updates.

```python
class MyStateHandler:
    def update_state(self, namespace, key, value):
        print(f"Updated: {namespace}, {key}, {value}")

pytonium.add_state_handler(MyStateHandler, ["user"])
```

---

## Advanced Features

### Context Menus

You can add custom context menus to your Pytonium application.

```python
def my_context_function():
    print("Context menu clicked")

pytonium.add_context_menu_entry(my_context_function, "My Menu")
```

### Custom Window Icon

Set a custom icon for your application window.

```python
pytonium.set_custom_icon_path("path/to/icon.ico")
```

---

## Platform Support

Pytonium is tested and developed on:

- Windows 11 with Python 3.11
- Linux Support
- Compatible with Python 3.10

---