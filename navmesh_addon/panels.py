import bpy
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


class NAVMESH_PT_Main(bpy.types.Panel):
    bl_idname = "NAVMESH_PT_main"
    bl_label = "NavMesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavMesh"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.navmesh_settings

        navmesh_obj = None
        for obj in context.selected_objects:
            if "navmesh_cs" in obj:
                navmesh_obj = obj
                break

        if navmesh_obj is not None:
            _sync_settings_from_navmesh(settings, navmesh_obj)

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

        if navmesh_obj is None:
            layout.separator()
            layout.label(text="Select mesh objects and click Rebuild", icon="INFO")
            return

        layout.separator()

        coll_name = navmesh_obj.get("navmesh_source_collection", "")
        coll = bpy.data.collections.get(coll_name)
        if coll is not None:
            src_box = layout.box()
            src_box.label(text=f"Source: {coll_name}", icon="OUTLINER_COLLECTION")
            for obj in coll.objects:
                if obj.type != "MESH":
                    continue
                row = src_box.row(align=True)
                row.label(text=obj.name, icon="OUTLINER_OB_MESH")
                op = row.operator(
                    "navmesh.remove_source_object",
                    text="",
                    icon="X",
                    emboss=False,
                )
                op.object_name = obj.name
            row = src_box.row()
            row.operator("navmesh.add_source_object", text="Add Selected", icon="ADD")
            row.label(text="")

        box = layout.box()
        box.label(text="Stats", icon="INFO")
        col = box.column(align=True)
        col.prop(navmesh_obj, '["navmesh_poly_count"]', text="Polygons", emboss=False)
        col.prop(navmesh_obj, '["navmesh_vert_count"]', text="Vertices", emboss=False)
        col.prop(navmesh_obj, '["navmesh_tri_count"]', text="Triangles", emboss=False)
        col.prop(
            navmesh_obj, '["navmesh_build_time"]', text="Build Time (s)", emboss=False
        )
        for item in col.children:
            item.enabled = False


classes = [NavMeshSettings, NAVMESH_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.navmesh_settings = PointerProperty(type=NavMeshSettings)


def unregister():
    del bpy.types.Scene.navmesh_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
