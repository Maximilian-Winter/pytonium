"""Container for a single loaded widget instance."""


class WidgetInstance:
    """Holds the Pytonium instance, manifest data, and optional backend for one widget."""

    def __init__(self, name, pytonium, manifest, backend_module=None):
        self.name = name
        self.pytonium = pytonium
        self.manifest = manifest
        self.backend = backend_module
        self.watcher = None  # set by hot_reload if enabled
