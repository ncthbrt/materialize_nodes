import bpy
from bpy.types import (
    Operator,
    Panel,
)
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty
import bl_ui.properties_data_modifier
from .utils import get_evaluated_geometry, is_materialize_modifier, is_materialize_child
from .parse_utils import concat_error_path, parse_objects
import bmesh


def update_armature(context, armature_data_block, object_data):
    pass


def create_armature(context, object_data):
    return {
        "status": "ERROR",
        "path": ["data", "geometry"],
        "message": "Armatures are not yet supported",
    }


def create_instance(context, data):
    return {
        "status": "ERROR",
        "path": ["data", "geometry"],
        "message": "Instances are not yet supported",
    }


def create_geometry_data_block(context, object_data):
    data_block_name = object_data["DATA"]["NAME"]
    data_block = object_data["DATA"]["GEOMETRY"]["value"]
    data_block.name = data_block_name
    object_name = object_data["NAME"]
    new_obj = bpy.data.objects.new(object_name, data_block)
    return {"status": "OK", "value": new_obj}


def create_or_update_object(root, parent, context, object_data):
    subtype = object_data["DATA"]["GEOMETRY"]["subtype"]
    new_obj = None
    match subtype:
        case "ARMATURE":
            result = create_armature(context, object_data)
            if result["status"] == "ERROR":
                return result
            new_obj = result["value"]
        case "MESH" | "CURVE" | "VOLUME" | "GREASEPENCIL" | "POINTCLOUD":
            result = create_geometry_data_block(context, object_data)
            if result["status"] == "ERROR":
                return result
            new_obj = result["value"]
        case "INSTANCE":
            result = create_instance(context, object_data)
            if result["status"] == "ERROR":
                return result
            new_obj = result["value"]

    new_obj.parent = parent
    context.collection.objects.link(new_obj)
    new_obj["materialize_name"] = object_data["DATA"]["NAME"]
    new_obj["materialize_subtype"] = subtype
    return {"status": "OK", "value": new_obj}


def update_object(root, parent, context, existing_object, object_data):
    # TODO: Armatures
    # TODO: Everything else
    return {
        "status": "ERROR",
        "message": "Cannot yet update objects",
        "path": [existing_object.name],
    }


def update_data_block(context, data):
    # TODO: Armatures
    # TODO: Everything else
    return {
        "status": "ERROR",
        "message": "Cannot yet update data-blocks",
        "path": [],
    }


def try_find_in_children(root_obj, name):
    children = root_obj.children
    for child in children:
        if "materialize_name" not in child:
            continue
        if child["materialize_name"] == name:
            return child
    return None


def materialize_object(
    root, parent, context, object_data, reference_geometry, existing_object
):
    create_object_result = create_or_update_object(root, parent, context, object_data)
    print("hello", create_object_result)
    if create_object_result["status"] == "ERROR":
        return create_object_result
    return {"status": "OK", "value": create_object_result["value"]}


def materialize(root_obj, context):
    data = get_evaluated_geometry(root_obj, context)
    parse_result = parse_objects(data)
    errors = []
    if parse_result["status"] == "ERROR":
        return concat_error_path(parse_result, root_obj.name)
    objects = parse_result["value"]
    parents = [root_obj]
    for object_data in objects:
        name = object_data["NAME"]
        parent_index = object_data["parent"] + 1
        if parent_index < 0 or parent_index >= len(parents):
            errors.append(
                {
                    "status": "ERROR",
                    "message": f"Parent index {parent_index} out of range for {name}",
                    "path": [root_obj.name, name],
                }
            )
            continue
        parent = parents[parent_index]
        existing_object = try_find_in_children(root_obj, name)
        reference_geometry = None
        if "REFERENCE_GEOMETRY" in object_data:
            reference_geometry = object_data["REFERENCE_GEOMETRY"]
        materialize_result = materialize_object(
            root_obj,
            parent,
            context,
            existing_object,
            object_data,
            reference_geometry,
            existing_object,
        )
        if materialize_result["status"] == "ERROR":
            errors.append(materialize_result)
        else:
            parents.append(materialize_result["value"])
    if len(errors) == 0:
        return {"status": "OK"}
    elif len(errors) == 1:
        error = concat_error_path(errors[0], root_obj.name)
        return {
            "status": "ERROR",
            "message": "",
            "path": error["path"],
            "errors": [error],
        }
    else:
        return {
            "status": "ERROR",
            "message": f"Multiple errors ocurred",
            "path": [root_obj.name],
            "errors": errors,
        }


def format_errors(errors):
    result = []
    for error in errors:
        path = str.join("/", error["path"])
        message = error["message"]
        result.append(f"{path}: {message}")
    return str.join("\n", result)


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
            formatted_errors = format_errors(materialize_result["errors"])
            self.report(
                {"ERROR_INVALID_INPUT"},
                f"{msg}\n{formatted_errors}",
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
        from .materialize_blend_loader import load_node_group, load_template_node_group

        ob = context.object
        index = len(ob.modifiers)
        ob.modifiers.new("Materialize", "NODES")
        modifier = ob.modifiers[index]
        copy = load_template_node_group("Materialize Template").copy()
        name = f"{ob.name} Materalize Group"
        copy.name = name
        modifier.node_group = copy

        index = len(ob.modifiers)
        ob.modifiers.new("Prepare Materialization", "NODES")
        prepare_modifier = ob.modifiers[index]
        copy = load_node_group("Prepare Materialization")
        prepare_modifier.node_group = copy
        modifier.is_active = True
        return {"FINISHED"}


extended = False


def draw_materialize_button(self, context):
    global extended
    extended = True
    from .custom_icons import get_icons

    layout = self.layout
    obj = context.object
    if not obj:
        return
    if is_materialize_child(obj) or not is_materialize_modifier(obj):
        return
    layout = layout.row()
    layout.enabled = True
    if "materialized" not in obj.data:
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


def draw_add_materialize_modifier(self, context):
    global extended
    extended = True
    from .custom_icons import get_icons

    obj = context.object
    layout = self.layout
    if not obj:
        return
    if not is_materialize_modifier(obj):
        layout.operator(
            OBJ_OT_template_group_add.bl_idname,
            text="New Materialize Node Group",
            icon_value=get_icons()["materialize_icon"].icon_id,
        )


def extend_modifier_panel():
    global extended
    if not extended:
        bl_ui.properties_data_modifier.DATA_PT_modifiers.append(draw_materialize_button)
        bl_ui.properties_data_modifier.OBJECT_MT_modifier_add.append(
            draw_add_materialize_modifier
        )
    extended = True


def remove_modifier_panel():
    global extended
    extended = False
    bl_ui.properties_data_modifier.DATA_PT_modifiers.remove(draw_materialize_button)
    bl_ui.properties_data_modifier.OBJECT_MT_modifier_add.remove(
        draw_add_materialize_modifier
    )


classes = (
    Modifier_OT_MaterializeOperator,
    Modifier_OT_RematerializeOperator,
    OBJ_OT_template_group_add,
)
