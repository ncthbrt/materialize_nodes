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
from .utils import get_evaluated_geometry, is_materialize_modifier
import os

dir_path = os.path.dirname(__file__)

def concat_error_path(error, part): 
    error["path"].append(part)
    return error

def parse_vertex_groups(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
                return { "status": "ERROR", "message": "Missing vertex_group values", "path": ["vertex_groups"] }
    reference_indices = pointcloud.attributes[".reference_index"]
    values = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        values.append(child.name)        
    return { "status": "OK", "values": values }

def parse_name(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return { "status": "ERROR", "message": "Missing name", "path": ["name"] }
    if instance_references is None:
        return { "status": "ERROR", "message": "Missing name", "path": ["name"] }
    reference_indices = pointcloud.attributes[".reference_index"]    
    for i in reference_indices.data:
        child = instance_references[i.value]
        return { "status": "OK", "value": child.name }
    return { "status": "ERROR", "message": "Missing name", "path": ["name"] }

def parse_attribute_values(pointcloud, instance_references):
    # geometry_set
    values = dict()
    reference_indices = pointcloud.attributes[".reference_index"]
    found_values = False
    for [attribute_name, attribute] in pointcloud.attributes.items():        
        if attribute_name == ".reference_index":
            continue
        for [i, attribute_value] in zip(reference_indices.data, attribute.data):
            child = instance_references[i.value]
            if child.name != "values":
                continue                
            found_values = True
            values[attribute_name] = attribute_value.value
    if found_values == False:
        return { "status": "ERROR", "message": "Missing attribute values", "path": ["values"] }
    print(values)
    return { "status": "OK", "values": values }    
    

def parse_attributes(geometry_set, values):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return { "status": "ERROR", "message": "Malformed data", "path": ["attributes"] }    
    values_result = parse_attribute_values(pointcloud, instance_references)
    if values_result["status"] == "ERROR":
            return concat_error_path(values_result, "attributes")
    else:
        return values_result    


def parse_properties(obj, context, geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return { "status": "ERROR", "message": "Malformed data", "path": ["properties"] }
    values = dict()
    reference_indices = pointcloud.attributes[".reference_index"]
    vertex_groups = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        if child.name == "name":
            name_result = parse_name(child)
            if name_result["status"] == "ERROR":
                return concat_error_path(name_result, "properties")
            else:
                name = name_result["value"]
                values["name"] = name
        elif child.name == "attributes":
            attributes_result = parse_attributes(child, values)
            if attributes_result["status"] == "ERROR":
                return concat_error_path(attributes_result, "properties")            
        elif child.name == "vertex_groups":
            vertex_groups_result = parse_vertex_groups(child)
            if vertex_groups_result["status"] == "ERROR":
                return concat_error_path(vertex_groups_result, "properties")            
            else:
                vertex_groups = vertex_groups_result["values"]
                values["vertex_grups"] = vertex_groups            
    return {"status": "OK", "values": values }

# def gather_child_objects(root_obj, context, transform, children_geometry_set):
#     pass

def materialize_objects_impl(geometry_set):
    pass

def materialize_root_object(root_obj, context, transform, geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    if pointcloud is None:
        return { "status": "ERROR", "message": "Malformed data" }
    instance_references: list = geometry_set.instance_references()
    if instance_references is None:
        return { "status": "ERROR", "message": "Malformed data" }
    instance_transforms = pointcloud.attributes["instance_transform"]
    reference_indices = pointcloud.attributes[".reference_index"]
    children = None
    properties = None
    data = None
    for (_, i) in zip(instance_transforms.data, reference_indices.data):
        child = instance_references[i.value]        
        properties = None
        if child.name == "properties":
            prop_result = parse_properties(root_obj, context, child)
            if prop_result["status"] == "ERROR":
                return prop_result
            else:
                properties = prop_result["values"]
        elif child.name == "data":
            data = child
        elif child.name == "children":
            children = child
        else: 
            continue
    if children is not None:
        pass
    if properties is None:
        return { "status": "ERROR", "message": "Missing properties for " + geometry_set.name }
    if data is None:
        return { "status": "ERROR", "message": "Missing data for " + geometry_set.name }
    return { "status": "OK" }

def materialize_objects(obj, context):
    data = get_evaluated_geometry(obj, context)
    instances_pointcloud: bpy.types.PointCloud = data.instances_pointcloud()
    instance_references: list = data.instance_references()
    if instances_pointcloud is None or instance_references is None:
        return { "status": "ERROR", "message": "Malformed data" }
    instance_transforms = instances_pointcloud.attributes["instance_transform"]
    reference_indices = instances_pointcloud.attributes[".reference_index"]    
    # Top level objects. These are special because they need to be pushed down once
    for (child_transform, i) in zip(instance_transforms.data, reference_indices.data):
        child_geometry_set = instance_references[i.value]
        result = materialize_root_object(obj, context, child_transform, child_geometry_set)
        if result["status"] == "ERROR":
            return result
    return { "status": "OK" }


class Modifier_OT_MaterializeOperator(Operator):
    """Materializes an object hierachy from geometry data"""
    bl_idname = "mtlz.materialize_objects"
    bl_label = "Materialize Nodes"
    bl_description = "Append Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj

    def execute(self, context):                
        obj = context.object
        materialize_objects(obj, context)
        obj.data["materialized"] = True
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
        return wm.invoke_props_dialog(self, title="(Re)Materialization is a potentially destructive operation. Are you sure you want to continue?", confirm_text="Continue")

class OBJ_OT_template_group_add(Operator):
    """Creates a new node group that outputs a materialized object"""
    bl_idname = "mtlz.add_template_group"
    bl_label = "Initialize Materialized Object"
    bl_description = "Creates a new node group that outputs a pass-through materialized object"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        result = is_materialize_modifier(context.object)
        return result == False            

    def execute(self, context):                
        import bpy.types
        ob = context.object
        index = len(ob.modifiers)
        ob.modifiers.new("Materialize", "NODES")
        modifier = ob.modifiers[index]
        template_name = "Materialize Template"
        filepath = os.path.join(dir_path, "node_groups.blend")
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            if template_name not in bpy.data.node_groups:
                data_to.node_groups.append(template_name)
        copy = bpy.data.node_groups[template_name].copy()
        name = ob.name + " Materalize Group"
        copy.name = name
        copy["materialize"] = True
        modifier.node_group = copy
        return {'FINISHED'}

def draw_materialize_button(self, context):
    from .custom_icons import get_icons        
    layout = self.layout
    obj = context.object
    if not obj:
        return
    layout = layout.row()
    layout.enabled = True
    if not is_materialize_modifier(obj):
        layout.operator(OBJ_OT_template_group_add.bl_idname, text="Add Materialize Modifier", icon_value = get_icons()["materialize_icon"].icon_id)
    elif "materialized" not in obj.data:
        layout.operator(Modifier_OT_MaterializeOperator.bl_idname, text="Materialize", icon_value = get_icons()["materialize_icon"].icon_id)
    else:
        layout.operator(Modifier_OT_RematerializeOperator.bl_idname, text="(Re)Materialize", icon_value = get_icons()["materialize_icon"].icon_id)

def extend_modifier_panel():
    if not hasattr(bpy.types, "Modifier_OT_MaterializeOperator"):    
        bl_ui.properties_data_modifier.DATA_PT_modifiers.append(draw_materialize_button)

def remove_modifier_panel():    
    bl_ui.properties_data_modifier.DATA_PT_modifiers.remove(draw_materialize_button)

classes = (Modifier_OT_MaterializeOperator, Modifier_OT_RematerializeOperator, OBJ_OT_template_group_add)