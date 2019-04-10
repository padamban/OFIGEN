bl_info = {
    "name": "Optical Flow Image Generator - Manager",
    "author": "padamban",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Tool Shelf > MNGR",
    "description": "Generate realistic images with spacial data.",
    "warning": "",
    "wiki_url": "",
    "category": "User",
    }






import bpy

from bpy.props import ( PointerProperty )




def installOFIGEN(context):
    ofigen_file = context.scene.mngr_data.ofigen_path
    bpy.ops.wm.addon_remove(module="addon_ofigen")
    bpy.ops.wm.addon_install(filepath=ofigen_file)
    bpy.ops.wm.addon_enable(module='addon_ofigen')
    bpy.ops.wm.save_userpref()

# Existing blender addon, used for creating background images. 
def enableIMAGESasPLANES():
    bpy.ops.wm.addon_enable(module="io_import_images_as_planes")






class MngrData(bpy.types.PropertyGroup):
    ofigen_path = bpy.props.StringProperty( name = "", default = "D:\\ofigen\\addon_ofigen.py", description = "Path of the OFIGEN addon file.", subtype = 'FILE_PATH')

class ButtonReload(bpy.types.Operator):
    """Remove the OFIGEN addon, then add it again."""
    bl_idname = "myops.reloadbtn"
    bl_label = "Reload OFIGEN"

    def execute(self, context):
        installOFIGEN(context)
        enableIMAGESasPLANES()
        return {'FINISHED'}


class OfigenConfigPanel(  bpy.types.Panel):
    bl_space_type =  'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "OFIGEN Manager"
    bl_idname = "OFIGEN_mngr"
    bl_category = 'MNGR'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.mngr_data, 'ofigen_path')
        layout.separator()
        layout.operator("myops.reloadbtn")




def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.mngr_data = PointerProperty(type=MngrData)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.mngr_data

if __name__ == "__main__":
    register()






















