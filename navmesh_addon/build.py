import ctypes
import struct
import time
from ctypes import (
    POINTER,
    byref,
    c_bool,
    c_float,
    c_int,
    c_ubyte,
    c_uint,
    c_ushort,
    c_void_p,
    cast,
)

from . import get_lib_wrapper

lib = get_lib_wrapper()


class rcConfig(ctypes.Structure):
    _fields_ = [
        ("width", c_int),
        ("height", c_int),
        ("tileSize", c_int),
        ("borderSize", c_int),
        ("cs", c_float),
        ("ch", c_float),
        ("bmin", c_float * 3),
        ("bmax", c_float * 3),
        ("walkableSlopeAngle", c_float),
        ("walkableHeight", c_int),
        ("walkableClimb", c_int),
        ("walkableRadius", c_int),
        ("maxEdgeLen", c_int),
        ("maxSimplificationError", c_float),
        ("minRegionArea", c_int),
        ("mergeRegionArea", c_int),
        ("maxVertsPerPoly", c_int),
        ("detailSampleDist", c_float),
        ("detailSampleMaxError", c_float),
    ]


class RCPolyMesh(ctypes.Structure):
    _fields_ = [
        ("verts", c_void_p),
        ("polys", c_void_p),
        ("regs", c_void_p),
        ("flags", c_void_p),
        ("areas", c_void_p),
        ("nverts", c_int),
        ("npolys", c_int),
        ("maxpolys", c_int),
        ("nvp", c_int),
        ("bmin", c_float * 3),
        ("bmax", c_float * 3),
        ("cs", c_float),
        ("ch", c_float),
        ("borderSize", c_int),
        ("maxEdgeError", c_float),
    ]


class RCPolyMeshDetail(ctypes.Structure):
    _fields_ = [
        ("meshes", c_void_p),
        ("verts", c_void_p),
        ("tris", c_void_p),
        ("nmeshes", c_int),
        ("nverts", c_int),
        ("ntris", c_int),
    ]


class dtNavMeshCreateParams(ctypes.Structure):
    _fields_ = [
        ("verts", c_void_p),
        ("vertCount", c_int),
        ("polys", c_void_p),
        ("polyFlags", c_void_p),
        ("polyAreas", c_void_p),
        ("polyCount", c_int),
        ("nvp", c_int),
        ("detailMeshes", c_void_p),
        ("detailVerts", c_void_p),
        ("detailVertsCount", c_int),
        ("detailTris", c_void_p),
        ("detailTriCount", c_int),
        ("offMeshConVerts", c_void_p),
        ("offMeshConRad", c_void_p),
        ("offMeshConFlags", c_void_p),
        ("offMeshConAreas", c_void_p),
        ("offMeshConDir", c_void_p),
        ("offMeshConUserID", c_void_p),
        ("offMeshConCount", c_int),
        ("userId", c_uint),
        ("tileX", c_int),
        ("tileY", c_int),
        ("tileLayer", c_int),
        ("bmin", c_float * 3),
        ("bmax", c_float * 3),
        ("walkableHeight", c_float),
        ("walkableRadius", c_float),
        ("walkableClimb", c_float),
        ("cs", c_float),
        ("ch", c_float),
        ("buildBvTree", c_bool),
    ]


RC_CONTOUR_TESS_WALL_EDGES = 0x01


def _setup():
    lib.NM_NewContext.restype = c_void_p
    lib.NM_NewContext.argtypes = [c_int]
    lib.NM_DeleteContext.argtypes = [c_void_p]

    lib.NM_AllocHeightfield.restype = c_void_p
    lib.NM_FreeHeightfield.argtypes = [c_void_p]

    lib.NM_AllocCompactHeightfield.restype = c_void_p
    lib.NM_FreeCompactHeightfield.argtypes = [c_void_p]

    lib.NM_AllocContourSet.restype = c_void_p
    lib.NM_FreeContourSet.argtypes = [c_void_p]

    lib.NM_AllocPolyMesh.restype = c_void_p
    lib.NM_FreePolyMesh.argtypes = [c_void_p]

    lib.NM_AllocPolyMeshDetail.restype = c_void_p
    lib.NM_FreePolyMeshDetail.argtypes = [c_void_p]

    lib.NM_CalcBounds.argtypes = [
        POINTER(c_float),
        c_int,
        POINTER(c_float),
        POINTER(c_float),
    ]
    lib.NM_CalcBounds.restype = None

    lib.NM_CalcGridSize.argtypes = [
        POINTER(c_float),
        POINTER(c_float),
        c_float,
        POINTER(c_int),
        POINTER(c_int),
    ]
    lib.NM_CalcGridSize.restype = None

    lib.NM_CreateHeightfield.argtypes = [
        c_void_p,
        c_void_p,
        c_int,
        c_int,
        POINTER(c_float),
        POINTER(c_float),
        c_float,
        c_float,
    ]
    lib.NM_CreateHeightfield.restype = c_int

    lib.NM_MarkWalkableTriangles.argtypes = [
        c_void_p,
        c_float,
        POINTER(c_float),
        c_int,
        POINTER(c_int),
        c_int,
        POINTER(c_ubyte),
    ]
    lib.NM_MarkWalkableTriangles.restype = None

    lib.NM_RasterizeTriangles.argtypes = [
        c_void_p,
        POINTER(c_float),
        c_int,
        POINTER(c_int),
        POINTER(c_ubyte),
        c_int,
        c_void_p,
        c_int,
    ]
    lib.NM_RasterizeTriangles.restype = c_int

    lib.NM_FilterLowHangingWalkableObstacles.argtypes = [
        c_void_p,
        c_int,
        c_void_p,
    ]
    lib.NM_FilterLowHangingWalkableObstacles.restype = None

    lib.NM_FilterLedgeSpans.argtypes = [
        c_void_p,
        c_int,
        c_int,
        c_void_p,
    ]
    lib.NM_FilterLedgeSpans.restype = None

    lib.NM_FilterWalkableLowHeightSpans.argtypes = [
        c_void_p,
        c_int,
        c_void_p,
    ]
    lib.NM_FilterWalkableLowHeightSpans.restype = None

    lib.NM_BuildCompactHeightfield.argtypes = [
        c_void_p,
        c_int,
        c_int,
        c_void_p,
        c_void_p,
    ]
    lib.NM_BuildCompactHeightfield.restype = c_int

    lib.NM_ErodeWalkableArea.argtypes = [
        c_void_p,
        c_int,
        c_void_p,
    ]
    lib.NM_ErodeWalkableArea.restype = c_int

    lib.NM_BuildDistanceField.argtypes = [c_void_p, c_void_p]
    lib.NM_BuildDistanceField.restype = c_int

    lib.NM_BuildRegions.argtypes = [
        c_void_p,
        c_void_p,
        c_int,
        c_int,
        c_int,
    ]
    lib.NM_BuildRegions.restype = c_int

    lib.NM_BuildContours.argtypes = [
        c_void_p,
        c_void_p,
        c_float,
        c_int,
        c_void_p,
        c_int,
    ]
    lib.NM_BuildContours.restype = c_int

    lib.NM_BuildPolyMesh.argtypes = [
        c_void_p,
        c_void_p,
        c_int,
        c_void_p,
    ]
    lib.NM_BuildPolyMesh.restype = c_int

    lib.NM_BuildPolyMeshDetail.argtypes = [
        c_void_p,
        c_void_p,
        c_void_p,
        c_float,
        c_float,
        c_void_p,
    ]
    lib.NM_BuildPolyMeshDetail.restype = c_int

    lib.NM_Free.argtypes = [c_void_p]
    lib.NM_Free.restype = None

    lib.NM_CreateNavMeshData.argtypes = [
        POINTER(dtNavMeshCreateParams),
        POINTER(c_void_p),
        POINTER(c_int),
    ]
    lib.NM_CreateNavMeshData.restype = c_int

    lib.NM_DtFree.argtypes = [c_void_p]
    lib.NM_DtFree.restype = None

    lib.NM_SizeOfRcConfig.restype = c_int
    lib.NM_SizeOfDtNavMeshCreateParams.restype = c_int
    lib.NM_SizeOfRcPolyMesh.restype = c_int
    lib.NM_SizeOfRcPolyMeshDetail.restype = c_int


_setup()


def _cast_pm(pm_addr):
    if pm_addr is None:
        return None
    if isinstance(pm_addr, int):
        pv = pm_addr
    else:
        pv = pm_addr.value or 0
    return cast(c_void_p(pv), POINTER(RCPolyMesh))


def _cast_dm(dm_addr):
    if dm_addr is None:
        return None
    if isinstance(dm_addr, int):
        pv = dm_addr
    else:
        pv = dm_addr.value or 0
    return cast(c_void_p(pv), POINTER(RCPolyMeshDetail))


def parse_tile_binary(nav_data, nav_data_size):
    HDR = 100
    if nav_data_size < HDR:
        raise RuntimeError("NavMesh data too small for header")

    raw = ctypes.string_at(nav_data, nav_data_size)

    def _i(off):
        return struct.unpack_from("i", raw, off)[0]

    def _f(off):
        return struct.unpack_from("f", raw, off)[0]

    def _H(off):
        return struct.unpack_from("H", raw, off)[0]

    def _B(off):
        return struct.unpack_from("B", raw, off)[0]

    poly_count = _i(24)
    vert_count = _i(28)
    max_link_count = _i(32)
    detail_mesh_count = _i(36)
    detail_vert_count = _i(40)
    detail_tri_count = _i(44)

    poly_sz = poly_count * 32
    vert_sz = vert_count * 12
    link_sz = max_link_count * 12
    dm_sz = detail_mesh_count * 12
    dv_sz = detail_vert_count * 12
    dt_sz = detail_tri_count * 4

    off_vert = HDR
    off_poly = off_vert + vert_sz
    off_link = off_poly + poly_sz
    off_dm = off_link + link_sz
    off_dv = off_dm + dm_sz
    off_dt = off_dv + dv_sz

    out_verts = []
    out_tris = []

    for pi in range(poly_count):
        po = off_poly + pi * 32
        pv_count = _B(po + 30)
        if pv_count < 3:
            continue

        pv = []
        for j in range(pv_count):
            vi = _H(po + 4 + j * 2)
            x = _f(off_vert + vi * 12)
            y = _f(off_vert + vi * 12 + 4)
            z = _f(off_vert + vi * 12 + 8)
            pv.append((x, y, z))

        if pi < detail_mesh_count:
            dmo = off_dm + pi * 12
            vb = struct.unpack_from("I", raw, dmo)[0]
            tb = struct.unpack_from("I", raw, dmo + 4)[0]
            dvc = _B(dmo + 8)
            dtc = _B(dmo + 9)

            all_v = list(pv)
            for k in range(dvc):
                dvx = _f(off_dv + (vb + k) * 12)
                dvy = _f(off_dv + (vb + k) * 12 + 4)
                dvz = _f(off_dv + (vb + k) * 12 + 8)
                all_v.append((dvx, dvy, dvz))

            total_v = pv_count + dvc

            if dtc > 0:
                for t in range(dtc):
                    dto = off_dt + (tb + t) * 4
                    a = _B(dto)
                    b = _B(dto + 1)
                    c = _B(dto + 2)
                    if a < total_v and b < total_v and c < total_v:
                        idx = len(out_verts)
                        out_verts.append(all_v[a])
                        out_verts.append(all_v[b])
                        out_verts.append(all_v[c])
                        out_tris.append((idx, idx + 1, idx + 2))
            else:
                for j in range(1, pv_count - 1):
                    idx = len(out_verts)
                    out_verts.append(pv[0])
                    out_verts.append(pv[j])
                    out_verts.append(pv[j + 1])
                    out_tris.append((idx, idx + 1, idx + 2))
        else:
            for j in range(1, pv_count - 1):
                idx = len(out_verts)
                out_verts.append(pv[0])
                out_verts.append(pv[j])
                out_verts.append(pv[j + 1])
                out_tris.append((idx, idx + 1, idx + 2))

    flat_v = []
    for v in out_verts:
        flat_v.extend(v)
    flat_t = []
    for t in out_tris:
        flat_t.extend(t)

    return (
        flat_v,
        flat_t,
        {
            "polyCount": poly_count,
            "vertCount": len(out_verts),
            "triCount": len(out_tris),
        },
    )


def build_navmesh(vertices, triangles, config):
    t0 = time.time()

    nv = len(vertices) // 3
    nt = len(triangles) // 3

    if nv < 3 or nt < 1:
        raise ValueError("Insufficient geometry")

    ctx = lib.NM_NewContext(0)
    if not ctx:
        raise MemoryError("NM_NewContext failed")

    try:
        return _build_navmesh_impl(ctx, vertices, triangles, config, t0, nv, nt)
    finally:
        lib.NM_DeleteContext(ctx)


def _build_navmesh_impl(ctx, vertices, triangles, config, t0, nv, nt):

    va = (c_float * len(vertices))(*vertices)
    ta = (c_int * len(triangles))(*triangles)

    bmin = (c_float * 3)()
    bmax = (c_float * 3)()

    lib.NM_CalcBounds(va, nv, bmin, bmax)

    cfg = rcConfig()
    cfg.cs = max(config.get("cs", 0.3), 0.01)
    cfg.ch = max(config.get("ch", 0.2), 0.01)
    cfg.walkableSlopeAngle = config.get("walkableSlopeAngle", 45.0)
    cfg.walkableHeight = config.get("walkableHeight", 10)
    cfg.walkableClimb = config.get("walkableClimb", 4)
    cfg.walkableRadius = config.get("walkableRadius", 2)
    cfg.maxEdgeLen = config.get("maxEdgeLen", 40)
    cfg.maxSimplificationError = config.get("maxSimplificationError", 1.3)
    cfg.minRegionArea = config.get("minRegionArea", 64)
    cfg.mergeRegionArea = config.get("mergeRegionArea", 400)
    cfg.maxVertsPerPoly = config.get("maxVertsPerPoly", 6)
    cfg.detailSampleDist = config.get("detailSampleDist", 6.0)
    cfg.detailSampleMaxError = config.get("detailSampleMaxError", 1.0)
    cfg.borderSize = 0
    cfg.tileSize = 0

    gpad = cfg.borderSize * cfg.cs
    cfg.bmin[0] = bmin[0] - gpad
    cfg.bmin[1] = bmin[1]
    cfg.bmin[2] = bmin[2] - gpad
    cfg.bmax[0] = bmax[0] + gpad
    cfg.bmax[1] = bmax[1] + cfg.walkableHeight * cfg.ch
    cfg.bmax[2] = bmax[2] + gpad

    gw = c_int()
    gh = c_int()
    lib.NM_CalcGridSize(bmin, bmax, cfg.cs, byref(gw), byref(gh))
    cfg.width = gw.value
    cfg.height = gh.value

    ta_areas = (c_ubyte * nt)()
    lib.NM_MarkWalkableTriangles(
        ctx,
        cfg.walkableSlopeAngle,
        va,
        nv,
        ta,
        nt,
        ta_areas,
    )

    hf = lib.NM_AllocHeightfield()
    if not hf:
        raise MemoryError("NM_AllocHeightfield failed")

    try:
        ok = lib.NM_CreateHeightfield(
            ctx,
            hf,
            cfg.width,
            cfg.height,
            cfg.bmin,
            cfg.bmax,
            cfg.cs,
            cfg.ch,
        )
        if not ok:
            raise RuntimeError("NM_CreateHeightfield failed")

        ok = lib.NM_RasterizeTriangles(
            ctx,
            va,
            nv,
            ta,
            ta_areas,
            nt,
            hf,
            0,
        )
        if not ok:
            raise RuntimeError("NM_RasterizeTriangles failed")

        lib.NM_FilterLowHangingWalkableObstacles(ctx, cfg.walkableClimb, hf)
        lib.NM_FilterLedgeSpans(ctx, cfg.walkableHeight, cfg.walkableClimb, hf)
        lib.NM_FilterWalkableLowHeightSpans(ctx, cfg.walkableHeight, hf)

        chf = lib.NM_AllocCompactHeightfield()
        if not chf:
            raise MemoryError("NM_AllocCompactHeightfield failed")

        try:
            ok = lib.NM_BuildCompactHeightfield(
                ctx,
                cfg.walkableHeight,
                cfg.walkableClimb,
                hf,
                chf,
            )
            if not ok:
                raise RuntimeError("NM_BuildCompactHeightfield failed")

            ok = lib.NM_ErodeWalkableArea(ctx, cfg.walkableRadius, chf)
            if not ok:
                raise RuntimeError("NM_ErodeWalkableArea failed")

            ok = lib.NM_BuildDistanceField(ctx, chf)
            if not ok:
                raise RuntimeError("NM_BuildDistanceField failed")

            ok = lib.NM_BuildRegions(
                ctx,
                chf,
                cfg.borderSize,
                cfg.minRegionArea,
                cfg.mergeRegionArea,
            )
            if not ok:
                raise RuntimeError("NM_BuildRegions failed")

            cset = lib.NM_AllocContourSet()
            if not cset:
                raise MemoryError("NM_AllocContourSet failed")

            try:
                ok = lib.NM_BuildContours(
                    ctx,
                    chf,
                    cfg.maxSimplificationError,
                    cfg.maxEdgeLen,
                    cset,
                    RC_CONTOUR_TESS_WALL_EDGES,
                )
                if not ok:
                    raise RuntimeError("NM_BuildContours failed")

                pm_addr = lib.NM_AllocPolyMesh()
                if not pm_addr:
                    raise MemoryError("NM_AllocPolyMesh failed")

                try:
                    ok = lib.NM_BuildPolyMesh(ctx, cset, cfg.maxVertsPerPoly, pm_addr)
                    if not ok:
                        raise RuntimeError("NM_BuildPolyMesh failed")

                    pm = _cast_pm(pm_addr)
                    if pm is None:
                        raise RuntimeError("Failed to cast poly mesh")

                    dm_addr = lib.NM_AllocPolyMeshDetail()
                    if not dm_addr:
                        raise MemoryError("NM_AllocPolyMeshDetail failed")

                    try:
                        ok = lib.NM_BuildPolyMeshDetail(
                            ctx,
                            pm_addr,
                            chf,
                            cfg.detailSampleDist,
                            cfg.detailSampleMaxError,
                            dm_addr,
                        )
                        if not ok:
                            raise RuntimeError("NM_BuildPolyMeshDetail failed")

                        dm = _cast_dm(dm_addr)

                        params = dtNavMeshCreateParams()
                        _fill_navmesh_create_params(params, pm, dm, cfg)

                        nav_data = c_void_p()
                        nav_data_size = c_int()

                        ok = lib.NM_CreateNavMeshData(
                            byref(params),
                            byref(nav_data),
                            byref(nav_data_size),
                        )
                        if not ok:
                            raise RuntimeError("NM_CreateNavMeshData failed")

                        try:
                            fv, ft, stats = parse_tile_binary(
                                nav_data, nav_data_size.value
                            )
                        finally:
                            lib.NM_DtFree(nav_data)

                    finally:
                        lib.NM_FreePolyMeshDetail(dm_addr)

                finally:
                    lib.NM_FreePolyMesh(pm_addr)

            finally:
                lib.NM_FreeContourSet(cset)

        finally:
            lib.NM_FreeCompactHeightfield(chf)

    finally:
        lib.NM_FreeHeightfield(hf)

    elapsed = time.time() - t0
    stats["buildTime"] = elapsed

    return fv, ft, stats


def _fill_navmesh_create_params(params, pm, dm, cfg):
    params.verts = pm.contents.verts
    params.vertCount = pm.contents.nverts
    params.polys = pm.contents.polys
    params.polyFlags = pm.contents.flags
    params.polyAreas = pm.contents.areas
    params.polyCount = pm.contents.npolys
    params.nvp = pm.contents.nvp

    params.detailMeshes = dm.contents.meshes
    params.detailVerts = dm.contents.verts
    params.detailVertsCount = dm.contents.nverts
    params.detailTris = dm.contents.tris
    params.detailTriCount = dm.contents.ntris

    params.offMeshConVerts = None
    params.offMeshConRad = None
    params.offMeshConFlags = None
    params.offMeshConAreas = None
    params.offMeshConDir = None
    params.offMeshConUserID = None
    params.offMeshConCount = 0

    params.userId = 0
    params.tileX = 0
    params.tileY = 0
    params.tileLayer = 0

    cs = cfg.cs
    ch = cfg.ch
    params.bmin[0] = cfg.bmin[0]
    params.bmin[1] = cfg.bmin[1]
    params.bmin[2] = cfg.bmin[2]
    params.bmax[0] = cfg.bmax[0]
    params.bmax[1] = cfg.bmax[1]
    params.bmax[2] = cfg.bmax[2]

    params.walkableHeight = cfg.walkableHeight * ch
    params.walkableRadius = cfg.walkableRadius * cs
    params.walkableClimb = cfg.walkableClimb * ch
    params.cs = cs
    params.ch = ch
    params.buildBvTree = False
