import bpy
import math

from . import build
from .panels import _get_or_create_material


def _resolve_source_objects(context):
    sel = list(context.selected_objects)
    navmesh_obj = None
    for obj in sel:
        if "navmesh_cs" in obj:
            navmesh_obj = obj
            break

    has_geometry = any(o.type == "MESH" and "navmesh_cs" not in o for o in sel)

    if (
        not has_geometry
        and navmesh_obj is not None
        and "navmesh_source_objects" in navmesh_obj
    ):
        names = navmesh_obj["navmesh_source_objects"].split("|")
        objects = []
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                objects.append(obj)
        return objects, navmesh_obj

    return [o for o in sel if o.type == "MESH" and "navmesh_cs" not in o], None


class NAVMESH_OT_Rebuild(bpy.types.Operator):
    bl_idname = "navmesh.rebuild"
    bl_label = "Rebuild NavMesh"
    bl_description = "Generate a navigation mesh from selected geometry"
    bl_options = {"REGISTER", "UNDO"}

    def _collect_mesh_data(self, context, objects):
        all_verts = []
        all_tris = []

        depsgraph = context.evaluated_depsgraph_get()

        for obj in objects:
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
        settings = context.scene.navmesh_settings
        source_objects, existing_navmesh = _resolve_source_objects(context)

        if not source_objects:
            self.report({"ERROR"}, "No mesh objects selected")
            return {"CANCELLED"}

        verts, tris = self._collect_mesh_data(context, source_objects)

        if len(verts) < 9 or len(tris) < 3:
            self.report({"ERROR"}, "Selected meshes have insufficient geometry")
            return {"CANCELLED"}

        ch = max(settings.cell_height, 0.01)
        cs = max(settings.cell_size, 0.01)

        config = {
            "cs": cs,
            "ch": ch,
            "walkableSlopeAngle": settings.agent_max_slope,
            "walkableHeight": math.ceil(settings.agent_height / ch),
            "walkableClimb": math.floor(settings.agent_max_climb / ch),
            "walkableRadius": math.ceil(settings.agent_radius / cs),
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

        source_name = source_objects[0].name if len(source_objects) == 1 else "multi"
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
        nm_obj["navmesh_agent_height"] = settings.agent_height
        nm_obj["navmesh_agent_radius"] = settings.agent_radius
        nm_obj["navmesh_agent_max_climb"] = settings.agent_max_climb
        nm_obj["navmesh_agent_max_slope"] = settings.agent_max_slope
        nm_obj["navmesh_poly_count"] = stats["polyCount"]
        nm_obj["navmesh_vert_count"] = stats["vertCount"]
        nm_obj["navmesh_tri_count"] = stats["triCount"]
        nm_obj["navmesh_build_time"] = stats["buildTime"]

        nm_obj["navmesh_source_objects"] = "|".join(o.name for o in source_objects)

        bpy.ops.object.select_all(action="DESELECT")
        nm_obj.select_set(True)
        context.view_layer.objects.active = nm_obj

        self.report(
            {"INFO"},
            f"NavMesh built: {stats['triCount']} tris, {stats['polyCount']} polys, {stats['buildTime']:.2f}s",
        )
        return {"FINISHED"}


def _find_navmesh(context):
    for obj in context.selected_objects:
        if "navmesh_cs" in obj:
            return obj
    return None


class NAVMESH_OT_AddSourceObject(bpy.types.Operator):
    bl_idname = "navmesh.add_source_object"
    bl_label = "Add to NavMesh"
    bl_description = "Add selected mesh objects to the navmesh source list"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        navmesh_obj = _find_navmesh(context)
        if navmesh_obj is None:
            self.report({"ERROR"}, "No NavMesh object selected")
            return {"CANCELLED"}

        existing = navmesh_obj.get("navmesh_source_objects", "")
        existing_set = set(existing.split("|")) if existing else set()

        added = []
        for obj in context.selected_objects:
            if obj.type != "MESH" or "navmesh_cs" in obj:
                continue
            if obj.name not in existing_set:
                added.append(obj.name)

        if not added:
            self.report({"WARNING"}, "No new mesh objects to add")
            return {"CANCELLED"}

        new_list = existing.split("|") if existing else []
        new_list.extend(added)
        navmesh_obj["navmesh_source_objects"] = "|".join(new_list)
        self.report({"INFO"}, f"Added: {', '.join(added)}")
        return {"FINISHED"}


class NAVMESH_OT_RemoveSourceObject(bpy.types.Operator):
    bl_idname = "navmesh.remove_source_object"
    bl_label = "Remove from NavMesh"
    bl_description = "Remove this object from the navmesh source list"
    bl_options = {"REGISTER", "UNDO"}

    object_name: bpy.props.StringProperty(name="Object Name")

    def execute(self, context):
        navmesh_obj = _find_navmesh(context)
        if navmesh_obj is None:
            self.report({"ERROR"}, "No NavMesh object selected")
            return {"CANCELLED"}

        existing = navmesh_obj.get("navmesh_source_objects", "")
        names = [n for n in existing.split("|") if n and n != self.object_name]
        navmesh_obj["navmesh_source_objects"] = "|".join(names)
        self.report({"INFO"}, f"Removed: {self.object_name}")
        return {"FINISHED"}


classes = [
    NAVMESH_OT_Rebuild,
    NAVMESH_OT_AddSourceObject,
    NAVMESH_OT_RemoveSourceObject,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
