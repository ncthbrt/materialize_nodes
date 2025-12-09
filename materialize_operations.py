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
import bmesh

dir_path = os.path.dirname(__file__)


def create_armature(context, data):
    return {
        "status": "ERROR",
        "path": ["data", "geometry"],
        "message": "Armatures are not yet supported",
    }


def create_curve(context, data):
    return {
        "status": "ERROR",
        "path": ["data", "geometry"],
        "message": "Curves are not yet supported",
    }


def create_mesh(context, data):
    data_block = bpy.data.meshes.new(data["DATA"]["NAME"])
    return {
        "status": "ERROR",
        "path": ["data", "geometry"],
        "message": "Curves are not yet supported",
    }


def create_object(root, parent, context, object_data, root_index, current_index):
    data_block = None
    subtype = object_data["DATA"]["GEOMETRY"]["subtype"]
    new_obj = None
    match subtype:
        case "ARMATURE":
            armature_result = create_armature(context, object_data)
            if armature_result["status"] == "ERROR":
                return armature_result
            new_obj = armature_result["value"]
        case "MESH":
            pass

    if subtype != "ARMATURE":
        data_block = bpy.data.meshes.new(object_data["DATA"]["NAME"])
    else:
        armature_result = create_armature(context, object_data)
        if armature_result["status"] == "ERROR":
            return armature_result
        data_block = armature_result["value"]
    name = object_data["NAME"]
    new_obj = bpy.data.objects.new(name, data_block)
    new_obj.parent = parent
    context.collection.objects.link(new_obj)
    new_obj["materialize_name"] = name
    new_obj["materialize_subtype"] = subtype

    if subtype == "ARMATURE":
        pass
    else:
        from .materialize_blend_loader import load_node_group

        node_group = load_node_group("Materialized Geometry")

        node_modifier: bpy.types.NodesModifier = new_obj.modifiers.new(
            "Materialize", "NODES"
        )  # type: ignore

        node_modifier.node_group = node_group
        node_modifier["Socket_5"] = root
        node_modifier["Socket_2"] = root_index
        node_modifier["Socket_3"] = current_index
        if subtype == "MESH":
            depsgraph = context.evaluated_depsgraph_get()
            # mesh = new_obj.to_mesh(depsgraph=depsgraph, preserve_all_data_layers=True)
            bm = bmesh.new()
            bm.from_object(object=new_obj, depsgraph=depsgraph)
            bm.to_mesh(new_obj.data)
            new_obj.modifiers.remove(node_modifier)
        else:
            pass
            # bpy.ops.object.modifier_apply()
            # bpy.ops.object.convert(target=subtype, )

        new_obj["materialize"] = "CHILD"
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
    root, parent, context, root_index, current_index, object_data, reference_geometry
):
    create_object_result = create_object(
        root, parent, context, object_data, root_index, current_index
    )
    if create_object_result["status"] == "ERROR":
        return create_object_result
    return {"status": "OK", "value": create_object_result["value"]}


def rematerialize_object(
    root,
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
        return concat_error_path(data_block_result, object_data["NAME"])
    data_block = data_block_result["value"]
    update_object_result = update_object(
        root, parent, context, existing_object, object_data
    )
    if update_object_result["status"] == "ERROR":
        return update_object_result
    return {"status": "OK", "value": update_object_result["value"]}


def materialize_objects(
    root_obj,
    context,
    root_index,
    root_geometry_index,
    parent_geometryset,
    child_geometry_set,
):
    object_parse_result = parse_root_object(
        root_geometry_index, parent_geometryset, child_geometry_set
    )
    if object_parse_result["status"] == "ERROR":
        return concat_error_path(object_parse_result, child_geometry_set.name)
    errors = []
    values = object_parse_result["value"]
    objects = values["CHILDREN"]
    reference_geometry_data = None
    if "REFERENCE_GEOMETRY" in values:
        reference_geometry_data = values["REFERENCE_GEOMETRY"]
    if reference_geometry_data is not None:
        # TODO: Materialize reference geometry
        pass
    reference_geometry = None
    parents = []
    print(objects)
    object_0_object_data = objects[0]
    object_0_name = object_0_object_data["NAME"]
    existing_object_0 = try_find_in_children(root_obj, object_0_name)
    if existing_object_0 != None:
        result = rematerialize_object(
            root_obj,
            root_obj,
            context,
            root_index,
            -1,
            existing_object_0,
            object_0_object_data,
            reference_geometry,
        )
        if result["status"] == "ERROR":
            return result
        parents.append(result["value"])
    else:
        result = materialize_object(
            root_obj,
            root_obj,
            context,
            root_index,
            -1,
            object_0_object_data,
            reference_geometry,
        )
        if result["status"] == "ERROR":
            return result
        parents.append(result["value"])

    for i in range(1, len(objects)):
        object_data = objects[i]
        name = object_data["NAME"]
        parent_index = object_data["parent"]
        if parent_index < 0 or parent_index >= len(parents):
            errors.append(
                {
                    "status": "ERROR",
                    "message": f"Parent index {parent_index} out of range for {name}",
                    "path": [object_0_name, name],
                }
            )
            continue
        parent = parents[parent_index]
        existing_object = try_find_in_children(root_obj, name)
        materialize_result = None
        if existing_object is not None:
            materialize_result = rematerialize_object(
                root_obj,
                parent,
                context,
                root_index,
                i - 1,
                existing_object,
                object_data,
                reference_geometry,
            )
        else:
            materialize_result = materialize_object(
                root_obj,
                parent,
                context,
                root_index,
                i - 1,
                object_data,
                reference_geometry,
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
            root_obj, context, index, i.value, instances_pointcloud, child_geometry_set
        )
        index += 1
        if result["status"] == "ERROR":
            errors.append(result)
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
        from .materialize_blend_loader import load_node_group

        ob = context.object
        index = len(ob.modifiers)
        ob.modifiers.new("Materialize", "NODES")
        modifier = ob.modifiers[index]
        template_name = "Materialize Template"
        copy = load_node_group(template_name).copy()
        name = f"{ob.name} Materalize Group"
        copy.name = name
        modifier.node_group = copy
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
