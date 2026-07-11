bl_info = {
    "name": "Recast NavMesh",
    "author": "Recast Blender Add-on",
    "version": (0, 1, 5),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > NavMesh",
    "description": "Generate navigation meshes from selected geometry using Recast/Detour",
    "category": "3D View",
}

import ctypes
import os
import platform

LIB_DIR = os.path.join(os.path.dirname(__file__), "libs")

PLATFORM_EXTS = {
    "Linux": ".so",
    "Darwin": ".dylib",
    "Windows": ".dll",
}

_ext = PLATFORM_EXTS.get(platform.system(), ".so")

_lib_wrapper = None


def get_lib_wrapper():
    global _lib_wrapper
    if _lib_wrapper is None:
        _lib_wrapper = ctypes.CDLL(os.path.join(LIB_DIR, f"libNavMeshWrapper{_ext}"))
    return _lib_wrapper


def register():
    from . import operators
    from . import panels

    operators.register()
    panels.register()


def unregister():
    from . import operators
    from . import panels

    operators.unregister()
    panels.unregister()
