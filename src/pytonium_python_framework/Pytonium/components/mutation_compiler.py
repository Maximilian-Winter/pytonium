"""MutationCompiler: Generates minimal JavaScript from UpdateCommands.

Pure Python implementation. Takes a list of UpdateCommand objects, groups them
by target node, and compiles into a single JS IIFE that executes all mutations
in one batch (single reflow). Sends via Pytonium.execute_javascript().
"""

from collections import defaultdict
from typing import Optional

from .types import UpdateCommand, UpdateType


def _js_string(s: str) -> str:
    """Escape and quote a Python string for safe embedding in JavaScript.

    Handles newlines, quotes, backslashes, and angle brackets to prevent
    XSS and syntax errors in generated JS.
    """
    if s is None:
        return '""'
    s = str(s)
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")
    s = s.replace("<", "\\x3c")
    s = s.replace(">", "\\x3e")
    return f'"{s}"'


def _var_name(node_id: str) -> str:
    """Convert a node_id like 'n_0042' into a valid JS variable name."""
    return node_id.replace("-", "_")


class MutationCompiler:
    """Compiles UpdateCommands into minimal JavaScript and sends to CEF.

    The compiler groups mutations by target node ID so each querySelector
    is called only once. All mutations are wrapped in an IIFE for a single
    execution context and single DOM reflow.

    Usage:
        compiler = MutationCompiler(pytonium_instance)
        compiler.apply_batch([
            UpdateCommand("n_0001", UpdateType.SET_TEXT_CONTENT, value="Hello"),
            UpdateCommand("n_0002", UpdateType.ADD_CLASS, value="active"),
        ])
    """

    def __init__(self, pytonium=None):
        """Initialize with a Pytonium instance for execute_javascript calls.

        Args:
            pytonium: Pytonium instance. Can be None for testing (compile_batch
                      still works, apply_batch becomes a no-op).
        """
        self._pytonium = pytonium

    def compile_batch(self, commands: list[UpdateCommand]) -> str:
        """Compile a list of UpdateCommands into a single JavaScript string.

        Groups commands by node_id to minimize querySelector calls.
        Returns an empty string if no commands are provided.

        Args:
            commands: List of UpdateCommand objects to compile.

        Returns:
            JavaScript IIFE string, or empty string if no commands.
        """
        if not commands:
            return ""

        lines: list[str] = []
        by_node: dict[str, list[UpdateCommand]] = defaultdict(list)
        for cmd in commands:
            by_node[cmd.node_id].append(cmd)

        for node_id, cmds in by_node.items():
            vn = _var_name(node_id)
            lines.append(
                f'var {vn}=document.querySelector(\'[data-pyt-id="{node_id}"]\');'
            )
            lines.append(f"if({vn}){{")
            for cmd in cmds:
                line = self._compile_single(vn, cmd)
                if line:
                    lines.append(line)
            lines.append("}")

        return "(function(){" + "".join(lines) + "})();"

    def apply_batch(self, commands: list[UpdateCommand]) -> str:
        """Compile commands and execute the resulting JS in the browser.

        Args:
            commands: List of UpdateCommand objects.

        Returns:
            The generated JavaScript string (useful for debugging/testing).
        """
        js = self.compile_batch(commands)
        if js and self._pytonium is not None:
            self._pytonium.execute_javascript(js)
        return js

    def _compile_single(self, var_name: str, cmd: UpdateCommand) -> str:
        """Compile a single UpdateCommand into a JS statement.

        Args:
            var_name: JS variable name holding the DOM element reference.
            cmd: The UpdateCommand to compile.

        Returns:
            JavaScript statement string.
        """
        match cmd.update_type:
            case UpdateType.SET_TEXT_CONTENT:
                return f"{var_name}.textContent={_js_string(cmd.value)};"

            case UpdateType.SET_ATTRIBUTE:
                return (
                    f"{var_name}.setAttribute("
                    f"{_js_string(cmd.key)},{_js_string(cmd.value)});"
                )

            case UpdateType.REMOVE_ATTRIBUTE:
                return f"{var_name}.removeAttribute({_js_string(cmd.key)});"

            case UpdateType.ADD_CLASS:
                return f"{var_name}.classList.add({_js_string(cmd.value)});"

            case UpdateType.REMOVE_CLASS:
                return f"{var_name}.classList.remove({_js_string(cmd.value)});"

            case UpdateType.TOGGLE_CLASS:
                return (
                    f"{var_name}.classList.toggle("
                    f"{_js_string(cmd.key)},{cmd.value});"
                )

            case UpdateType.SET_STYLE:
                return (
                    f"{var_name}.style[{_js_string(cmd.key)}]"
                    f"={_js_string(cmd.value)};"
                )

            case UpdateType.SET_VALUE:
                return f"{var_name}.value={_js_string(cmd.value)};"

            case UpdateType.INSERT_CHILD:
                if cmd.index >= 0:
                    return (
                        f"(function(){{var r={var_name}.children[{cmd.index}];"
                        f"if(r){{{var_name}.insertAdjacentHTML('beforebegin',"
                        f"{_js_string(cmd.html)});}}"
                        f"else{{{var_name}.insertAdjacentHTML('beforeend',"
                        f"{_js_string(cmd.html)});}}}})()"
                    )
                return (
                    f"{var_name}.insertAdjacentHTML("
                    f'"beforeend",{_js_string(cmd.html)});'
                )

            case UpdateType.REMOVE_CHILD:
                return (
                    f"var _rc=document.querySelector("
                    f"'[data-pyt-id=\"{cmd.value}\"]');"
                    f"if(_rc)_rc.remove();"
                )

            case UpdateType.MOVE_CHILD:
                return (
                    f"(function(){{var _mc=document.querySelector("
                    f"'[data-pyt-id=\"{cmd.value}\"]');"
                    f"if(_mc){{var _ref={var_name}.children[{cmd.index}];"
                    f"if(_ref){{{var_name}.insertBefore(_mc,_ref);}}"
                    f"else{{{var_name}.appendChild(_mc);}}}}}})()"
                )

            case UpdateType.REPLACE_INNER_HTML:
                return f"{var_name}.innerHTML={_js_string(cmd.html)};"

            case _:
                return ""
