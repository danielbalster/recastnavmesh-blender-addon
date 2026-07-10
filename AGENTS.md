# AGENTS.md — Recast NavMesh Blender Add-on

## Project repository

```
recastnavmesh-blender-addon/
├── navmesh_addon/             # Blender add-on directory
│   ├── __init__.py            # bl_info, register/unregister, library loading
│   ├── build.py               # ctypes structs + full Recast→Detour pipeline + tile parser
│   ├── operators.py           # NAVMESH_OT_Rebuild operator
│   ├── panels.py              # NAVMESH_PT_Main panel
│   └── libs/                  # compiled .so/.dll/.dylib go here (gitignored)
├── navmesh_wrapper/
│   └── wrapper.cpp            # C-linkage adapter: wraps all C++ functions in extern "C"
├── build_libs.py              # Python build script (clones recast, compiles wrapper)
├── package.py                 # Creates .zip for Blender add-on installation
├── .github/workflows/release.yml  # CI/CD: builds on tag, creates multi-platform release
├── .gitignore
├── LICENSE                    # MIT
├── README.md
└── AGENTS.md                  # This file
```

### Development workspace layout (for reference)

```
recast-blender/
├── recastnavigation/          # full upstream clone (not shallow)
├── navmesh_addon/             # same as repo navmesh_addon/
├── navmesh_wrapper/           # same as repo navmesh_wrapper/
└── build_libs.sh              # shell equivalent of build_libs.py
```

## Workflow

### Build and release
```bash
# Local build
python3 build_libs.py

# Package for Blender
python3 package.py

# Create a release tag
git tag v0.1.0
git push origin v0.1.0
# CI builds all platforms and creates a GitHub Release automatically
```

### CI/CD
- **Trigger**: pushing a `v*` tag (e.g., `v0.1.0`)
- **Builds**: Linux (.so), macOS (.dylib), Windows (.dll)
- **Release**: Creates GitHub Release with add-on .zip + per-platform library files
- Users install the add-on .zip, then manually copy their platform's library into `navmesh_addon/libs/`

## Architecture

```
recast-blender/
├── recastnavigation/          # upstream Recast/Detour C++ library (clone)
│   ├── Recast/Include/        # Recast.h, RecastAlloc.h — API headers
│   ├── Detour/Include/        # DetourNavMesh.h, DetourNavMeshBuilder.h, DetourAlloc.h
│   ├── Recast/Source/         # Recast.cpp, RecastRasterization.cpp, etc.
│   └── Detour/Source/         # DetourNavMeshBuilder.cpp, etc.
├── navmesh_wrapper/
│   └── wrapper.cpp            # C-linkage adapter: wraps all C++ functions in extern "C"
├── navmesh_addon/             # Blender add-on directory
│   ├── __init__.py            # bl_info, register/unregister, library loading
│   ├── build.py               # ctypes structs + full Recast→Detour pipeline
│   ├── operators.py           # NAVMESH_OT_Rebuild operator
│   ├── panels.py              # NAVMESH_PT_Main panel
│   └── libs/                  # compiled .so files (output of build_libs.sh)
│       ├── libRecast.so       # Recast shared library
│       ├── libRecast.so.1 →   # symlink for SONAME resolution
│       ├── libDetour.so       # Detour shared library
│       ├── libDetour.so.1 →   # symlink for SONAME resolution
│       └── libNavMeshWrapper.so  # C-linkage wrapper (links Recast+Detour)
└── build_libs.sh              # one-shot build script
```

### Data flow
```
Selected Blender mesh objects
  → extract_geometry(): world-space verts + tri indices
  → build_navmesh(verts, tris, rcConfig)
    → Recast pipeline: classify → rasterize → filter → compact → regions → contours → polymesh → detail
    → dtCreateNavMeshData → raw binary tile (248 bytes for a flat 10×10 plane)
    → parse_tile_binary() → detail triangle verts + indices
  → bpy.data.meshes.new() → navmesh object in scene
  → assign NavMesh_Material (semi-transparent green, BLEND mode)
```

## Build

```bash
# One-shot: build Recast.so, Detour.so, and wrapper, then copy to libs/
./build_libs.sh

# Manual steps:
cd recastnavigation
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
  -DRECASTNAVIGATION_DEMO=OFF -DRECASTNAVIGATION_TESTS=OFF \
  -DRECASTNAVIGATION_EXAMPLES=OFF
cmake --build build --target Recast Detour --parallel

# Copy built libs (note: CMake creates versioned .so files)
cp build/Recast/libRecast.so.1.6.0 ../navmesh_addon/libs/libRecast.so
cp build/Detour/libDetour.so.1.6.0 ../navmesh_addon/libs/libDetour.so

# Build C-linkage wrapper
g++ -shared -fPIC -O2 \
  -I recastnavigation/Recast/Include \
  -I recastnavigation/Detour/Include \
  -o navmesh_addon/libs/libNavMeshWrapper.so \
  navmesh_wrapper/wrapper.cpp \
  -L navmesh_addon/libs -lRecast -lDetour \
  -Wl,-rpath,'$ORIGIN'

# Create SONAME symlinks (required: DT_NEEDED entries are libRecast.so.1, libDetour.so.1)
ln -sf libRecast.so navmesh_addon/libs/libRecast.so.1
ln -sf libDetour.so navmesh_addon/libs/libDetour.so.1
```

### Build caveats
- The CMakeLists uses `add_library(Recast)` without STATIC/SHARED keyword — `BUILD_SHARED_LIBS=ON` works.
- Output files are versioned (`libRecast.so.1.6.0`), not plain `.so`.
- SONAME embedded in libraries is `libRecast.so.1` / `libDetour.so.1` — need symlinks.
- Compiler flags: `-fno-rtti -fno-exceptions` (no RTTI, exceptions disabled).
- Assertions disabled in Release via `RC_DISABLE_ASSERTS` / `RECASTNAVIGATION_ENABLE_ASSERTS=OFF`.

## Verified struct sizes and layouts

Use `nm`-based test to get exact C++ sizes:

```bash
# Quick sizeof check
cat > /tmp/check.cpp << 'EOF'
#include <cstdio>
#include "DetourNavMesh.h"
#include "DetourNavMeshBuilder.h"
#include "Recast.h"
int main() {
    printf("dtMeshHeader: %zu\n", sizeof(dtMeshHeader));
    printf("dtPoly: %zu\n", sizeof(dtPoly));
    printf("dtLink: %zu\n", sizeof(dtLink));
    printf("dtPolyDetail: %zu\n", sizeof(dtPolyDetail));
    printf("dtBVNode: %zu\n", sizeof(dtBVNode));
    printf("rcConfig: %zu\n", sizeof(rcConfig));
    printf("rcPolyMesh: %zu\n", sizeof(rcPolyMesh));
    printf("rcPolyMeshDetail: %zu\n", sizeof(rcPolyMeshDetail));
    printf("dtNavMeshCreateParams: %zu\n", sizeof(dtNavMeshCreateParams));
    return 0;
}
EOF
g++ -I recastnavigation/Recast/Include -I recastnavigation/Detour/Include \
  /tmp/check.cpp -o /tmp/check && /tmp/check
```

### Verified sizes (x86_64 Linux, GCC)
| Struct | C++ sizeof | ctypes sizeof | Notes |
|--------|-----------|--------------|-------|
| `rcConfig` | 92 | 92 | 11 ints + 12 floats |
| `rcPolyMesh` | 96 | 96 | 5 ptrs + 4 ints + 6 floats + 2 floats + int + float |
| `rcPolyMeshDetail` | 40 | 40 | 3 ptrs + 3 ints; padded to 8-byte alignment |
| `dtMeshHeader` | **100** | — | NOT 80! 16 ints + 10 floats = 104? No: 16×4 + 3×4(walkable) + 6×4(bmin/bmax) + 1×4(bvQuant) = 100 |
| `dtPoly` | 32 | — | uint + 6×ushort + 6×ushort + ushort + uchar + uchar |
| `dtLink` | **12** | — | NOT 16! uint + uint + 4×uchar |
| `dtPolyDetail` | **12** | — | NOT 10! uint + uint + uchar + uchar + 2 bytes padding |
| `dtBVNode` | 16 | — | 3×ushort + 3×ushort + int |
| `dtNavMeshCreateParams` | 208 | 208 | complex struct with many pointer fields |

### dtMeshHeader field offsets (100 bytes total)
```
Offset  0: int magic          Offset 60: float walkableHeight
Offset  4: int version        Offset 64: float walkableRadius
Offset  8: int x              Offset 68: float walkableClimb
Offset 12: int y              Offset 72: float bmin[0]
Offset 16: int layer          Offset 76: float bmin[1]
Offset 20: uint userId        Offset 80: float bmin[2]
Offset 24: int polyCount      Offset 84: float bmax[0]
Offset 28: int vertCount      Offset 88: float bmax[1]
Offset 32: int maxLinkCount   Offset 92: float bmax[2]
Offset 36: int detailMeshCount Offset 96: float bvQuantFactor
Offset 40: int detailVertCount
Offset 44: int detailTriCount
Offset 48: int bvNodeCount
Offset 52: int offMeshConCount
Offset 56: int offMeshBase
```

## Detour tile binary layout

The binary output from `dtCreateNavMeshData` is laid out in this exact order:

```
Offset 0:                              dtMeshHeader (100 bytes)
Offset 100:                            float verts[3 * vertCount]      ← VERTICES COME FIRST
Offset 100 + 12*vertCount:             dtPoly[polyCount]               ← polys AFTER verts
Offset + 32*polyCount:                 dtLink[maxLinkCount]
Offset + 12*maxLinkCount:              dtPolyDetail[detailMeshCount]
Offset + 12*detailMeshCount:           float detailVerts[3*detailVertCount]
Offset + 12*detailVertCount:           uchar detailTris[4*detailTriCount]
Offset + 4*detailTriCount:             dtBVNode[bvNodeCount]
Offset + 16*bvNodeCount:               dtOffMeshConnection[offMeshConCount]
```

**Critical: verts come BEFORE polys, not after.** This was confirmed by reading the `dtCreateNavMeshData` source in `DetourNavMeshBuilder.cpp` (line ~427-451). The order is: `headerSize + vertsSize + polysSize + linksSize + ...`

### dtPolyDetail extra vertices
Each poly has `dtPolyDetail` with `vertCount` extra detail vertices. The total vertex count for a single poly's detail mesh is `poly.vertCount + detail.vertCount`. Detail vertex indices 0..poly.vertCount-1 refer to the poly's corner vertices; indices poly.vertCount.. refer to extra detail vertices at `detailVerts[vertBase + k]`.

## Key pitfalls found and resolved

### 1. C++ name mangling — all symbols are mangled
**Problem**: All Recast/Detour functions use C++ linkage (no `extern "C"` in headers). `ctypes.CDLL` can't resolve mangled names like `_Z18rcAllocHeightfieldv`.

**Solution**: Created `navmesh_wrapper/wrapper.cpp` — a single C++ file that includes the Recast/Detour headers, wraps every needed function in `extern "C"`, and compiles to `libNavMeshWrapper.so`. This wrapper links against `libRecast.so` and `libDetour.so`.

**Key wrapper pattern** for functions taking C++ references (which are pointers at the ABI level):
```cpp
extern "C" {
int NM_CreateHeightfield(void* ctx, void* hf, int w, int h, ...) {
    return rcCreateHeightfield(
        static_cast<rcContext*>(ctx),
        *static_cast<rcHeightfield*>(hf),  // deref pointer → reference
        w, h, ...) ? 1 : 0;
}
}
```

### 2. ctypes restype defaults to c_int (32-bit), truncating 64-bit pointers
**Problem**: Any function returning a pointer MUST have `restype = c_void_p`. Without it, ctypes defaults to `c_int` (32 bits), truncating 64-bit pointers on x86_64. Symptom: segfault at an address that looks like truncated high bits.

**Solution**: Explicitly set `restype` and `argtypes` for EVERY wrapper function:
```python
lib.NM_NewContext.restype = c_void_p
lib.NM_NewContext.argtypes = [c_int]
lib.NM_DeleteContext.argtypes = [c_void_p]
lib.NM_AllocHeightfield.restype = c_void_p
# ... etc for all functions
```

### 3. NULL context crashes some Recast functions
**Problem**: Passing `c_void_p(0)` (null pointer) for the `rcContext*` parameter crashes in functions that use `rcScopedTimer`, because the timer tries to call virtual methods on the context without proper null checks in all code paths.

**Solution**: Always create a real context:
```python
ctx = lib.NM_NewContext(0)  # 0 = logging and timers disabled
# ... use ctx in all pipeline calls ... 
lib.NM_DeleteContext(ctx)
```

### 4. Flat geometry has zero span height — walkable check fails
**Problem**: For a flat plane at Y=0, bmin[1]==bmax[1]==0, so all spans have height 0. The walkable height check (`smax - smin >= walkableHeight`) fails for every span → 0 polys.

**Solution**: Pad `bmax[1]` by `walkableHeight * ch` so spans have vertical room:
```python
cfg.bmax[1] = bmax[1] + cfg.walkableHeight * cfg.ch
```

### 5. Tile binary struct sizes were wrong
**Problem**: Assumed `dtLink`=16 bytes (actually 12), `dtPolyDetail`=10 bytes (actually 12), `dtMeshHeader`=80 bytes (actually 100). All subsequent offset calculations were wrong.

**Solution**: Always verify struct sizes against the compiled C++ library. Used a test program to output `sizeof()` for every struct. See "Verified struct sizes" section above.

### 6. Tile binary layout: verts before polys
**Problem**: Assumed polys come before verts in the tile binary. Actually verts come first (confirmed by reading `DetourNavMeshBuilder.cpp`).

**Solution**: Corrected offset calculations in `parse_tile_binary`.

## Debugging techniques

### Verify struct sizes match between C++ and ctypes
```python
from navmesh_addon.build import lib, rcConfig
print(f"C++ sizeof rcConfig: {lib.NM_SizeOfRcConfig()}")
print(f"ctypes sizeof rcConfig: {ctypes.sizeof(rcConfig)}")
```

### Check exported symbols in a .so
```bash
nm -D libNavMeshWrapper.so | grep "^[0-9a-f]* T "  # C-linkage (text) symbols
nm -D libRecast.so | grep "_ZTV"                     # vtable symbols
```

### Check shared library dependencies and rpath
```bash
readelf -d libNavMeshWrapper.so | grep -E "NEEDED|RPATH|RUNPATH"
```

### Debug segfaults with GDB
```bash
gdb -batch -ex "set pagination off" -ex "run" -ex "bt" -ex "frame 0" -ex "info args" \
  --args python3 your_test.py
```

### Hex dump tile binary to verify parser
```python
raw = ctypes.string_at(nav_data, nav_data_size)
for i in range(0, min(200, len(raw)), 16):
    hexpart = binascii.hexlify(raw[i:i+16], ' ').decode()
    print(f'{i:04x}: {hexpart}')
```

### Step-through pipeline with flush
```python
print('Step N...', flush=True)
# call function
print('OK', flush=True)
```

## ctypes patterns used

### Struct with mixed int/float fields (packing matches C++)
```python
class rcConfig(ctypes.Structure):
    _fields_ = [
        ("width", c_int),
        ("height", c_int),
        # ...
        ("cs", c_float),
        ("ch", c_float),
        ("bmin", c_float * 3),  # fixed-size array
        # ...
    ]
```

### Casting raw pointer to typed struct
```python
pm = ctypes.cast(c_void_p(pm_addr_int), ctypes.POINTER(RCPolyMesh))
print(pm.contents.npolys)
```

### Passing output parameters via byref
```python
gw = c_int(); gh = c_int()
lib.NM_CalcGridSize(bmin, bmax, 0.3, byref(gw), byref(gh))
```

### Creating and passing arrays
```python
va = (c_float * len(verts))(*verts)     # float array from Python list
ta = (c_int * len(tris))(*tris)         # int array
bmin = (c_float * 3)()                  # zero-initialized fixed array
```

## Testing

### Non-Blender pipeline test (runs in plain Python)
```bash
timeout 15 python3 -c "
import sys, math
sys.path.insert(0,'.')
from navmesh_addon.build import build_navmesh
verts = [-5,0,-5, 5,0,-5, 5,0,5, -5,0,5]
tris = [0,2,1, 0,3,2]  # proper winding for up-pointing normals
config = {
    'cs':0.3, 'ch':0.2, 'walkableSlopeAngle':45.0,
    'walkableHeight':math.ceil(2.0/0.2), 'walkableClimb':math.floor(0.9/0.2),
    'walkableRadius':math.ceil(0.6/0.3), 'maxEdgeLen':int(12/0.3),
    'maxSimplificationError':1.3, 'minRegionArea':64, 'mergeRegionArea':400,
    'maxVertsPerPoly':6, 'detailSampleDist':6.0, 'detailSampleMaxError':1.0,
}
out_verts, out_tris, stats = build_navmesh(verts, tris, config)
print(f'Stats: {stats}')
"
```

### Triangle winding matters
Vertices must be ordered counter-clockwise as seen from above (right-hand rule). Normal should point UP for walkable faces. Wrong winding → normal points down → `rcMarkWalkableTriangles` marks as non-walkable → 0 polys.

## Blender-specific notes

- `bpy`, `bmesh`, `bpy.props` are Blender-internal modules — LSP will report them as unresolvable (expected).
- Property annotations like `cell_size: FloatProperty(...)` produce LSP "Call expression not allowed in type expression" (false positive).
- Relative imports (`from . import build`) work at runtime in Blender but LSP can't validate them.
- The add-on installs to View3D > Sidebar > NavMesh tab.
- Navmesh objects are prefixed `navmesh_` and have custom properties (`navmesh_cs`, `navmesh_poly_count`, etc.).
- Material setup: `diffuse_color = (0.0, 0.8, 0.3, 0.2)` with `blend_method='BLEND'`, `show_wire=True`.

## Build: Combined single-library approach

After discovering C++ name mangling and glibc version issues, the build was simplified to a **single combined .so**:

```bash
g++ -shared -fPIC -O2 -ffast-math -ffinite-math-only \
  -I "$RECAST_DIR/Recast/Include" \
  -I "$RECAST_DIR/Detour/Include" \
  -o "$LIBS_DIR/libNavMeshWrapper.so" \
  "$RECAST_DIR/Recast/Source/"*.cpp \
  "$RECAST_DIR/Detour/Source/"*.cpp \
  navmesh_wrapper/wrapper.cpp
```

This avoids:
- Separate libRecast.so / libDetour.so with SONAME dependencies
- Versioned glibc symbol issues (`sqrtf@GLIBC_2.43` on newer systems)
- Complex rpath setup

The `-ffast-math -ffinite-math-only` flags inline `sqrtf` as the CPU `sqrtss` instruction, bypassing the libm versioned symbol.

## Blender coordinate system

Recast uses X-right, Y-up, Z-forward. Blender uses X-right, Y-forward, Z-up:
- Recast Y (up) = Blender Z (up)
- Recast Z (forward) = Blender Y (forward)

### Vertex extraction (Blender → Recast)
```python
wc = obj.matrix_world @ v.co
all_verts.extend([wc.x, wc.z, wc.y])  # swap Y and Z
```

### Output mesh (Recast → Blender)  
```python
# Swap back: Recast (x, y=up, z) → Blender (x, z=up, y)
(out_verts[i], out_verts[i+2], out_verts[i+1])
```

### Triangle winding
The Y/Z coordinate swap inverts triangle winding. **Must reverse vertex order**:
```python
tri.vertices[0] + v_base,
tri.vertices[2] + v_base,  # swapped
tri.vertices[1] + v_base,  # swapped
```

## Blender 5.1 API notes

- `obj.evaluated_get(depsgraph)` returns an **Object**, not a Mesh. Access mesh via `.data`.
- `mesh.copy()` and `mesh.transform()` are removed in Blender 4.2+. Apply `matrix_world` manually to vertices.
- No `mesh.free()` or `bpy.data.meshes.remove()` needed when using `.data` directly (no copy made).
- `mesh.calc_loop_triangles()` still works.
- `obj["key"]` for custom properties.

## Release checklist

1. Bump version in `navmesh_addon/__init__.py` (`bl_info["version"]`)
2. Commit: `git commit -m "Release vX.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Push: `git push origin main && git push origin vX.Y.Z`
5. CI builds all platforms automatically and creates a GitHub Release
6. Edit the release notes on GitHub if needed

### To verify a release locally
```bash
python3 build_libs.py           # builds libNavMeshWrapper.so
python3 package.py --version X.Y.Z  # creates navmesh_addon-X.Y.Z.zip
```
