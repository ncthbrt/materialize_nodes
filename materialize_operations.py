import bpy
from bpy.types import (
    Operator,
    Panel,
)
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty
import bl_ui.properties_data_modifier
from .utils import get_evaluated_geometry, is_materialize_modifier, is_materialize_child
import os
from .parse_utils import concat_error_path, parse_root_object

dir_path = os.path.dirname(__file__)


def create_data_block(context, data):
    if data["type"] == "ARMATURE":
        # TODO: Armatures
        return {
            "status": "ERROR",
            "path": ["data"],
            "message": "Armatures are not yet supported",
        }
    else:
        data_block = bpy.data.meshes.new(data["properties"]["name"])
        return {"status": "OK", "value": data_block}


def create_object(root, parent, context, object_data, data_block):
    name = object_data["properties"]["name"]
    new_obj = bpy.data.objects.new(object_data["properties"]["name"], data_block)
    new_obj.parent = parent
    context.collection.objects.link(data_block)
    new_obj["materialize_name"] = name
    new_obj["materialize_type"] = object_data["data"]["type"]
    node_modifier: bpy.types.NodesModifier = new_obj.modifiers.new(
        "Materialize", "NODES"
    )  # type: ignore

    new_obj["materialize"] = "CHILD"
    # node_modifier.node_group =

    return {"status": "OK", "value": new_obj}


def update_object(parent, context, existing_object, object_data):
    # TODO: Armatures
    # TODO: Everything else
    pass


def update_data_block(context, data):
    # TODO: Armatures
    # TODO: Everything else
    pass


def try_find_in_children(root_obj, name):
    children = root_obj.children
    for child in children:
        if "materialize_name" not in child:
            continue
        if child["materialize_name"] == name:
            return child
    return None


def materialize_object(
    parent, context, root_index, current_index, object_data, reference_geometry
):
    data_block_result = create_data_block(context, object_data)
    if data_block_result["status"] == "ERROR":
        return concat_error_path(data_block_result, object_data["properties"]["name"])
    data_block = data_block_result["values"]

    create_object_result = create_object(parent, context, object_data)
    if create_object_result["status"] == "ERROR":
        return create_object_result
    return {"status": "OK", "value": create_object_result["value"]}


def rematerialize_object(
    parent,
    context,
    root_index,
    current_index,
    existing_object,
    object_data,
    reference_geometry,
):
    data_block_result = update_data_block(context, object_data)
    if data_block_result["status"] == "ERROR":
        return concat_error_path(data_block_result, object_data["properties"]["name"])
    data_block = data_block_result["values"]

    update_object_result = update_object(parent, context, existing_object, object_data)
    if update_block_result["status"] == "ERROR":
        return update_object_result
    return {"status": "OK", "value": update_object_result["value"]}


def materialize_objects(
    root_obj, context, root_index, child_transform, child_geometry_set
):
    object_parse_result = parse_root_object(child_transform, child_geometry_set)
    if object_parse_result["status"] == "ERROR":
        return concat_error_path(object_parse_result, child_geometry_set.name)
    values = object_parse_result["values"]
    objects = values["objects"]
    reference_geometry_data = values["reference_geometry"]
    if reference_geometry_data is not None:
        pass
    reference_geometry = None
    parents = []
    object_0_object_data = objects[0]
    object_0_name = object_0_object_data["props"]["name"]
    existing_object_0 = try_find_in_children(root_obj, object_0_name)
    if existing_object_0 != None:
        result = rematerialize_object(
            root_obj,
            context,
            root_index,
            0,
            existing_object_0,
            object_0_object_data,
            reference_geometry,
        )
        if result["status"] == "ERROR":
            return result
        parents.append(result["value"])
    else:
        result = materialize_object(
            root_obj, context, root_index, 0, object_0_object_data, reference_geometry
        )
        if result["status"] == "ERROR":
            return result
        parents.append(result["value"])

    errors = []
    for i in range(1, len(objects)):
        object_data = objects[i]
        props = parent_index["properties"]
        name = props["name"]
        parent_index = object_data["parent"] + 1
        if parent_index <= 0 or parent_index >= len(parents):
            errors.append(
                {
                    "status": "ERROR",
                    "message": f"Parent index {parent_index} out of range for {name}",
                    "path": [object_0_name, name],
                }
            )
        parent = parents[parent]
        existing_object = try_find_in_children(root_obj, name)
        materialize_result = None
        if existing_object is not None:
            materialize_result = rematerialize_object(
                parent,
                context,
                root_index,
                i,
                existing_object,
                object_data,
                reference_geometry,
            )
        else:
            materialize_result = materialize_object(
                parent, context, root_index, i, object_data, reference_geometry
            )
        if materialize_result["status"] == "ERROR":
            errors.append(materialize_result)
        else:
            parents.append(materialize_result["value"])
    if len(errors) == 0:
        return {"status": "OK"}
    elif len(errors) == 1:
        return concat_error_path(errors[0], object_0_name)
    else:
        return {
            "status": "ERROR",
            "message": f"Multiple errors ocurred",
            "path": [object_0_name],
            "errors": errors,
        }


def materialize(root_obj, context):
    data = get_evaluated_geometry(root_obj, context)
    instances_pointcloud: bpy.types.PointCloud = data.instances_pointcloud()
    instance_references: list = data.instance_references()
    if instances_pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data"}
    instance_transforms = instances_pointcloud.attributes["instance_transform"]
    reference_indices = instances_pointcloud.attributes[".reference_index"]
    errors = []
    index = 0
    # Top level objects. These are special because they need to be pushed down once
    for child_transform, i in zip(instance_transforms.data, reference_indices.data):
        child_geometry_set = instance_references[i.value]
        result = materialize_objects(
            root_obj, context, index, child_transform.value, child_geometry_set
        )
        index += 1
        if result["status"] == "ERROR":
            errors.append(result)
    if len(errors) == 0:
        return {"status": "OK"}
    elif len(errors) == 1:
        return concat_error_path(errors[0], root_obj.name)
    else:
        return {
            "status": "ERROR",
            "message": f"Multiple errors ocurred",
            "path": [root_obj.name],
            "errors": errors,
        }


def format_errors(errors):
    result = ""
    for error in errors:
        path = str.join("/", error["path"])
        message = error["message"]
        result += f"{path}: {message}\n"
    return result


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
        materialize_result = materialize(obj, context)
        if materialize_result["status"] == "ERROR":
            msg = materialize_result["message"]
            self.report(
                {"ERROR_INVALID_INPUT"},
                f"{msg}\n" + format_errors(materialize_result["errors"]),
            )
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
        materialize(ob, context)
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
    if is_materialize_child(obj):
        return
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
