#!/usr/bin/env python3
"""
Pytonium Build Preparation Script

This script performs all the necessary preparation steps before building the
Cython extension wheel. It combines cleanup, C++ syncing, and CEF binary
copying into a single automated workflow.

Usage:
    python prepare_build.py                    # Full prepare (Windows + Linux)
    python prepare_build.py --platform windows  # Windows only
    python prepare_build.py --platform linux    # Linux only
    python prepare_build.py --build-dir ../cmake-build-release  # Custom CMake build dir
    python prepare_build.py --dry-run          # Show what would be done
    python prepare_build.py -v                 # Verbose output
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
PYTHON_FRAMEWORK_DIR = SRC_DIR / "src" / "pytonium_python_framework"
PYTONIUM_LIBRARY_DIR = SRC_DIR / "src" / "pytonium_library"
PYTONIUM_SUBPROCESS_DIR = SRC_DIR / "src" / "pytonium_subprocess"
CEF_BINARIES_WINDOWS = SRC_DIR / "cef-binaries-windows"
CEF_BINARIES_LINUX = SRC_DIR / "cef-binaries-linux"


def clean_directories(directories, dry_run=False, verbose=False):
    """Remove existing directories."""
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists():
            if verbose or dry_run:
                action = "Would remove" if dry_run else "Removing"
                print(f"{action}: {directory}")
            if not dry_run:
                shutil.rmtree(dir_path)


def delete_files(file_list, dry_run=False, verbose=False):
    """Delete specific files."""
    for file_path in file_list:
        path = Path(file_path)
        if path.exists():
            if verbose or dry_run:
                action = "Would delete" if dry_run else "Deleting"
                print(f"{action}: {file_path}")
            if not dry_run:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)


def sync_cpp_library(dry_run=False, verbose=False):
    """Sync C++ library source files to pyframework."""
    src = PYTONIUM_LIBRARY_DIR
    dst = PYTHON_FRAMEWORK_DIR / "Pytonium" / "src" / "pytonium_library"

    if not src.exists():
        print(f"ERROR: Source library not found: {src}")
        return False

    if not dst.exists():
        print(f"ERROR: Target directory not found: {dst}")
        return False

    if verbose or dry_run:
        action = "Would sync" if dry_run else "Syncing"
        print(f"{action} C++ library: {src.name}/ -> {dst.parent.name}/{dst.name}/")

    if dry_run:
        return True

    deleted = 0
    for item in sorted(dst.iterdir()):
        if item.is_dir():
            shutil.rmtree(item)
            deleted += 1
        else:
            item.unlink()
            deleted += 1

    copied = 0
    for item in sorted(src.iterdir()):
        dst_item = dst / item.name
        if item.is_dir():
            shutil.copytree(item, dst_item)
        else:
            shutil.copy2(item, dst_item)
        copied += 1

    print(f"  Synced {copied} items (deleted: {deleted})")
    return True


def sync_subprocess(dry_run=False, verbose=False):
    """Sync subprocess source files to pyframework."""
    src = PYTONIUM_SUBPROCESS_DIR
    dst = PYTHON_FRAMEWORK_DIR / "Pytonium" / "src" / "pytonium_subprocess"

    if not src.exists():
        if verbose:
            print(f"Subprocess source not found: {src}, skipping")
        return True

    if not dst.exists():
        if verbose:
            print(f"Target directory not found: {dst}, creating")
        if not dry_run:
            dst.mkdir(parents=True, exist_ok=True)

    if verbose or dry_run:
        action = "Would sync" if dry_run else "Syncing"
        print(f"{action} subprocess: {src.name}/ -> {dst.parent.name}/{dst.name}/")

    if dry_run:
        return True

    for item in sorted(src.iterdir()):
        dst_item = dst / item.name
        if item.is_file():
            shutil.copy2(item, dst_item)

    print(f"  Synced subprocess files")
    return True


def copy_cef_binaries(platform, base_src, base_dest, dry_run=False, verbose=False):
    """Copy CEF binaries for a specific platform."""
    if verbose:
        print(f"\nCopying {platform} CEF binaries from {base_src}")

    src_path = Path(base_src)
    dest_path = Path(base_dest)

    if not src_path.exists():
        print(f"WARNING: CEF binaries not found: {base_src}")
        return 0

    dirs_to_copy = ["cmake", "include", "libcef_dll"]
    total_copied = 0

    for dir_name in dirs_to_copy:
        src = src_path / dir_name
        dest = dest_path / dir_name
        if src.exists():
            if verbose or dry_run:
                action = "Would copy" if dry_run else "Copying"
                print(f"  {action} {dir_name}/")
            if not dry_run:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                total_copied += len(list(src.rglob("*")))

    release_dir = dest_path / "Release"
    release_dir.mkdir(parents=True, exist_ok=True)

    if platform == "windows":
        lib_src = src_path / "Release" / "libcef.lib"
        lib_dest = release_dir / "libcef.lib"
    else:
        lib_src = src_path / "Release" / "libcef.so"
        lib_dest = release_dir / "libcef.so"

    if lib_src.exists():
        if not dry_run:
            # Remove existing file/symlink at destination
            if lib_dest.exists() or lib_dest.is_symlink():
                lib_dest.unlink()
            # Try symlink first (avoids copying 1.5GB libcef.so on Linux/WSL),
            # fall back to copy if symlinks aren't supported (e.g. NTFS without symlink perms)
            linked = False
            try:
                lib_dest.symlink_to(lib_src.resolve())
                linked = True
            except OSError:
                pass
            if linked:
                if verbose:
                    print(f"  Symlinked {lib_src.name} -> {lib_src.resolve()}")
            else:
                if verbose:
                    print(f"  Copying {lib_src.name} ({lib_src.stat().st_size / (1024*1024):.0f} MB)...")
                shutil.copy2(lib_src, lib_dest)
                # Verify the copy actually landed (WSL/NTFS can silently fail for large files)
                if not lib_dest.exists() or lib_dest.stat().st_size != lib_src.stat().st_size:
                    print(f"  ERROR: Copy verification failed for {lib_src.name}!")
                    print(f"    Expected size: {lib_src.stat().st_size}, got: {lib_dest.stat().st_size if lib_dest.exists() else 'missing'}")
                    return total_copied
                if verbose:
                    print(f"  Copied {lib_src.name} OK")
        elif verbose or dry_run:
            print(f"  Would link/copy {lib_src.name}")
        total_copied += 1

    return total_copied


def copy_cef_runtime(platform, dry_run=False, verbose=False):
    """Copy CEF runtime resources and DLLs to bin folder."""
    if platform == "windows":
        cef_src = CEF_BINARIES_WINDOWS
        bin_dest = PYTHON_FRAMEWORK_DIR / "Pytonium" / "bin_win"
    else:
        cef_src = CEF_BINARIES_LINUX
        bin_dest = PYTHON_FRAMEWORK_DIR / "Pytonium" / "bin_linux"

    if not cef_src.exists():
        print(f"WARNING: CEF binaries not found: {cef_src}")
        return 0

    if verbose or dry_run:
        action = "Would copy" if dry_run else "Copying"
        print(f"{action} CEF runtime to {bin_dest.name}/")

    if dry_run:
        return 1

    bin_dest.mkdir(parents=True, exist_ok=True)

    resources_src = cef_src / "Resources"
    if resources_src.exists():
        for item in resources_src.iterdir():
            dest = bin_dest / item.name
            if item.is_dir() and item.name == "locales":
                dest.mkdir(parents=True, exist_ok=True)
                for locale_file in item.iterdir():
                    shutil.copy2(locale_file, dest / locale_file.name)
            else:
                shutil.copy2(item, dest)

    release_src = cef_src / "Release"
    if release_src.exists():
        if platform == "windows":
            extensions = [".dll", ".exe"]
        else:
            extensions = [".so", ".so.1", ".bin", ".json"]
        for item in release_src.iterdir():
            if item.is_file():
                # Match exact suffix or multi-part suffixes like .so.1
                if item.suffix in extensions or "".join(item.suffixes) in extensions:
                    dest_file = bin_dest / item.name
                    shutil.copy2(item, dest_file)
                    if verbose:
                        size_mb = item.stat().st_size / (1024 * 1024)
                        print(f"  Copied {item.name} ({size_mb:.0f} MB)")

    # Strip debug symbols from .so files to reduce size (e.g. libcef.so 1.5GB -> ~250MB)
    if platform != "windows" and shutil.which("strip"):
        for item in bin_dest.iterdir():
            if item.is_file() and ".so" in item.name:
                original_size = item.stat().st_size
                if original_size > 1024 * 1024:  # Only strip files > 1MB
                    import subprocess
                    result = subprocess.run(
                        ["strip", "--strip-unneeded", str(item)],
                        capture_output=True,
                    )
                    if result.returncode == 0:
                        new_size = item.stat().st_size
                        if verbose:
                            print(
                                f"  Stripped {item.name}: "
                                f"{original_size / (1024*1024):.0f} MB -> {new_size / (1024*1024):.0f} MB"
                            )

    return 1


def find_subprocess_exe(platform, build_dir=None):
    """Find the pytonium_subprocess executable, searching build_dir first if provided."""
    exe_name = "pytonium_subprocess.exe" if platform == "windows" else "pytonium_subprocess"

    search_paths = []

    if build_dir:
        build_path = Path(build_dir).resolve()
        # CMake output structure: <build-dir>/src/pytonium_subprocess/<Config>/
        for config in ["Release", "release", "Debug", "debug"]:
            search_paths.append(build_path / "src" / "pytonium_subprocess" / config / exe_name)
        # Also check directly under the subprocess build dir (Linux single-config)
        search_paths.append(build_path / "src" / "pytonium_subprocess" / exe_name)

    # Default paths (where CMake post-build copies land)
    for config in ["release", "debug"]:
        search_paths.append(
            SRC_DIR / "src" / "pytonium_library_test" / config / "bin" / exe_name
        )

    for path in search_paths:
        if path.exists():
            return path

    return None


def copy_subprocess_exe(platform, build_dir=None, dry_run=False, verbose=False):
    """Copy the pytonium_subprocess executable to bin folder."""
    bin_dest = PYTHON_FRAMEWORK_DIR / "Pytonium" / ("bin_win" if platform == "windows" else "bin_linux")

    subprocess_src = find_subprocess_exe(platform, build_dir)

    if subprocess_src is None:
        locations = f" (build-dir: {build_dir})" if build_dir else ""
        print(f"WARNING: pytonium_subprocess not found at expected locations{locations}")
        return 0

    if verbose or dry_run:
        action = "Would copy" if dry_run else "Copying"
        print(f"{action} pytonium_subprocess to {bin_dest.name}/ (from {subprocess_src})")

    if dry_run:
        return 1

    bin_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(subprocess_src, bin_dest / subprocess_src.name)

    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Pytonium build by cleaning and copying necessary files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full prepare (all platforms)
  %(prog)s --platform windows       # Windows only
  %(prog)s --platform linux         # Linux only
  %(prog)s --build-dir ../cmake-build-release  # Custom CMake build dir
  %(prog)s --dry-run                # Show what would be done
  %(prog)s -v                       # Verbose output
        """,
    )

    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "all"],
        default="all",
        help="Which platform to prepare (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--skip-clean", action="store_true", help="Skip cleanup step")
    parser.add_argument(
        "--skip-sync", action="store_true", help="Skip C++ source sync step"
    )
    parser.add_argument(
        "--skip-cef", action="store_true", help="Skip CEF binary copy step"
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        default=None,
        help="Path to the CMake build directory (e.g. cmake-build-release, build_linux). "
             "Used to locate the pytonium_subprocess executable.",
    )

    args = parser.parse_args()

    print(f"{'=' * 60}")
    print(f"Pytonium Build Preparation Script")
    print(f"{'=' * 60}")

    if args.dry_run:
        print("*** DRY RUN - No changes will be made ***\n")

    dirs_to_clean = [
        PYTHON_FRAMEWORK_DIR / "dist",
        PYTHON_FRAMEWORK_DIR / "_skbuild",
        PYTHON_FRAMEWORK_DIR / "Pytonium.egg-info",
    ]

    if args.platform in ("windows", "all"):
        dirs_to_clean.append(PYTHON_FRAMEWORK_DIR / "Pytonium" / "bin_win")
    if args.platform in ("linux", "all"):
        dirs_to_clean.append(PYTHON_FRAMEWORK_DIR / "Pytonium" / "bin_linux")

    if not args.skip_clean:
        if args.verbose or args.dry_run:
            print("Step 1: Cleaning old build artifacts...")
            for d in dirs_to_clean:
                print(f"  - {d.relative_to(PYTHON_FRAMEWORK_DIR)}")
        clean_directories(dirs_to_clean, args.dry_run, args.verbose)
    else:
        print("Step 1: Skipping cleanup (--skip-clean)")

    print()

    if not args.skip_sync:
        if args.verbose or args.dry_run:
            print("Step 2: Syncing C++ library source files...")
        success = sync_cpp_library(args.dry_run, args.verbose)
        if not success:
            print("ERROR: Failed to sync C++ library")
            return 1

        if args.verbose or args.dry_run:
            print("Step 3: Syncing subprocess source files...")
        sync_subprocess(args.dry_run, args.verbose)
    else:
        print("Step 2-3: Skipping C++ sync (--skip-sync)")

    print()

    total_binaries = 0

    if not args.skip_cef:
        if args.platform in ("windows", "all"):
            if args.verbose or args.dry_run:
                print("Step 4: Copying CEF Windows binaries...")
            count = copy_cef_binaries(
                "windows",
                CEF_BINARIES_WINDOWS,
                PYTHON_FRAMEWORK_DIR / "Pytonium" / "src" / "cef-binaries-windows",
                args.dry_run,
                args.verbose,
            )
            total_binaries += count

            if args.verbose or args.dry_run:
                print("Step 5: Copying CEF Windows runtime to bin_win/...")
            copy_cef_runtime("windows", args.dry_run, args.verbose)

            if args.verbose or args.dry_run:
                print("Step 6: Copying pytonium_subprocess.exe...")
            copy_subprocess_exe("windows", args.build_dir, args.dry_run, args.verbose)

        if args.platform in ("linux", "all"):
            if args.verbose or args.dry_run:
                print("Step 4: Copying CEF Linux binaries...")
            count = copy_cef_binaries(
                "linux",
                CEF_BINARIES_LINUX,
                PYTHON_FRAMEWORK_DIR / "Pytonium" / "src" / "cef-binaries-linux",
                args.dry_run,
                args.verbose,
            )
            total_binaries += count

            if args.verbose or args.dry_run:
                print("Step 5: Copying CEF Linux runtime to bin_linux/...")
            copy_cef_runtime("linux", args.dry_run, args.verbose)

            if args.verbose or args.dry_run:
                print("Step 6: Copying pytonium_subprocess...")
            copy_subprocess_exe("linux", args.build_dir, args.dry_run, args.verbose)
    else:
        print("Step 4-6: Skipping CEF copy (--skip-cef)")

    print()
    print(f"{'=' * 60}")
    mode = "(dry run - no changes made)" if args.dry_run else ""
    print(f"Preparation complete {mode}")
    print(f"Platform: {args.platform}")
    print(f"{'=' * 60}")
    print()
    print("Next step: Build the wheel with:")
    print(f"  cd {PYTHON_FRAMEWORK_DIR}")
    print(f"  python -m build --wheel")
    print(f"  After build, install. For example: pip install dist/pytonium-0.0.13-cp313-cp313-win_amd64.whl --force-reinstall")
    return 0


if __name__ == "__main__":
    sys.exit(main())
