"""Unit tests for Pytonium Python API.

These tests validate the public API surface without requiring a running
CEF browser (no GPU, no display server needed).
"""

import pytest
import sys
import os

# Ensure the package is importable for editable installs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "pytonium_python_framework"))


class TestImportAndCreation:
    """Tests that the package can be imported and instances created."""

    def test_import_pytonium(self):
        from Pytonium import Pytonium
        assert Pytonium is not None

    def test_create_instance(self):
        from Pytonium import Pytonium
        p = Pytonium()
        assert p is not None

    def test_subprocess_path_set(self):
        from Pytonium import Pytonium
        path = Pytonium.pytonium_subprocess_path()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_returns_value_decorator(self):
        from Pytonium import returns_value_to_javascript

        @returns_value_to_javascript("number")
        def my_func():
            return 42

        assert my_func.returns_value_to_javascript is True
        assert my_func.return_type == "number"
        assert my_func() == 42


class TestInputValidation:
    """Tests that invalid inputs raise appropriate errors."""

    def test_bind_function_not_callable(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(TypeError, match="callable"):
            p.bind_function_to_javascript("not a function")

    def test_bind_functions_not_list(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(TypeError, match="list"):
            p.bind_functions_to_javascript("not a list")

    def test_bind_functions_item_not_callable(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(TypeError, match="callable"):
            p.bind_functions_to_javascript([lambda: None, "not_callable"])

    def test_bind_object_methods_none(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(ValueError, match="None"):
            p.bind_object_methods_to_javascript(None)

    def test_add_context_menu_entry_not_callable(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(TypeError, match="callable"):
            p.add_context_menu_entry(42)

    def test_add_state_handler_without_update_state(self):
        from Pytonium import Pytonium
        p = Pytonium()

        class BadHandler:
            pass

        with pytest.warns(UserWarning, match="update_state"):
            p.add_state_handler(BadHandler(), ["test"])

    def test_on_title_change_not_callable(self):
        from Pytonium import Pytonium
        p = Pytonium()
        with pytest.raises(TypeError, match="callable"):
            p.on_title_change("not callable")


class TestDecoratorBehavior:
    """Tests for the returns_value_to_javascript decorator."""

    def test_decorator_preserves_function(self):
        from Pytonium import returns_value_to_javascript

        @returns_value_to_javascript("string")
        def greet(name):
            return f"Hello, {name}!"

        assert greet("World") == "Hello, World!"

    def test_decorator_default_return_type(self):
        from Pytonium import returns_value_to_javascript

        @returns_value_to_javascript()
        def test_func():
            return "test"

        assert test_func.return_type == "any"

    def test_decorator_custom_return_type(self):
        from Pytonium import returns_value_to_javascript

        @returns_value_to_javascript("boolean")
        def check():
            return True

        assert check.return_type == "boolean"


class TestBindingRegistration:
    """Tests that function bindings work without crashing."""

    def test_bind_single_function(self):
        from Pytonium import Pytonium
        p = Pytonium()

        def hello():
            pass

        p.bind_function_to_javascript(hello)

    def test_bind_function_with_custom_name(self):
        from Pytonium import Pytonium
        p = Pytonium()

        def hello():
            pass

        p.bind_function_to_javascript(hello, name="greet")

    def test_bind_multiple_functions(self):
        from Pytonium import Pytonium
        p = Pytonium()

        def func_a():
            pass

        def func_b():
            pass

        p.bind_functions_to_javascript([func_a, func_b])

    def test_bind_object_methods(self):
        from Pytonium import Pytonium
        p = Pytonium()

        class Api:
            def hello(self):
                pass

            def world(self):
                pass

        p.bind_object_methods_to_javascript(Api())

    def test_bind_with_javascript_object_namespace(self):
        from Pytonium import Pytonium
        p = Pytonium()

        def my_func():
            pass

        p.bind_function_to_javascript(my_func, javascript_object="myApi")


class TestInstanceState:
    """Tests for instance state before initialization."""

    def test_is_running_before_init(self):
        from Pytonium import Pytonium
        p = Pytonium()
        assert p.is_running() is False

    def test_get_window_handle_before_init(self):
        from Pytonium import Pytonium
        p = Pytonium()
        assert p.get_native_window_handle() == 0

    def test_browser_id_before_init(self):
        from Pytonium import Pytonium
        p = Pytonium()
        assert p.get_browser_id() == -1

    def test_cef_not_initialized_before_init(self):
        from Pytonium import Pytonium
        assert Pytonium.is_cef_initialized() is False


class TestMultiInstanceImports:
    """Tests that multi-instance helpers are importable."""

    def test_import_multi_async(self):
        from Pytonium import run_pytonium_multi_async
        assert callable(run_pytonium_multi_async)

    def test_import_single_async(self):
        from Pytonium import run_pytonium_async
        assert callable(run_pytonium_async)

    def test_create_two_instances(self):
        from Pytonium import Pytonium
        p1 = Pytonium()
        p2 = Pytonium()
        assert p1 is not p2
        assert p1.get_browser_id() == -1
        assert p2.get_browser_id() == -1
        assert p1.is_running() is False
        assert p2.is_running() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
