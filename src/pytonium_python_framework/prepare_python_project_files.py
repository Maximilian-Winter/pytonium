#!/usr/bin/env python3
"""
Prepare Python project files by copying C++ source and CEF binaries.

This script copies the necessary files from the main project into the
Python framework build folder before building the wheel.
"""

import argparse
import os
import shutil
import sys
from os.path import isfile
from pathlib import Path


def clean_directories(directories, dry_run=False, verbose=False):
    """Remove existing directories."""
    for directory in directories:
        if os.path.exists(directory):
            if verbose or dry_run:
                action = "Would remove" if dry_run else "Removing"
                print(f"{action}: {directory}")
            if not dry_run:
                shutil.rmtree(directory)


def copy_files(src_dir, dest_dir, pattern="*", dry_run=False, verbose=False, preserve_structure=True):
    """Copy files from source to destination."""
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)
    
    if not src_path.exists():
        if verbose:
            print(f"Source directory does not exist: {src_dir}")
        return
    
    copied = 0
    for path in src_path.rglob(pattern):
        if path.is_file():
            if preserve_structure:
                relative_path = path.relative_to(src_path)
                dest_fpath = dest_path / relative_path
            else:
                dest_fpath = dest_path / path.name
            
            if verbose or dry_run:
                action = "Would copy" if dry_run else "Copying"
                print(f"{action}: {path} -> {dest_fpath}")
            
            if not dry_run:
                os.makedirs(dest_fpath.parent, exist_ok=True)
                shutil.copyfile(path, dest_fpath)
            copied += 1
    
    return copied


def copy_cef_binaries(platform, base_src, base_dest, dry_run=False, verbose=False):
    """Copy CEF binaries for a specific platform."""
    if verbose:
        print(f"\nCopying {platform} CEF binaries...")
    
    dirs_to_copy = ["cmake", "include", "libcef_dll"]
    total_copied = 0
    
    for dir_name in dirs_to_copy:
        src = Path(base_src) / dir_name
        dest = Path(base_dest) / dir_name
        if src.exists():
            count = copy_files(src, dest, "*", dry_run, verbose, preserve_structure=True)
            total_copied += count
        elif verbose:
            print(f"  Directory not found: {src}")
    
    # Create Release directory and copy library file
    release_dir = Path(base_dest) / "Release"
    release_placeholder = release_dir / "placeholder"
    
    if platform == "windows":
        lib_src = Path(base_src) / "Release" / "libcef.lib"
        lib_dest = release_dir / "libcef.lib"
    else:
        lib_src = Path(base_src) / "Release" / "libcef.so"
        lib_dest = release_dir / "libcef.so"
    
    if verbose or dry_run:
        action = "Would create" if dry_run else "Creating"
        print(f"{action} directory: {release_dir}")
    
    if not dry_run:
        os.makedirs(release_dir, exist_ok=True)
        if not release_placeholder.exists():
            release_placeholder.touch()
    
    if lib_src.exists():
        if verbose or dry_run:
            action = "Would copy" if dry_run else "Copying"
            print(f"{action}: {lib_src} -> {lib_dest}")
        if not dry_run:
            shutil.copyfile(lib_src, lib_dest)
        total_copied += 1
    elif verbose:
        print(f"  Library file not found: {lib_src}")
    
    return total_copied


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Python project files by copying C++ source and CEF binaries.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full prepare (clean + copy all)
  %(prog)s --platform windows       # Copy only Windows binaries
  %(prog)s --platform linux         # Copy only Linux binaries
  %(prog)s --no-clean               # Skip cleanup, just copy files
  %(prog)s --dry-run                # Show what would be done
  %(prog)s -v                       # Verbose output
        """
    )
    
    parser.add_argument(
        "--platform",
        choices=["windows", "linux", "all"],
        default="all",
        help="Which platform binaries to copy (default: all)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleanup of existing directories"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean directories, don't copy files"
    )
    parser.add_argument(
        "--clean-all",
        action="store_true",
        help="Clean all directories regardless of --platform (default: only clean what will be copied)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--src-library",
        default="../pytonium_library/",
        help="Source directory for pytonium library (default: ../pytonium_library/)"
    )
    parser.add_argument(
        "--src-windows",
        default="../../cef-binaries-windows/",
        help="Source directory for Windows CEF binaries (default: ../../cef-binaries-windows/)"
    )
    parser.add_argument(
        "--src-linux",
        default="../../cef-binaries-linux/",
        help="Source directory for Linux CEF binaries (default: ../../cef-binaries-linux/)"
    )
    parser.add_argument(
        "--dest",
        default="./Pytonium/src/",
        help="Destination directory (default: ./Pytonium/src/)"
    )
    
    args = parser.parse_args()
    
    # Define directories to clean based on platform selection
    # By default, only clean what we're going to copy (to preserve other platform binaries)
    dirs_to_clean = [
        "./Pytonium/src/pytonium_library/",
        "./dist",
        "./_skbuild",
        "./Pytonium.egg-info"
    ]
    
    # Only clean platform directories that we're going to copy
    if args.platform in ("windows", "all") or args.clean_all:
        dirs_to_clean.append("./Pytonium/src/cef-binaries-windows/")
    if args.platform in ("linux", "all") or args.clean_all:
        dirs_to_clean.append("./Pytonium/src/cef-binaries-linux/")
    
    # Clean directories
    if not args.no_clean:
        if args.verbose or args.dry_run:
            print(f"Cleaning directories for platform '{args.platform}'...")
            for d in dirs_to_clean:
                print(f"  - {d}")
        clean_directories(dirs_to_clean, args.dry_run, args.verbose)
    
    if args.clean_only:
        if args.verbose or args.dry_run:
            print("Clean-only mode, exiting.")
        return 0
    
    # Copy pytonium library source
    if args.verbose or args.dry_run:
        print("\nCopying pytonium library source...")
    
    src_lib = Path(args.src_library)
    dest_lib = Path(args.dest) / "pytonium_library"
    
    if not src_lib.exists():
        print(f"Error: Source library directory not found: {src_lib}")
        print("Make sure you're running this script from the pytonium_python_framework directory")
        return 1
    
    copied = copy_files(src_lib, dest_lib, "*", args.dry_run, args.verbose, preserve_structure=True)
    if args.verbose:
        print(f"Copied {copied} library files")
    
    # Copy CEF binaries
    total_binaries = 0
    
    if args.platform in ("windows", "all"):
        dest_win = Path(args.dest) / "cef-binaries-windows"
        count = copy_cef_binaries("windows", args.src_windows, dest_win, args.dry_run, args.verbose)
        total_binaries += count
        if args.verbose:
            print(f"Copied {count} Windows binary files")
    
    if args.platform in ("linux", "all"):
        dest_linux = Path(args.dest) / "cef-binaries-linux"
        count = copy_cef_binaries("linux", args.src_linux, dest_linux, args.dry_run, args.verbose)
        total_binaries += count
        if args.verbose:
            print(f"Copied {count} Linux binary files")
    
    # Summary
    if args.verbose or args.dry_run:
        mode = "(dry run - no changes made)" if args.dry_run else ""
        print(f"\n{'='*50}")
        print(f"Prepare complete {mode}")
        print(f"Platform: {args.platform}")
        print(f"Library files: {copied}")
        print(f"CEF binary files: {total_binaries}")
        print(f"{'='*50}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
