"""Build or preview the MkDocs documentation locally."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--serve",
        action="store_true",
        help="start MkDocs' live-reloading preview server instead of building",
    )
    parser.add_argument(
        "--address",
        default="127.0.0.1:8000",
        help="preview address used with --serve (default: 127.0.0.1:8000)",
    )
    parser.add_argument(
        "--output",
        default="site",
        help="static build directory, relative to the repository (default: site)",
    )
    args = parser.parse_args()

    if importlib.util.find_spec("mkdocs") is None:
        print(
            "MkDocs is not installed for this Python interpreter. Run:\n"
            f"  {sys.executable} -m pip install -r "
            f'"{ROOT / "requirements-docs.txt"}"',
            file=sys.stderr,
        )
        return 1

    command = [
        sys.executable,
        "-m",
        "mkdocs",
        "serve" if args.serve else "build",
        "--config-file",
        str(ROOT / "mkdocs.yml"),
    ]
    if args.serve:
        command.extend(["--dev-addr", args.address])
    else:
        output = Path(args.output)
        if not output.is_absolute():
            output = ROOT / output
        command.extend(["--strict", "--clean", "--site-dir", str(output)])

    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
