## Pytonium
### Pytonium is a framework for building python apps, with a GUI based on the web-technologies HTML, CSS and Javascript.

It uses the Chromium Embedded Framework for rendering and execution of javascript.

At the moment the framework has functionality for loading an url and add
Javascript bindings, so a python function can be called from Javascript.
And also Javascript can be executed, on the website, from python.

The package is avaible via pip.

So just type the following in the console to install it.
```
pip install Pytonium
```

To start Pytonium and load a website or local site, you have to first import Pytonium

```python
from Pytonium import Pytonium
```
This imports the Pytonium class.

After we have created an instance of Pytonium, we can initialize Pytonium, with an initial window width and height and
a URL or filepath. 

```python
from Pytonium import Pytonium

pytonium = Pytonium()
pytonium.initialize("C:\TestSite\index.html", 1920, 1080)
```
Now the App starts the browser on the URL or filepath, we provided.

After the initialization, we need to call the method "update_message_loop" on the Pytonium instance. We need to do
this in a regular interval, so the chromium embedded framework can update.
The easiest way to do this, is with a while loop, that runs as long the browser is open.

```python
import time
from Pytonium import Pytonium

pytonium = Pytonium()

pytonium.initialize("C:\TestSite\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

This are the basics to load an HTML file, with CSS and Javascript. 

We have the option to register python functions and methods in Javascript. And make them callable from there.

You can find a complete example and more information in the [GitHub Project Wiki](https://github.com/Maximilian-Winter/pytonium/wiki).




It is tested and developed under Windows 11 and **Python 3.11**, but also has **Linux Support**. And can be used with **Python 3.10**.