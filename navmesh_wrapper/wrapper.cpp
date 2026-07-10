#include "Recast.h"
#include "RecastAlloc.h"
#include "DetourNavMeshBuilder.h"
#include "DetourAlloc.h"

extern "C" {

void* NM_NewContext(int state) {
    return new rcContext(state != 0);
}

void NM_DeleteContext(void* ctx) {
    delete static_cast<rcContext*>(ctx);
}

void* NM_AllocHeightfield() { return rcAllocHeightfield(); }
void NM_FreeHeightfield(void* hf) { rcFreeHeightField(static_cast<rcHeightfield*>(hf)); }

void* NM_AllocCompactHeightfield() { return rcAllocCompactHeightfield(); }
void NM_FreeCompactHeightfield(void* chf) { rcFreeCompactHeightfield(static_cast<rcCompactHeightfield*>(chf)); }

void* NM_AllocContourSet() { return rcAllocContourSet(); }
void NM_FreeContourSet(void* cs) { rcFreeContourSet(static_cast<rcContourSet*>(cs)); }

void* NM_AllocPolyMesh() { return rcAllocPolyMesh(); }
void NM_FreePolyMesh(void* pm) { rcFreePolyMesh(static_cast<rcPolyMesh*>(pm)); }

void* NM_AllocPolyMeshDetail() { return rcAllocPolyMeshDetail(); }
void NM_FreePolyMeshDetail(void* dm) { rcFreePolyMeshDetail(static_cast<rcPolyMeshDetail*>(dm)); }

void NM_CalcBounds(const float* verts, int nv, float* bmin, float* bmax) {
    rcCalcBounds(verts, nv, bmin, bmax);
}

void NM_CalcGridSize(const float* bmin, const float* bmax, float cs, int* w, int* h) {
    rcCalcGridSize(bmin, bmax, cs, w, h);
}

int NM_CreateHeightfield(void* ctx, void* hf, int w, int h,
                         const float* bmin, const float* bmax, float cs, float ch) {
    return rcCreateHeightfield(static_cast<rcContext*>(ctx),
                               *static_cast<rcHeightfield*>(hf),
                               w, h, bmin, bmax, cs, ch) ? 1 : 0;
}

void NM_MarkWalkableTriangles(void* ctx, float angle,
                              const float* verts, int nv,
                              const int* tris, int nt,
                              unsigned char* areas) {
    rcMarkWalkableTriangles(static_cast<rcContext*>(ctx), angle, verts, nv, tris, nt, areas);
}

int NM_RasterizeTriangles(void* ctx,
                          const float* verts, int nv,
                          const int* tris, const unsigned char* areas, int nt,
                          void* hf, int flagMergeThr) {
    return rcRasterizeTriangles(static_cast<rcContext*>(ctx),
                                verts, nv, tris, areas, nt,
                                *static_cast<rcHeightfield*>(hf),
                                flagMergeThr) ? 1 : 0;
}

void NM_FilterLowHangingWalkableObstacles(void* ctx, int climb, void* hf) {
    rcFilterLowHangingWalkableObstacles(static_cast<rcContext*>(ctx), climb,
                                        *static_cast<rcHeightfield*>(hf));
}

void NM_FilterLedgeSpans(void* ctx, int walkableHeight, int walkableClimb, void* hf) {
    rcFilterLedgeSpans(static_cast<rcContext*>(ctx), walkableHeight, walkableClimb,
                       *static_cast<rcHeightfield*>(hf));
}

void NM_FilterWalkableLowHeightSpans(void* ctx, int walkableHeight, void* hf) {
    rcFilterWalkableLowHeightSpans(static_cast<rcContext*>(ctx), walkableHeight,
                                   *static_cast<rcHeightfield*>(hf));
}

int NM_BuildCompactHeightfield(void* ctx, int walkableHeight, int walkableClimb,
                               void* hf, void* chf) {
    return rcBuildCompactHeightfield(static_cast<rcContext*>(ctx),
                                     walkableHeight, walkableClimb,
                                     *static_cast<const rcHeightfield*>(hf),
                                     *static_cast<rcCompactHeightfield*>(chf)) ? 1 : 0;
}

int NM_ErodeWalkableArea(void* ctx, int radius, void* chf) {
    return rcErodeWalkableArea(static_cast<rcContext*>(ctx), radius,
                               *static_cast<rcCompactHeightfield*>(chf)) ? 1 : 0;
}

int NM_BuildDistanceField(void* ctx, void* chf) {
    return rcBuildDistanceField(static_cast<rcContext*>(ctx),
                                *static_cast<rcCompactHeightfield*>(chf)) ? 1 : 0;
}

int NM_BuildRegions(void* ctx, void* chf, int borderSize, int minRegionArea, int mergeRegionArea) {
    return rcBuildRegions(static_cast<rcContext*>(ctx),
                          *static_cast<rcCompactHeightfield*>(chf),
                          borderSize, minRegionArea, mergeRegionArea) ? 1 : 0;
}

int NM_BuildContours(void* ctx, void* chf, float maxError, int maxEdgeLen,
                     void* cset, int buildFlags) {
    return rcBuildContours(static_cast<rcContext*>(ctx),
                           *static_cast<const rcCompactHeightfield*>(chf),
                           maxError, maxEdgeLen,
                           *static_cast<rcContourSet*>(cset),
                           buildFlags) ? 1 : 0;
}

int NM_BuildPolyMesh(void* ctx, void* cset, int nvp, void* mesh) {
    return rcBuildPolyMesh(static_cast<rcContext*>(ctx),
                           *static_cast<const rcContourSet*>(cset),
                           nvp, *static_cast<rcPolyMesh*>(mesh)) ? 1 : 0;
}

int NM_BuildPolyMeshDetail(void* ctx, void* mesh, void* chf,
                           float sampleDist, float sampleMaxError, void* dmesh) {
    return rcBuildPolyMeshDetail(static_cast<rcContext*>(ctx),
                                 *static_cast<const rcPolyMesh*>(mesh),
                                 *static_cast<const rcCompactHeightfield*>(chf),
                                 sampleDist, sampleMaxError,
                                 *static_cast<rcPolyMeshDetail*>(dmesh)) ? 1 : 0;
}

void NM_Free(void* ptr) {
    rcFree(ptr);
}

int NM_CreateNavMeshData(dtNavMeshCreateParams* params,
                         unsigned char** outData, int* outDataSize) {
    return dtCreateNavMeshData(params, outData, outDataSize) ? 1 : 0;
}

void NM_DtFree(void* ptr) {
    dtFree(ptr);
}

int NM_SizeOfRcConfig() { return (int)sizeof(rcConfig); }
int NM_SizeOfDtNavMeshCreateParams() { return (int)sizeof(dtNavMeshCreateParams); }
int NM_SizeOfRcPolyMesh() { return (int)sizeof(rcPolyMesh); }
int NM_SizeOfRcPolyMeshDetail() { return (int)sizeof(rcPolyMeshDetail); }

}
