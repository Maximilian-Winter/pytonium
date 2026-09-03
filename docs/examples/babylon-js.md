---
title: 3D with Babylon.js
---

# 3D with Babylon.js

This example demonstrates how to load and render 3D content in Pytonium using [Babylon.js](https://www.babylonjs.com/), with custom URL schemes for local asset loading and MIME type mapping for binary 3D model files.

!!! tip "Full Source"
    The complete source code is available in the main repository at [`pytonium_examples/pytonium_example_babylon_js`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_babylon_js).

---

## Project Structure

```
babylon-example/
    main.py
    index.html
    js/
        babylon.js              # Babylon.js library
        babylonjs.loaders.js    # Babylon.js GLTF/GLB loader plugin
    data/
        model.glb               # 3D model in glTF Binary format
```

---

## Python Entry Point

```python title="main.py"
import os
import time
from Pytonium import Pytonium

app_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(app_dir, "data") + os.sep

pytonium = Pytonium()

# Scheme for HTML, JS, and CSS files
pytonium.add_custom_scheme("app", app_dir + os.sep)

# Separate scheme for data files (3D models, textures)
pytonium.add_custom_scheme("myapp-data", data_dir)

# Register MIME type for .glb files so CEF serves them correctly
pytonium.add_mime_type_mapping("glb", "model/gltf-binary")

pytonium.initialize("app://index.html", 1280, 720)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

---

## HTML Page

```html title="index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Babylon.js 3D Example</title>
    <style>
        html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
        #renderCanvas { width: 100%; height: 100%; touch-action: none; }
    </style>
</head>
<body>
    <canvas id="renderCanvas"></canvas>

    <script src="app://js/babylon.js"></script>
    <script src="app://js/babylonjs.loaders.js"></script>
    <script>
        const canvas = document.getElementById("renderCanvas");
        const engine = new BABYLON.Engine(canvas, true);

        const createScene = function () {
            const scene = new BABYLON.Scene(engine);
            scene.clearColor = new BABYLON.Color4(0.1, 0.1, 0.15, 1);

            // Camera
            const camera = new BABYLON.ArcRotateCamera(
                "camera", Math.PI / 4, Math.PI / 3, 10,
                BABYLON.Vector3.Zero(), scene
            );
            camera.attachControl(canvas, true);

            // Lighting
            const light = new BABYLON.HemisphericLight(
                "light", new BABYLON.Vector3(0, 1, 0), scene
            );
            light.intensity = 0.8;

            // Load 3D model from the custom data scheme
            BABYLON.SceneLoader.Append(
                "myapp-data://",    // Base URL using custom scheme
                "model.glb",       // File name
                scene,
                function () {
                    console.log("Model loaded successfully");
                    // Frame the camera on the loaded content
                    scene.createDefaultCamera(true, true, true);
                }
            );

            return scene;
        };

        const scene = createScene();

        engine.runRenderLoop(function () {
            scene.render();
        });

        window.addEventListener("resize", function () {
            engine.resize();
        });
    </script>
</body>
</html>
```

---

## How It Works

### Multiple Custom Schemes

This example registers two custom schemes, each mapping to a different directory:

```python
pytonium.add_custom_scheme("app", app_dir + os.sep)
pytonium.add_custom_scheme("myapp-data", data_dir)
```

| Scheme | Maps To | Used For |
|---|---|---|
| `app://` | Project root directory | HTML, JavaScript, CSS |
| `myapp-data://` | `data/` subdirectory | 3D models, textures, binary assets |

This separation keeps your URLs clean. In JavaScript, loading a model is simply:

```javascript
BABYLON.SceneLoader.Append("myapp-data://", "model.glb", scene);
```

### MIME Type Mapping

```python
pytonium.add_mime_type_mapping("glb", "model/gltf-binary")
```

CEF determines how to handle a file based on its MIME type. The `.glb` extension (glTF Binary) is not recognized by default. Without this mapping, CEF would serve the file with a generic or incorrect content type, and Babylon.js would fail to parse it.

!!! warning "Register MIME types before initialize"
    Like custom schemes, MIME type mappings must be registered **before** calling `initialize()`.

Common MIME types you might need for 3D applications:

| Extension | MIME Type |
|---|---|
| `.glb` | `model/gltf-binary` |
| `.gltf` | `model/gltf+json` |
| `.obj` | `text/plain` |
| `.mtl` | `text/plain` |
| `.hdr` | `application/octet-stream` |
| `.env` | `application/octet-stream` |
| `.basis` | `application/octet-stream` |

### Loading Babylon.js from Local Files

The Babylon.js library files are loaded from the `app://` scheme rather than a CDN:

```html
<script src="app://js/babylon.js"></script>
<script src="app://js/babylonjs.loaders.js"></script>
```

This ensures the application works offline and loads instantly. Download the Babylon.js files from the [Babylon.js CDN](https://cdn.babylonjs.com/) or npm and place them in your `js/` directory.

### Render Loop

Babylon.js manages its own render loop via `engine.runRenderLoop()`. This is independent of Pytonium's message loop. Both loops run concurrently -- Pytonium processes native events while Babylon.js renders frames via the Chromium compositor.

---

## Extending This Example

### Python-Controlled 3D Scene

You can bind Python functions to control the 3D scene at runtime:

```python
@returns_value_to_javascript("any")
def get_model_list():
    models = os.listdir(data_dir)
    return [f for f in models if f.endswith(".glb")]

pytonium.bind_function_to_javascript(get_model_list, javascript_object="scene_api")
```

```javascript
const models = await scene_api.get_model_list();
// Dynamically load a model selected by the user
```

### State-Driven Camera

Use state management to control camera parameters from Python:

```python
pytonium.set_state("camera", "target", json.dumps({"x": 0, "y": 2, "z": 0}))
```

```javascript
Pytonium.registerForStateUpdates("camera", "target", function (value) {
    const target = JSON.parse(value);
    camera.setTarget(new BABYLON.Vector3(target.x, target.y, target.z));
});
```

---

## Next Steps

- **[Custom Schemes Guide](../guides/custom-schemes.md)** -- Full reference for scheme registration and MIME types.
- **[Real-Time Line Graph](line-graph.md)** -- Another example of live data flowing from Python to JavaScript.
- **[Simple App](simple-app.md)** -- Start with the basics if you have not already.
