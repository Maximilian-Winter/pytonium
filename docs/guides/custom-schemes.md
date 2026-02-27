# Custom Schemes & MIME Types

Pytonium supports custom URL schemes that map to local directories on disk.
This lets you serve your HTML, CSS, JavaScript, images, and other assets through
clean URLs like `myapp://index.html` instead of raw `file:///` paths.

---

## Registering a Custom Scheme

Use `add_custom_scheme()` to map a scheme identifier to a folder on disk.

```python
from Pytonium import Pytonium

p = Pytonium()
p.add_custom_scheme("myapp", "./web/")
p.initialize("myapp://index.html", 800, 600)
```

| Parameter                     | Type  | Description                                              |
|-------------------------------|-------|----------------------------------------------------------|
| `scheme_identifier`           | `str` | The scheme name (e.g. `"myapp"` for `myapp://` URLs).   |
| `scheme_content_root_folder`  | `str` | Absolute or relative path to the content root folder.    |

After registration, any URL using the scheme resolves to a file relative to the
root folder:

| URL                          | File on Disk              |
|------------------------------|---------------------------|
| `myapp://index.html`         | `./web/index.html`        |
| `myapp://css/style.css`      | `./web/css/style.css`     |
| `myapp://js/app.js`          | `./web/js/app.js`         |
| `myapp://images/logo.png`    | `./web/images/logo.png`   |

!!! warning "Call before initialize"
    `add_custom_scheme()` **must** be called before `initialize()`.  Custom
    schemes are registered with CEF at startup and cannot be added later.

---

## Using Custom Schemes in HTML

Once registered, you can reference scheme URLs in your HTML just like any other
URL.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="myapp://css/style.css">
    <script src="myapp://js/app.js" defer></script>
    <title>My App</title>
</head>
<body>
    <img src="myapp://images/logo.png" alt="Logo">
    <h1>Hello from Pytonium</h1>
</body>
</html>
```

!!! tip "Relative paths"
    Within HTML served from a custom scheme, you can also use relative paths.
    For example, if the page is `myapp://index.html`, then `<script src="js/app.js">`
    resolves to `myapp://js/app.js`.

---

## Custom MIME Type Mappings

Pytonium recognizes common file extensions (`.html`, `.css`, `.js`, `.png`,
`.jpg`, etc.) automatically.  For uncommon file types, use
`add_mime_type_mapping()` to tell Pytonium what Content-Type to serve.

```python
p.add_mime_type_mapping(".glb", "model/gltf-binary")
p.add_mime_type_mapping(".gltf", "model/gltf+json")
p.add_mime_type_mapping(".wasm", "application/wasm")
p.add_mime_type_mapping(".webp", "image/webp")
p.add_mime_type_mapping(".avif", "image/avif")
```

| Parameter        | Type  | Description                                  |
|------------------|-------|----------------------------------------------|
| `file_extension` | `str` | The file extension including the dot (e.g. `".wasm"`). |
| `mime_type`      | `str` | The MIME type string (e.g. `"application/wasm"`).      |

!!! warning "Call before initialize"
    Like custom schemes, MIME type mappings must be registered before
    `initialize()`.

---

## Use Case: 3D Viewer with Babylon.js

Custom schemes and MIME mappings are particularly useful for loading 3D assets
that require specific content types.

=== "Python"

    ```python
    import time
    from Pytonium import Pytonium

    p = Pytonium()

    # Map the scheme to our assets folder
    p.add_custom_scheme("viewer", "./viewer_app/")

    # Register 3D model MIME types
    p.add_mime_type_mapping(".glb", "model/gltf-binary")
    p.add_mime_type_mapping(".gltf", "model/gltf+json")
    p.add_mime_type_mapping(".bin", "application/octet-stream")

    p.initialize("viewer://index.html", 1024, 768)

    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

    p.shutdown()
    ```

=== "HTML (viewer_app/index.html)"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>3D Viewer</title>
        <script src="https://cdn.babylonjs.com/babylon.js"></script>
        <script src="https://cdn.babylonjs.com/loaders/babylonjs.loaders.min.js"></script>
        <style>
            body { margin: 0; overflow: hidden; }
            #renderCanvas { width: 100%; height: 100vh; }
        </style>
    </head>
    <body>
        <canvas id="renderCanvas"></canvas>
        <script>
            const canvas = document.getElementById("renderCanvas");
            const engine = new BABYLON.Engine(canvas, true);
            BABYLON.SceneLoader.Load(
                "viewer://models/",
                "scene.glb",
                engine,
                (scene) => {
                    scene.createDefaultCameraOrLight(true, true, true);
                    engine.runRenderLoop(() => scene.render());
                }
            );
            window.addEventListener("resize", () => engine.resize());
        </script>
    </body>
    </html>
    ```

---

## Alternative: file:/// Protocol

For simple cases where you do not need clean URLs, you can use the `file:///`
protocol directly.

```python
import os

html_path = os.path.abspath("./web/index.html")
p.initialize(f"file:///{html_path}", 800, 600)
```

!!! note "When to use custom schemes vs file:///"
    Use **custom schemes** when your app has multiple assets (CSS, JS, images)
    and you want clean, predictable URLs.  Use **file:///** for quick
    prototypes or single-file apps where URL structure does not matter.

---

## Multiple Schemes

You can register multiple schemes, each pointing to a different directory.

```python
p.add_custom_scheme("app", "./src/frontend/")
p.add_custom_scheme("assets", "./resources/")
p.add_custom_scheme("data", "./data_files/")
```

Then use them in HTML:

```html
<link rel="stylesheet" href="app://styles/main.css">
<img src="assets://icons/logo.png">
<script>
    fetch("data://config.json")
        .then(r => r.json())
        .then(config => console.log(config));
</script>
```
