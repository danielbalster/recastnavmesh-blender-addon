#!/usr/bin/env python3
"""Package the add-on into a .zip file for Blender installation.

Usage:
    python package.py                           # creates navmesh_addon.zip
    python package.py --version v0.3.0          # creates navmesh_addon-v0.3.0.zip
    python package.py --platform linux-x64      # creates navmesh_linux-x64.zip
    python package.py --platform linux-x64 --version v0.3.0  # navmesh_linux-x64-v0.3.0.zip
"""

import os
import sys
import zipfile
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.join(SCRIPT_DIR, "navmesh_addon")


def main():
    parser = argparse.ArgumentParser(description="Package Blender add-on")
    parser.add_argument("--version", default=None, help="Version string (e.g. v0.3.0)")
    parser.add_argument(
        "--platform", default=None, help="Platform ID (e.g. linux-x64, windows-x64)"
    )
    args = parser.parse_args()

    if args.platform:
        filename = f"navmesh_{args.platform}"
    else:
        filename = "navmesh_addon"

    if args.version:
        filename += f"-{args.version}"
    filename += ".zip"

    output = os.path.join(SCRIPT_DIR, filename)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ADDON_DIR):
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
    if not args.platform:
        print(
            "Make sure navmesh_addon/libs/libNavMeshWrapper.so exists before installing."
        )


if __name__ == "__main__":
    main()
