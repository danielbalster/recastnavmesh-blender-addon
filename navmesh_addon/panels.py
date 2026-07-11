import bpy
import traceback
from bpy.props import FloatProperty, PointerProperty


MATERIAL_NAME = "NavMesh_Material"


def _get_or_create_material():
    mat = bpy.data.materials.get(MATERIAL_NAME)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(MATERIAL_NAME)
    mat.use_nodes = False
    mat.diffuse_color = (0.0, 0.8, 0.3, 0.2)
    mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    mat.show_transparent_back = False
    return mat


class NavMeshSettings(bpy.types.PropertyGroup):
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


def _sync_settings_from_navmesh(settings, navmesh_obj):
    settings.cell_size = navmesh_obj.get("navmesh_cs", settings.cell_size)
    settings.cell_height = navmesh_obj.get("navmesh_ch", settings.cell_height)
    settings.agent_height = navmesh_obj.get(
        "navmesh_agent_height", settings.agent_height
    )
    settings.agent_radius = navmesh_obj.get(
        "navmesh_agent_radius", settings.agent_radius
    )
    settings.agent_max_climb = navmesh_obj.get(
        "navmesh_agent_max_climb", settings.agent_max_climb
    )
    settings.agent_max_slope = navmesh_obj.get(
        "navmesh_agent_max_slope", settings.agent_max_slope
    )


def _find_navmesh(context):
    for obj in context.selected_objects:
        if "navmesh_cs" in obj:
            return obj
    if context.active_object is not None and "navmesh_cs" in context.active_object:
        return context.active_object
    for obj in bpy.data.objects:
        if "navmesh_cs" in obj:
            return obj
    return None


class NAVMESH_PT_Main(bpy.types.Panel):
    bl_idname = "NAVMESH_PT_main"
    bl_label = "NavMesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavMesh"

    def draw(self, context):
        try:
            layout = self.layout
            settings = context.scene.navmesh_settings
            nm = _find_navmesh(context)

            layout.operator("navmesh.rebuild", text="Rebuild", icon="MESH_DATA")

            box = layout.box()
            box.label(text="Agent", icon="OUTLINER_OB_ARMATURE")
            col = box.column(align=True)
            col.prop(settings, "agent_height", text="Height")
            col.prop(settings, "agent_radius", text="Radius")
            col.prop(settings, "agent_max_climb", text="Max Climb")
            col.prop(settings, "agent_max_slope", text="Max Slope")

            box = layout.box()
            box.label(text="Cells", icon="GRID")
            col = box.column(align=True)
            col.prop(settings, "cell_size", text="Cell Size")
            col.prop(settings, "cell_height", text="Cell Height")

            layout.separator()

            if nm is None:
                layout.label(text="Select mesh objects and click Rebuild", icon="INFO")
            else:
                coll_name = nm.get("navmesh_source_collection", "")
                coll = bpy.data.collections.get(coll_name)
                if coll is not None:
                    mesh_count = sum(1 for o in coll.objects if o.type == "MESH")
                    src_box = layout.box()
                    src_box.label(text="Source Objects", icon="OUTLINER_COLLECTION")
                    src_box.label(text=f"Collection: {coll_name}")
                    src_box.label(
                        text=f"{mesh_count} mesh objects (manage in Outliner)"
                    )
                    row = src_box.row(align=True)
                    row.operator(
                        "navmesh.add_source_object", text="Add Selected", icon="ADD"
                    )
                    row.operator(
                        "navmesh.remove_source_object",
                        text="Remove Selected",
                        icon="REMOVE",
                    )

                stat_items = [
                    ("navmesh_poly_count", "Polygons"),
                    ("navmesh_vert_count", "Vertices"),
                    ("navmesh_tri_count", "Triangles"),
                    ("navmesh_build_time", "Build Time (s)"),
                ]
                has_stats = any(key in nm for key, label in stat_items)
                if has_stats:
                    box = layout.box()
                    box.label(text="Stats", icon="INFO")
                    col = box.column(align=True)
                    col.enabled = False
                    for key, label in stat_items:
                        if key in nm:
                            col.prop(nm, f'["{key}"]', text=label, emboss=False)
        except Exception:
            traceback.print_exc()
            layout = self.layout
            box = layout.box()
            box.label(text="Panel draw error", icon="ERROR")
            col = box.column(align=True)
            for line in traceback.format_exc().splitlines()[-8:]:
                col.label(text=line)


classes = [NavMeshSettings, NAVMESH_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.navmesh_settings = PointerProperty(type=NavMeshSettings)


def unregister():
    del bpy.types.Scene.navmesh_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
