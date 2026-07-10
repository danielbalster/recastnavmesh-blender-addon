import bpy
import math
from bpy.props import (
    FloatProperty,
    IntProperty,
)

from . import build
from .panels import _get_or_create_material


class NAVMESH_OT_Rebuild(bpy.types.Operator):
    bl_idname = "navmesh.rebuild"
    bl_label = "Rebuild NavMesh"
    bl_description = "Generate a navigation mesh from selected geometry"
    bl_options = {"REGISTER", "UNDO"}

    cell_size: FloatProperty(
        name="Cell Size",
        description="XZ-plane cell size in world units",
        default=0.3,
        min=0.01,
        soft_max=2.0,
    )
    cell_height: FloatProperty(
        name="Cell Height",
        description="Y-axis cell size in world units",
        default=0.2,
        min=0.01,
        soft_max=1.0,
    )
    agent_height: FloatProperty(
        name="Agent Height",
        description="Minimum floor-to-ceiling height for walkable areas",
        default=2.0,
        min=0.1,
        soft_max=5.0,
    )
    agent_radius: FloatProperty(
        name="Agent Radius",
        description="Erosion radius around obstacles",
        default=0.6,
        min=0.0,
        soft_max=2.0,
    )
    agent_max_climb: FloatProperty(
        name="Max Climb",
        description="Maximum traversable step height",
        default=0.9,
        min=0.0,
        soft_max=2.0,
    )
    agent_max_slope: FloatProperty(
        name="Max Slope",
        description="Maximum walkable slope angle in degrees",
        default=45.0,
        min=0.0,
        max=89.0,
    )

    def _collect_mesh_data(self, context):
        all_verts = []
        all_tris = []

        depsgraph = context.evaluated_depsgraph_get()

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.data
            if mesh is None or len(mesh.vertices) == 0:
                continue

            v_base = len(all_verts) // 3

            mat = obj.matrix_world
            for v in mesh.vertices:
                wc = mat @ v.co
                all_verts.extend([wc.x, wc.z, wc.y])

            mesh.calc_loop_triangles()
            for tri in mesh.loop_triangles:
                all_tris.extend(
                    [
                        tri.vertices[0] + v_base,
                        tri.vertices[2] + v_base,
                        tri.vertices[1] + v_base,
                    ]
                )

        return all_verts, all_tris

    def execute(self, context):
        selected = [o for o in context.selected_objects if o.type == "MESH"]
        if not selected:
            self.report({"ERROR"}, "No mesh objects selected")
            return {"CANCELLED"}

        verts, tris = self._collect_mesh_data(context)

        if len(verts) < 9 or len(tris) < 3:
            self.report({"ERROR"}, "Selected meshes have insufficient geometry")
            return {"CANCELLED"}

        ch = max(self.cell_height, 0.01)
        cs = max(self.cell_size, 0.01)

        config = {
            "cs": cs,
            "ch": ch,
            "walkableSlopeAngle": self.agent_max_slope,
            "walkableHeight": math.ceil(self.agent_height / ch),
            "walkableClimb": math.floor(self.agent_max_climb / ch),
            "walkableRadius": math.ceil(self.agent_radius / cs),
            "maxEdgeLen": max(1, int(12.0 / cs)),
            "maxSimplificationError": 1.3,
            "minRegionArea": 64,
            "mergeRegionArea": 400,
            "maxVertsPerPoly": 6,
            "detailSampleDist": 6.0,
            "detailSampleMaxError": 1.0,
            "borderSize": 0,
            "tileSize": 0,
        }

        try:
            out_verts, out_tris, stats = build.build_navmesh(verts, tris, config)
        except OSError as e:
            self.report({"ERROR"}, f"Library error: {e}")
            return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Build failed: {e}")
            return {"CANCELLED"}

        if stats["polyCount"] == 0:
            self.report({"WARNING"}, "No walkable area found")
            return {"CANCELLED"}

        source_name = selected[0].name if len(selected) == 1 else "multi"
        nm_name = f"navmesh_{source_name}"

        existing = bpy.data.objects.get(nm_name)
        if existing is not None:
            md = existing.data
            bpy.data.objects.remove(existing, do_unlink=True)
            if md and md.users == 0:
                bpy.data.meshes.remove(md)

        new_mesh = bpy.data.meshes.new(nm_name)
        new_mesh.from_pydata(
            [
                (out_verts[i], out_verts[i + 2], out_verts[i + 1])
                for i in range(0, len(out_verts), 3)
            ],
            [],
            [out_tris[i : i + 3] for i in range(0, len(out_tris), 3)],
        )
        new_mesh.update()

        nm_obj = bpy.data.objects.new(nm_name, new_mesh)
        context.collection.objects.link(nm_obj)

        mat = _get_or_create_material()
        if mat and nm_obj.data.materials:
            nm_obj.data.materials[0] = mat
        elif mat:
            nm_obj.data.materials.append(mat)

        nm_obj.show_wire = True
        nm_obj.show_all_edges = True

        nm_obj["navmesh_cs"] = cs
        nm_obj["navmesh_ch"] = ch
        nm_obj["navmesh_agent_height"] = self.agent_height
        nm_obj["navmesh_agent_radius"] = self.agent_radius
        nm_obj["navmesh_agent_max_climb"] = self.agent_max_climb
        nm_obj["navmesh_agent_max_slope"] = self.agent_max_slope
        nm_obj["navmesh_poly_count"] = stats["polyCount"]
        nm_obj["navmesh_vert_count"] = stats["vertCount"]
        nm_obj["navmesh_tri_count"] = stats["triCount"]
        nm_obj["navmesh_build_time"] = stats["buildTime"]

        bpy.ops.object.select_all(action="DESELECT")
        nm_obj.select_set(True)
        context.view_layer.objects.active = nm_obj

        self.report(
            {"INFO"},
            f"NavMesh built: {stats['triCount']} tris, {stats['polyCount']} polys, {stats['buildTime']:.2f}s",
        )
        return {"FINISHED"}


classes = [NAVMESH_OT_Rebuild]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
