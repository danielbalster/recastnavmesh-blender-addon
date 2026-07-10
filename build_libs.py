#!/usr/bin/env python3
"""Build the native NavMesh wrapper library.

Clones recastnavigation (shallow, depth 1) if not present,
then compiles the combined C-linkage wrapper library into
navmesh_addon/libs/.

Prerequisites: g++, git, cmake (optional, only needed if using
CMake-based approach; this script defaults to direct g++ compile).
"""

import os
import subprocess
import sys
import platform
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RECAST_DIR = os.path.join(SCRIPT_DIR, "recastnavigation")
WRAPPER_DIR = os.path.join(SCRIPT_DIR, "navmesh_wrapper")
LIBS_DIR = os.path.join(SCRIPT_DIR, "navmesh_addon", "libs")


def run(cmd, cwd=None):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)


def clone_recast():
    if os.path.isdir(RECAST_DIR):
        print(f"recastnavigation already present at {RECAST_DIR}, skipping clone")
        return
    print("Cloning recastnavigation (shallow, depth 1)...")
    run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "main",
            "https://github.com/recastnavigation/recastnavigation.git",
            RECAST_DIR,
        ],
        cwd=SCRIPT_DIR,
    )


def build_wrapper():
    os.makedirs(LIBS_DIR, exist_ok=True)

    recast_include = os.path.join(RECAST_DIR, "Recast", "Include")
    detour_include = os.path.join(RECAST_DIR, "Detour", "Include")
    recast_source = os.path.join(RECAST_DIR, "Recast", "Source")
    detour_source = os.path.join(RECAST_DIR, "Detour", "Source")

    ext = (
        ".dll"
        if platform.system() == "Windows"
        else ".so"
        if platform.system() == "Linux"
        else ".dylib"
    )
    output = os.path.join(LIBS_DIR, f"libNavMeshWrapper{ext}")

    sources = (
        [
            os.path.join(recast_source, f)
            for f in [
                "Recast.cpp",
                "RecastAlloc.cpp",
                "RecastArea.cpp",
                "RecastAssert.cpp",
                "RecastContour.cpp",
                "RecastFilter.cpp",
                "RecastLayers.cpp",
                "RecastMesh.cpp",
                "RecastMeshDetail.cpp",
                "RecastRasterization.cpp",
                "RecastRegion.cpp",
            ]
        ]
        + [
            os.path.join(detour_source, f)
            for f in [
                "DetourAlloc.cpp",
                "DetourAssert.cpp",
                "DetourCommon.cpp",
                "DetourNavMesh.cpp",
                "DetourNavMeshBuilder.cpp",
                "DetourNavMeshQuery.cpp",
                "DetourNode.cpp",
            ]
        ]
        + [os.path.join(WRAPPER_DIR, "wrapper.cpp")]
    )

    cmd = ["g++", "-shared", "-fPIC", "-O2", "-ffast-math", "-ffinite-math-only"]
    cmd += ["-I", recast_include, "-I", detour_include]
    cmd += ["-o", output]
    cmd += sources

    print("Building libNavMeshWrapper...")
    run(cmd, cwd=SCRIPT_DIR)
    print(f"Built: {output}")


def main():
    clone_recast()
    build_wrapper()
    print("Build complete.")


if __name__ == "__main__":
    main()
