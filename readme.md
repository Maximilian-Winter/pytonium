This is a framework for building python apps, with a GUI based on the web-technologies HTML, CSS and Javascript.

It uses the Chromium Embedded Framework for rendering and execution of javascript.

At the moment the framework has basic functionality for loading an url and add
Javascript bindings, so a python function can be called from Javascript.
And also Javascript can be executed, on the website, from python.

It is still at an early stage.

I will try to keep the Chromium Embedded Framework updated.

Based on cef version: 106.1.1+g5891c70+chromium-106.0.5249.119

To Build from source, you would have to copy the content of minimal 
distrubition of the Chromium Embedded Framework into the folder called 'cef-binaries'.
