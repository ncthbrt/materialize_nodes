import bpy


def concat_error_path(error, part):
    if len(part) > 0:
        error["path"].insert(0, part)
    return error


type_ids = {
    1: "OBJECT",
    2: "BONE",
    3: "DATA",
    4: "CHILDREN",
    5: "REFERENCE_GEOMETRY",
    6: "GEOMETRY",
    7: "MODIFIER",
    8: "CONSTRAINT",
    9: "DEPENDENCIES",
    10: "FALLOFF",
    11: "MATERIALS",
    12: "CONSTRAINTS",
    13: "MODIFIERS",
    14: "VERTEX_GROUPS",
    15: "ATTRIBUTES",
    16: "SELECTION",
    17: "NAME",
    18: "TARGET",
    19: "DEPENDENCY",
    20: "TARGET_SPACE",
    21: "OWNER_SPACE",
    22: "VERTEX_GROUP",
    23: "TARGET_VALUE",
    24: "SUBTARGET_VALUE",
}

data_block_type_ids = {
    1: "ARMATURE",
    2: "CURVE",
    3: "GREASEPENCIL",
    4: "MESH",
    5: "POINTCLOUD",
    6: "VOLUME",
    7: "INSTANCE",
}

constraint_type_ids = {1: "TRANSFORM", 2: "LOCATION", 3: "ROTATION", 4: "SCALE"}

modifier_type_ids = {1: "HOOK", 2: "ARMATURE"}

space_type_ids = {
    1: "WORLD",
    2: "CUSTOM",
    3: "POSE",
    4: "LOCAL_WITH_PARENT",
    5: "LOCAL",
}

subtype_type_ids = {
    "SPACE": space_type_ids,
    "MODIFIER": modifier_type_ids,
    "CONSTRAINT": constraint_type_ids,
    "GEOMETRY": data_block_type_ids,
    "REFERENCE_GEOMETRY": data_block_type_ids,
}

domain_type_ids = {
    1: "POINT",
    2: "EDGE",
    3: "FACE",
    4: "FACE_CORNER",
    5: "SPLINE",
    6: "INSTANCE",
    7: "LAYER",
}


def parse_name(child):
    return {"status": "OK", "type": "NAME", "value": child.name}


def get_attribute_value(data_type, attribute_value):
    if (
        data_type == "FLOAT_VECTOR"
        or data_type == "FLOAT2"
        or data_type == "INT16_2D"
        or data_type == "INT32_2D"
    ):
        return attribute_value.vector.copy().freeze()
    if data_type == "FLOAT_COLOR" or data_type == "BYTE_COLOR":
        return attribute_value.color.copy().freeze()
    else:
        return attribute_value.value


def parse_attributes(index, pointcloud, _child):
    values = {}
    for [attribute_name, attribute] in pointcloud.attributes.items():
        if (
            attribute_name == ".reference_index"
            or attribute_name == "type"
            or attribute_name == "subtype"
        ):
            continue
        value = attribute.data[index]
        values[attribute_name] = get_attribute_value(attribute.data_type, value)
    return {"status": "OK", "type": "ATTRIBUTES", "value": values}


def parse_element_bag(type, index, parent_pointcloud, child):
    subtype = None
    subtypes = None
    if type in subtype_type_ids:
        subtypes = subtype_type_ids[type]
    if subtypes is not None:
        subtype_ids_attribute = parent_pointcloud.attributes["subtype"]
        subtype = subtype_ids_attribute.data[index]
        subtype = subtypes[
            get_attribute_value(subtype_ids_attribute.data_type, subtype)
        ]
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "bone")
    value = {}
    concat_to_values(attributes_result, value)
    pointcloud = child.instances_pointcloud()
    instance_references = child.instance_references()
    if pointcloud is None or instance_references is None:
        value["subtype"] = subtype
        return {
            "status": "OK",
            "type": type,
            "subtype": subtype,
            "value": value,
        }

    reference_indices = pointcloud.attributes[".reference_index"]
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, value)
        value["subtype"] = subtype
    return {
        "status": "OK",
        "type": type,
        "subtype": subtype,
        "value": value,
    }


def parse_collection(type_name, index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "OK", "values": []}
    reference_indices = pointcloud.attributes[".reference_index"]
    values = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        values.append(element_result["value"])
    return {"status": "OK", "type": type_name, "value": values}


def parse_selection(index, parent_pointcloud, child):
    mesh = child.mesh
    if mesh is None or "index" not in mesh.attributes:
        return {"status": "ERROR", "message": "Expected indices", "path": ["selection"]}
    bag_result = parse_element_bag("SELECTION", index, parent_pointcloud, child)
    if bag_result["status"] == "ERROR":
        return concat_error_path(bag_result, "selection")
    value = bag_result["value"]
    indices = []
    value["indices"] = indices
    index_attribute = mesh.attributes["index"]
    for v in mesh.vertices:
        indices.append(
            get_attribute_value(
                index_attribute.data_type, index_attribute.data[v.index]
            )
        )
    return {"status": "OK", "value": value}


def parse_element(index, pointcloud, child):
    type_ids_attribute = pointcloud.attributes["type"]
    type = type_ids_attribute.data[index]
    type_id = get_attribute_value(type_ids_attribute.data_type, type)
    type_name = type_ids[type_id]
    match type_name:
        case "OBJECT":
            return parse_object(index, pointcloud, child)
        case "BONE":
            return parse_element_bag("BONE", index, pointcloud, child)
        case "DATA":
            return parse_element_bag("DATA", index, pointcloud, child)
        case "CHILDREN":
            return parse_element_bag("CHILDREN", index, pointcloud, child)
        case "REFERENCE_GEOMETRY":
            return parse_reference_geometry(index, pointcloud, child)
        case "GEOMETRY":
            return parse_element_bag("GEOMETRY", index, pointcloud, child)
        case "MODIFIER":
            return parse_element_bag("MODIFIER", index, pointcloud, child)
        case "CONSTRAINT":
            return parse_element_bag("CONSTRAINT", index, pointcloud, child)
        case "DEPENDENCIES":
            return parse_collection("DEPENDENCIES", index, pointcloud, child)
        case "FALLOFF":
            return parse_element_bag("FALLOFF", index, pointcloud, child)
        case "MATERIALS":
            return parse_collection("MATERIALS", index, pointcloud, child)
        case "CONSTRAINTS":
            return parse_collection("CONSTRAINTS", index, pointcloud, child)
        case "MODIFIERS":
            return parse_collection("MODIFIERS", index, pointcloud, child)
        case "VERTEX_GROUPS":
            return parse_collection("VERTEX_GROUPS", index, pointcloud, child)
        case "VERTEX_GROUP":
            return parse_element_bag("VERTEX_GROUP", index, pointcloud, child)
        case "ATTRIBUTES":
            return parse_attributes(index, pointcloud, child)
        case "SELECTION":
            return parse_selection(index, pointcloud, child)
        case "NAME":
            return parse_name(child)
        case "TARGET":
            return parse_element_bag("TARGET", index, pointcloud, child)
        case "DEPENDENCY":
            return parse_element_bag("DEPENDENCY", index, pointcloud, child)
        case "TARGET_SPACE":
            return parse_element_bag("TARGET_SPACE", index, pointcloud, child)
        case "OWNER_SPACE":
            return parse_element_bag("OWNER_SPACE", index, pointcloud, child)
        case "TARGET_VALUE":
            return parse_element_bag("TARGET_VALUE", index, pointcloud, child)
        case "SUBTARGET_VALUE":
            return parse_element_bag("SUBTARGET_VALUE", index, pointcloud, child)
    return {
        "status": "ERROR",
        "message": f"UNKNOWN TYPE {type_name}, {type_id}",
        "path": [],
    }


def parse_geometry(index, parent_pointcloud, child):
    subtypes = parent_pointcloud.attributes["subtype"]
    if subtypes is None:
        return {
            "status": "ERROR",
            "message": "Geometry is missing subtype value",
            "path": ["geometry"],
        }

    subtype = get_attribute_value(subtypes, subtypes.data[index])
    subtype_name = data_block_type_ids[subtype]
    match subtype_name:
        case "ARMATURE":
            armature_result = parse_element_bag(
                "GEOMETRY", index, parent_pointcloud, child
            )
            if armature_result["status"] == "ERROR":
                return concat_error_path(armature_result, "geometry")
            value = armature_result["value"]
            value["type"] = "GEOMETRY"
            value["subtype"] = "ARMATURE"
            return {"status": "OK", "value": value}
        case "CURVE":
            if child.curves is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "CURVE",
                        "value": child.curves,
                    },
                }
        case "GREASEPENCIL":
            if child.grease_pencil is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "GREASEPENCIL",
                        "value": child.curves,
                    },
                }
        case "MESH":
            if child.mesh is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "MESH",
                        "value": child.mesh,
                    },
                }
        case "POINTCLOUD":
            if child.pointcloud is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "POINTCLOUD",
                        "value": child.pointcloud,
                    },
                }
        case "VOLUME":
            if child.volume is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "VOLUME",
                        "value": child.volume,
                    },
                }
        case "INSTANCE":
            instance_references = child.instance_references()
            instances_pointcloud = child.instances_pointcloud()
            if instance_references is not None and instances_pointcloud is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "INSTANCE",
                        "value": {
                            "pointcloud": instances_pointcloud,
                            "references": instance_references,
                        },
                    },
                }
    return {
        "status": "ERROR",
        "message": "Missing expected geometry data",
        "path": ["geometry"],
    }


def parse_data(index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["data"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "bone")
    value = {}
    concat_to_values(attributes_result, value)
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, value)
        value["type"] = "DATA"
    return {"status": "OK", "value": value}


def concat_to_values(element_result, values):
    if element_result["type"] == "ATTRIBUTES":
        for k, v in element_result["value"].items():
            values[k] = v
    else:
        values[element_result["type"]] = element_result["value"]


def parse_object(index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": []}
    reference_indices = pointcloud.attributes[".reference_index"]
    value = {}
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    concat_to_values(attributes_result, value)
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, value)

    return {
        "status": "OK",
        "type": "OBJECT",
        "value": value,
    }


def parse_reference_geometry(index, parent_pointcloud, child):
    geometry_result = parse_geometry(index, parent_pointcloud, child)
    if geometry_result["status"] == "ERROR":
        return concat_error_path(geometry_result, "reference_geometry")
    return {
        "status": "OK",
        "type": "REFERENCE_GEOMETRY",
        "subtype": geometry_result["value"]["subtype"],
        "value": geometry_result["value"],
    }


def parse_root_object(index, _parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {
            "status": "ERROR",
            "message": "Malformed data",
            "path": [child.name],
        }
    reference_indices = pointcloud.attributes[".reference_index"]
    attributes_result = parse_attributes(index, pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "object")
    values = {}
    concat_to_values(attributes_result, values)

    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)
    objects = []
    if "CHILDREN" not in values:
        values["CHILDREN"] = objects
    if values["DATA"] is None:
        return {
            "status": "ERROR",
            "message": "Missing data",
            "path": ["data"],
        }
    from copy import copy

    obj = copy(values)
    del obj["CHILDREN"]
    objects.insert(
        0,
        obj,
    )
    return {"status": "OK", "type": "OBJECT", "value": values}
