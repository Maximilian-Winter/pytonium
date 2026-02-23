"""LayerInstance — state container for a single desktop shell layer."""

from enum import Enum


class LayerType(Enum):
    """Types of layers in the desktop compositor."""
    WALLPAPER = "wallpaper"       # Bottom layer, always click-through
    DESKTOP = "desktop"           # Desktop icons, above wallpaper
    WIDGET_HOST = "widget_host"   # Widget container, above desktop
    TASKBAR = "taskbar"           # Docked bar, always interactive
    OVERLAY = "overlay"           # Top layer, shown on demand (launcher, notifications)


class InputMode(Enum):
    """How a layer handles mouse/keyboard input."""
    CLICK_THROUGH_ALWAYS = "click_through_always"        # Never receives input
    ALWAYS_ACTIVE = "always_active"                      # Always receives input
    PASSTHROUGH_WHEN_INACTIVE = "passthrough_when_inactive"  # Input only when shown/focused


class LayerInstance:
    """Holds the Pytonium instance, config, and runtime state for one layer."""

    def __init__(self, layer_id, layer_type, z_order, config):
        # Identity
        self.id = layer_id                     # e.g. "wallpaper", "taskbar"
        self.type = layer_type                 # LayerType enum
        self.z_order = z_order                 # numeric z-ordering (0 = bottom)
        self.config = config                   # layer-specific config dict from shell.json

        # Runtime state (set during load)
        self.pytonium = None                   # Pytonium instance
        self.backend = None                    # loaded backend module (optional)
        self.backend_obj = None                # instantiated WidgetBackend (optional)
        self.visible = True                    # current visibility
        self.input_mode = InputMode(
            config.get("input", "passthrough_when_inactive")
        )

        # Bar mode: AppBar data for cleanup
        self.appbar_data = None

    def __repr__(self):
        return (f"LayerInstance(id={self.id!r}, type={self.type.value}, "
                f"z={self.z_order}, visible={self.visible})")
