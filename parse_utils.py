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
}

data_block_type_ids = {
    1: "ARMATURE",
    2: "CURVE",
    3: "GREASE_PENCIL",
    4: "MESH",
    5: "POINT_CLOUD",
    6: "VOLUME",
    7: "INSTANCE",
}


def _reverse_dict(d):
    result = dict()
    for k, v in d.items():
        result[v] = k
    return result


reversed_type_ids = _reverse_dict(type_ids)
reversed_data_block_type_ids = _reverse_dict(data_block_type_ids)


def parse_vertex_groups(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {
            "status": "ERROR",
            "message": "Missing vertex_group values",
            "path": ["vertex_groups"],
        }
    reference_indices = pointcloud.attributes[".reference_index"]
    values = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        values.append(child.name)
    return {"status": "OK", "values": values}


def parse_name(child):
    return {"status": "OK", "value": {"type": "NAME", "value": child.name}}


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
        return attribute_value.value.copy().freeze()


def parse_attributes(index, pointcloud, child):
    values = {}
    for [attribute_name, attribute] in pointcloud.attributes.items():
        if attribute_name == ".reference_index":
            continue
        value = attribute.data[index]
        found_values = True
        values[attribute_name] = get_attribute_value(attribute, value)
    if found_values == False:
        return {
            "status": "ERROR",
            "message": "Missing attribute values",
            "path": ["values"],
        }
    return {"status": "OK", "value": {"type": "ATTRIBUTES", "values": values}}


def parse_modifier(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Modifiers are not yet supported",
        "path": ["modifier"],
    }


def parse_modifiers(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Modifiers are not yet supported",
        "path": ["modifiers"],
    }


def parse_constraint(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Constraints are not yet supported",
        "path": ["constraint"],
    }


def parse_constraints(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Constraints are not yet supported",
        "path": ["constraints"],
    }


def parse_dependencies(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Dependencies are not yet supported",
        "path": ["dependencies"],
    }


def parse_dependency(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Dependency is not yet supported",
        "path": ["dependency"],
    }


def parse_falloff(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Falloff is not yet supported",
        "path": ["dependencies"],
    }


def parse_materials(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Materials are not yet supported",
        "path": ["dependencies"],
    }


def parse_vertex_groups(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "VertexGroups are not yet supported",
        "path": ["vertex_groups"],
    }


def parse_selection(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Selection is not yet supported",
        "path": ["selection"],
    }


def parse_space(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Space is not yet supported",
        "path": ["space"],
    }


def parse_target(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Target is not yet supported",
        "path": ["target"],
    }


def parse_target_space(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Target Space is not yet supported",
        "path": ["target_space"],
    }


def parse_owner_space(index, pointcloud, child):
    return {
        "status": "ERROR",
        "message": "Owner Space is not yet supported",
        "path": ["owner_space"],
    }


def parse_element(index, pointcloud, child):
    type_ids = pointcloud.attributes["type"]
    type = type_ids[index]
    type_name = reversed_type_ids[type]
    match type_name:
        case "OBJECT":
            return parse_object(index, pointcloud, child)
        case "BONE":
            return parse_bone(index, pointcloud, child)
        case "DATA":
            return parse_data(index, pointcloud, child)
        case "CHILDREN":
            return parse_children(index, pointcloud, child)
        case "REFERENCE_GEOMETRY":
            return parse_reference_geometry(index, pointcloud, child)
        case "GEOMETRY":
            return parse_geometry(index, pointcloud, child)
        case "MODIFIER":
            return parse_modifier(index, pointcloud, child)
        case "CONSTRAINT":
            return parse_constraint(index, pointcloud, child)
        case "DEPENDENCIES":
            return parse_dependencies(index, pointcloud, child)
        case "FALLOFF":
            return parse_falloff(index, pointcloud, child)
        case "MATERIALS":
            return parse_materials(index, pointcloud, child)
        case "CONSTRAINTS":
            return parse_constraints(index, pointcloud, child)
        case "MODIFIERS":
            return parse_modifiers(index, pointcloud, child)
        case "VERTEX_GROUPS":
            return parse_vertex_groups(index, pointcloud, child)
        case "ATTRIBUTES":
            return parse_attributes(index, pointcloud, child)
        case "SELECTION":
            return parse_selection(index, pointcloud, child)
        case "NAME":
            return parse_name(child)
        case "TARGET":
            return parse_target(index, pointcloud, child)
        case "DEPENDENCY":
            return parse_dependency(index, pointcloud, child)
        case "TARGET_SPACE":
            return parse_target_space(index, pointcloud, child)
        case "OWNER_SPACE":
            return parse_owner_space(index, pointcloud, child)


def parse_bone(index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed bone", "path": []}
    values = {}
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "bone")
    concat_to_values(attributes_result, values)
    reference_indices = pointcloud.attributes[".reference_index"]
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)

    return {"status": "OK", "value": {"type": "BONE", "values": values}}


def parse_armature(index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["armature"]}
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "bone")
    values = {}
    concat_to_values(attributes_result, values)
    reference_indices = pointcloud.attributes[".reference_index"]
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)
    return {"status": "OK", "value": {"type": "ARMATURE", "values": values}}


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
            armature_result = parse_armature(index, parent_pointcloud, child)
            if armature_result["status"] == "ERROR":
                return concat_error_path(armature_result, "geometry")
            return {
                "status": "OK",
                "value": {
                    "type": "GEOMETRY",
                    "subtype": "ARMATURE",
                    "value": armature_result["value"]["values"],
                },
            }
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
        case "GREASE_PENCIL":
            if child.grease_pencil is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "GREASE_PENCIL",
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
        case "POINT_CLOUD":
            if child.pointcloud is not None:
                return {
                    "status": "OK",
                    "value": {
                        "type": "GEOMETRY",
                        "subtype": "POINT_CLOUD",
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
    values = {}
    concat_to_values(attributes_result, values)
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)
    return {"status": "OK", "values": {"type": "DATA", "values": values}}


def concat_to_values(element_result, values):
    if element_result["value"]["type"] == "ATTRIBUTES":
        for k, v in element_result["value"]["values"].items():
            values[k] = v
    else:
        values[element_result["value"]["type"]] = element_result["value"]


def parse_object(index, parent_pointcloud, child):
    parents = parent_pointcloud.attributes["parent"]

    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": []}
    reference_indices = pointcloud.attributes[".reference_index"]
    values = {}
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    concat_to_values(attributes_result, values)
    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)
    return {
        "status": "OK",
        "value": {"type": "OBJECT", "values": values},
    }


def parse_children(_index, pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["children"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    children = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        attributes_result = parse_attributes(i.value, pointcloud, child)
        if attributes_result["status"] == "ERROR":
            return concat_error_path(attributes_result, child.name)
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        children.append(element_result["value"])
    return {"status": "OK", "values": {"type": "CHILDREN", "values": children}}


def parse_reference_geometry(index, parent_pointcloud, child):
    geometry_result = parse_geometry(index, parent_pointcloud, child)
    if geometry_result["status"] == "ERROR":
        return concat_error_path(geometry_result, "reference_geometry")
    return {
        "status": "OK",
        "value": {
            "type": "REFERENCE_GEOMETRY",
            "subtype": geometry_result["value"]["subtype"],
            "value": geometry_result["value"],
        },
    }


def parse_root_object(index, parent_pointcloud, child):
    pointcloud = child.instances_pointcloud()
    instance_references: list = child.instance_references()
    if pointcloud is None or instance_references is None:
        return {
            "status": "ERROR",
            "message": "Malformed data",
            "path": [child.name],
        }
    reference_indices = pointcloud.attributes[".reference_index"]
    attributes_result = parse_attributes(index, parent_pointcloud, child)
    if attributes_result["status"] == "ERROR":
        return concat_error_path(attributes_result, "bone")
    values = {}
    concat_to_values(attributes_result, values)

    for i in reference_indices.data:
        child = instance_references[i.value]
        element_result = parse_element(i.value, pointcloud, child)
        if element_result["status"] == "ERROR":
            return concat_error_path(element_result, child.name)
        concat_to_values(element_result, values)

    objects = []
    if values["CHILDREN"] is not None:
        objects = values["CHILDREN"]["values"]
    else:
        values["CHILDREN"] = {"type": "CHILDREN", "values": objects}
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
    values["type"] = "OBJECT"
    return {"status": "OK", "value": values}
