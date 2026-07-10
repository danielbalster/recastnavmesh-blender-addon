import bpy


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


class NAVMESH_PT_Main(bpy.types.Panel):
    bl_idname = "NAVMESH_PT_main"
    bl_label = "NavMesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NavMesh"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.operator("navmesh.rebuild", text="Rebuild", icon="MESH_DATA")

        selected_meshes = [o for o in context.selected_objects if o.type == "MESH"]
        if not selected_meshes:
            layout.label(text="Select mesh objects and click Rebuild", icon="INFO")

        if obj is None or "navmesh_cs" not in obj:
            return

        layout.separator()

        box = layout.box()
        box.label(text="Agent", icon="OUTLINER_OB_ARMATURE")
        col = box.column(align=True)
        col.prop(obj, '["navmesh_agent_height"]', text="Height", emboss=False)
        col.prop(obj, '["navmesh_agent_radius"]', text="Radius", emboss=False)
        col.prop(obj, '["navmesh_agent_max_climb"]', text="Max Climb", emboss=False)
        col.prop(obj, '["navmesh_agent_max_slope"]', text="Max Slope", emboss=False)
        for item in col.children:
            item.enabled = False

        box = layout.box()
        box.label(text="Cells", icon="GRID")
        col = box.column(align=True)
        col.prop(obj, '["navmesh_cs"]', text="Cell Size", emboss=False)
        col.prop(obj, '["navmesh_ch"]', text="Cell Height", emboss=False)
        for item in col.children:
            item.enabled = False

        box = layout.box()
        box.label(text="Stats", icon="INFO")
        col = box.column(align=True)
        col.prop(obj, '["navmesh_poly_count"]', text="Polygons", emboss=False)
        col.prop(obj, '["navmesh_vert_count"]', text="Vertices", emboss=False)
        col.prop(obj, '["navmesh_tri_count"]', text="Triangles", emboss=False)
        col.prop(obj, '["navmesh_build_time"]', text="Build Time (s)", emboss=False)
        for item in col.children:
            item.enabled = False


classes = [NAVMESH_PT_Main]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
