import bpy
from bpy.types import (
    Operator,
    Panel,
)
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty
)
import bl_ui.properties_data_modifier

def materialize_objects(object, context):
    pass

class Modifier_OT_MaterializeOperator(Operator):
    """Materializes an object hierachy from geometry data"""
    bl_idname = "mtlz.materialize_objects"
    bl_label = "Materialize Nodes"
    bl_description = "Append Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def execute(self, context):                
        ob = context.object
        materialize_objects(ob, context)
        ob.data["materialized"] = True
        return {'FINISHED'}
    
class Modifier_OT_RematerializeOperator(Operator):
    """(Re)Materializes an object hierachy from geometry data"""
    bl_idname = "mtlz.rematerialize_objects"
    bl_label = "(Re)Materialize Nodes"
    bl_description = "Append Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def execute(self, context):                
        ob = context.object        
        materialize_objects(ob, context)
        ob.data["materialized"] = True
        return {'FINISHED'}    

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, title="(Re)Materialization is a destructive operation. Are you sure you want to continue?")

def draw_materialize_button(self, context):
    from .custom_icons import get_icons        
    layout = self.layout
    ob = context.object
    if not ob:
        return
    layout = layout.row()
    layout.enabled = True
    if "materialized" not in ob.data:
        layout.operator(Modifier_OT_MaterializeOperator.bl_idname, text="Materialize", icon_value = get_icons()["materialize_icon"].icon_id)
    else:
        layout.operator(Modifier_OT_RematerializeOperator.bl_idname, text="(Re)Materialize", icon_value = get_icons()["materialize_icon"].icon_id)

def extend_modifier_panel():
    if not hasattr(bpy.types, "Modifier_OT_MaterializeOperator"):    
        bl_ui.properties_data_modifier.DATA_PT_modifiers.append(draw_materialize_button)

def remove_modifier_panel():    
    bl_ui.properties_data_modifier.DATA_PT_modifiers.remove(draw_materialize_button)

classes = (Modifier_OT_MaterializeOperator, Modifier_OT_RematerializeOperator)