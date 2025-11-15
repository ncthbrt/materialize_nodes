import bpy
from bpy.types import (
    Operator,
    Panel,
)
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty
import bl_ui.properties_data_modifier
from .utils import get_evaluated_geometry, is_materialize_modifier
import os
from .parse_utils import concat_error_path, parse_root_object

dir_path = os.path.dirname(__file__)


# def gather_child_objects(root_obj, context, transform, children_geometry_set):
#     pass


def materialize_objects_impl(root_obj, geometry_set):
    pass


def create_data_block(data):
    pass


def materialize_object(obj, context, child_transform, child_geometry_set):
    object_result = parse_root_object(child_transform, child_geometry_set)
    if object_result["status"] == "ERROR":
        return concat_error_path(object_result, child_geometry_set.name)
    values = object_result["values"]
    objects = values["objects"]
    reference_geometry = values["reference_geometry"]
    stack = []
    if reference_geometry is not None:
        pass

    for object in objects:
        props = parent["properties"]
        name = props["name"]
        parent = object["parent"] + 1
        if parent >= 0:
            pass
        else:
            pass

    return {"status": "OK"}


def materialize_objects(obj, context):
    data = get_evaluated_geometry(obj, context)
    instances_pointcloud: bpy.types.PointCloud = data.instances_pointcloud()
    instance_references: list = data.instance_references()
    if instances_pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data"}
    instance_transforms = instances_pointcloud.attributes["instance_transform"]
    reference_indices = instances_pointcloud.attributes[".reference_index"]
    # Top level objects. These are special because they need to be pushed down once
    for child_transform, i in zip(instance_transforms.data, reference_indices.data):
        child_geometry_set = instance_references[i.value]
        result = materialize_object(
            obj, context, child_transform.value, child_geometry_set
        )
        if result["status"] == "ERROR":
            return result
    return {"status": "OK"}


class Modifier_OT_MaterializeOperator(Operator):
    """Materializes an object hierachy from geometry data"""

    bl_idname = "mtlz.materialize_objects"
    bl_label = "Materialize Nodes"
    bl_description = "Append Node Group"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj

    def execute(self, context):
        obj = context.object
        materialize_objects(obj, context)
        obj.data["materialized"] = True
        return {"FINISHED"}


class Modifier_OT_RematerializeOperator(Operator):
    """(Re)Materializes an object hierachy from geometry data"""

    bl_idname = "mtlz.rematerialize_objects"
    bl_label = "(Re)Materialize Nodes"
    bl_description = "Append Node Group"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob

    def execute(self, context):
        ob = context.object
        materialize_objects(ob, context)
        ob.data["materialized"] = True
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(
            self,
            title="(Re)Materialization is a potentially destructive operation. Are you sure you want to continue?",
            confirm_text="Continue",
        )


class OBJ_OT_template_group_add(Operator):
    """Creates a new node group that outputs a materialized object"""

    bl_idname = "mtlz.add_template_group"
    bl_label = "Initialize Materialized Object"
    bl_description = (
        "Creates a new node group that outputs a pass-through materialized object"
    )
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
        return {"FINISHED"}


def draw_materialize_button(self, context):
    from .custom_icons import get_icons

    layout = self.layout
    obj = context.object
    if not obj:
        return
    layout = layout.row()
    layout.enabled = True
    if not is_materialize_modifier(obj):
        layout.operator(
            OBJ_OT_template_group_add.bl_idname,
            text="Add Materialize Modifier",
            icon_value=get_icons()["materialize_icon"].icon_id,
        )
    elif "materialized" not in obj.data:
        layout.operator(
            Modifier_OT_MaterializeOperator.bl_idname,
            text="Materialize",
            icon_value=get_icons()["materialize_icon"].icon_id,
        )
    else:
        layout.operator(
            Modifier_OT_RematerializeOperator.bl_idname,
            text="(Re)Materialize",
            icon_value=get_icons()["materialize_icon"].icon_id,
        )


def extend_modifier_panel():
    if not hasattr(bpy.types, "Modifier_OT_MaterializeOperator"):
        bl_ui.properties_data_modifier.DATA_PT_modifiers.append(draw_materialize_button)


def remove_modifier_panel():
    bl_ui.properties_data_modifier.DATA_PT_modifiers.remove(draw_materialize_button)


classes = (
    Modifier_OT_MaterializeOperator,
    Modifier_OT_RematerializeOperator,
    OBJ_OT_template_group_add,
)
