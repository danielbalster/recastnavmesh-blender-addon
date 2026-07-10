#!/usr/bin/env python3
"""Package the add-on into a .zip file for Blender installation.

Usage:
    python package.py              # creates navmesh_addon.zip
    python package.py --version X  # includes version in filename
"""

import os
import sys
import zipfile
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(SCRIPT_DIR, "navmesh_addon")


def main():
    parser = argparse.ArgumentParser(description="Package Blender add-on")
    parser.add_argument("--version", default=None, help="Version string")
    args = parser.parse_args()

    filename = "navmesh_addon"
    if args.version:
        filename += f"-{args.version}"
    filename += ".zip"

    output = os.path.join(SCRIPT_DIR, filename)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ADDON_DIR):
            # Skip empty libs directory (user runs build_libs.py after install)
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for fname in files:
                if fname.endswith(".pyc") or fname.startswith("."):
                    continue
                filepath = os.path.join(root, fname)
                arcname = os.path.relpath(filepath, SCRIPT_DIR)
                zf.write(filepath, arcname)

    size = os.path.getsize(output)
    print(f"Created {output} ({size} bytes)")
    print(
        "Install in Blender: Edit > Preferences > Add-ons > Install... > select this file"
    )
    print(
        "Then run: python build_libs.py in the add-on directory to compile the native library."
    )


if __name__ == "__main__":
    main()
