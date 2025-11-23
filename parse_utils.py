import bpy


def concat_error_path(error, part):
    if len(part) > 0:
        error["path"].insert(0, part)
    return error


type_ids = {
    1: "OBJECT",
    2: "BONE",
    3: "DATA",
    4: "PROPERTIES",
    5: "CHILDREN",
    6: "REFERENCE_GEOMETRY",
    7: "GEOMETRY",
}

data_block_type_ids = {
    0: "ARMATURE",
    1: "CURVE",
    2: "GREASE_PENCIL",
    3: "MESH",
    4: "POINT_CLOUD",
    5: "VOLUME",
    6: "INSTANCE",
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


def parse_name(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Missing name", "path": ["name"]}
    if instance_references is None:
        return {"status": "ERROR", "message": "Missing name", "path": ["name"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    for i in reference_indices.data:
        child = instance_references[i.value]
        return {"status": "OK", "value": child.name}
    return {"status": "ERROR", "message": "Missing name", "path": ["name"]}


def parse_attribute_values(pointcloud, instance_references, values):
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
            values[attribute_name] = get_attribute_value(attribute, attribute_value)
    if found_values == False:
        return {
            "status": "ERROR",
            "message": "Missing attribute values",
            "path": ["values"],
        }
    return {"status": "OK", "values": values}


def get_attribute_value(data_type, attribute_value):
    if (
        data_type == "FLOAT_VECTOR"
        or data_type == "FLOAT2"
        or data_type == "INT16_2D"
        or data_type == "INT32_2D"
    ):
        return attribute_value.vector
    if data_type == "FLOAT_COLOR" or data_type == "BYTE_COLOR":
        return attribute_value.color
    else:
        return attribute_value.value


def parse_attributes(geometry_set, values):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["attributes"]}
    values_result = parse_attribute_values(pointcloud, instance_references, values)
    if values_result["status"] == "ERROR":
        return concat_error_path(values_result, "attributes")

    return {"status": "OK", "values": values}


def parse_properties(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["properties"]}
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
    return {"status": "OK", "values": values}


def parse_bone(geometry_set, bone):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed bone", "path": []}
    reference_indices = pointcloud.attributes[".reference_index"]
    types = pointcloud.attributes["type"]
    properties = None
    for i, type in zip(reference_indices.data, types.data):
        child = instance_references[i.value]
        if reversed_type_ids["PROPERTIES"] == type.value:
            properties_result = parse_properties(child)
            if properties_result["status"] == "ERROR":
                return concat_error_path(properties_result, "data")
            properties = properties_result["values"]
    if properties is None:
        return {
            "status": "ERROR",
            "message": "Missing properties",
            "path": ["properties"],
        }
    bone["properties"] = properties
    return {"status": "OK", "value": bone}


def parse_bones(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["attributes"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    num_bones = pointcloud.attributes.domain_size("INSTANCE")
    bones = [dict()] * num_bones
    index = 0
    for [attribute_name, attribute] in pointcloud.attributes.items():
        if attribute_name == ".reference_index":
            continue
        elif attribute_name == "instance_transform":
            for i, attribute_value in zip(range(num_bones), attribute.data):
                bones[i]["transform"] = attribute_value.value.copy().freeze()
        else:
            bones[i]["properties"] = attribute_value.value
        index += 1
    index = 0
    for i in reference_indices.data:
        child = instance_references[i.value]
        bone_result = parse_bone(child, bones[index])
        if bone_result["status"] == "ERROR":
            return concat_error_path(bone_result, index)
        bones[index] = bone_result["value"]
        index += 1
    return {
        "status": "OK",
        "values": bones,
    }


def parse_armature(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    bones = []
    properties = None
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["attributes"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    type_ids = pointcloud.attributes["type"]
    for i, type_id in zip(reference_indices.data, type_ids.data):
        child = instance_references[i.value]
        if reversed_data_block_type_ids["CHILDREN"] == type_id.value:
            bones_result = parse_bones(child)
            if bones_result["status"] == "ERROR":
                return concat_error_path(bones_result, "children")
            bones = bones_result["values"]
        if reversed_type_ids["PROPERTIES"] == type_id.value:
            properties_result = parse_properties(child)
            if properties_result["status"] == "ERROR":
                return concat_error_path(properties_result, "properties")
            properties = properties_result["values"]
    if bones is None:
        return {
            "status": "ERROR",
            "message": "Missing bones",
            "path": ["data", "bones"],
        }
    if properties is None:
        return {
            "status": "ERROR",
            "message": "Missing properties",
            "path": ["data", "properties"],
        }
    return {
        "status": "ERROR",
        "message": "Armatures are not yet supported",
        "path": [],
    }


def parse_geometry(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    data_type = None
    values = None
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["attributes"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    type_ids = pointcloud.attributes["type"]
    index = 0
    for i, type_id in zip(reference_indices.data, type_ids.data):
        data_type = data_block_type_ids[type_id.value]
        child = instance_references[i.value]
        if data_type == "ARMATURE":
            armature_result = parse_armature(child)
            if armature_result["status"] == "ERROR":
                return concat_error_path(armature_result, "geometry")
            values = armature_result["values"]
        else:
            values = instance_references[i.value]
    if values is None:
        return {"status": "ERROR", "message": "Missing geometry", "path": ["geometry"]}
    if data_type is None:
        return {
            "status": "ERROR",
            "message": "Missing geometry type",
            "path": ["geometry", "type"],
        }
    return {"status": "OK", "values": {"type": data_type, "values": values}}


def parse_object_data(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["data"]}

    reference_indices = pointcloud.attributes[".reference_index"]
    type_ids = pointcloud.attributes["type"]
    geometry = None
    properties = None
    for i, type_id in zip(reference_indices.data, type_ids.data):
        child = instance_references[i.value]
        if reversed_type_ids["GEOMETRY"] == type_id.value:
            geometry_result = parse_geometry(child)
            if geometry_result["status"] == "ERROR":
                return concat_error_path(geometry_result, "data")
            geometry = geometry_result["values"]
        elif reversed_type_ids["PROPERTIES"] == type_id.value:
            properties_result = parse_properties(child)
            if properties_result["status"] == "ERROR":
                return concat_error_path(properties_result, "data")
            properties = properties_result["values"]
    if geometry is None:
        return {
            "status": "ERROR",
            "message": "Missing geometry data",
            "path": ["data", "geometry"],
        }
    if properties is None:
        return {
            "status": "ERROR",
            "message": "Missing properties",
            "path": ["data", "properties"],
        }

    return {"status": "OK", "values": {"geometry": geometry, "properties": properties}}


def parse_object(transform, parent, geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": []}
    reference_indices = pointcloud.attributes[".reference_index"]
    type_ids = pointcloud.attributes["type"]
    properties = None
    data = None
    for i, type_id in zip(reference_indices.data, type_ids.data):
        child = instance_references[i.value]
        if reversed_type_ids["PROPERTIES"] == type_id.value:
            properties_result = parse_properties(child)
            if properties_result["status"] == "ERROR":
                return concat_error_path(properties_result, "properties")
            properties = properties_result["values"]
        elif reversed_type_ids["DATA"] == type_id.value:
            data_result = parse_object_data(child)
            if data_result["status"] == "ERROR":
                return concat_error_path(properties_result, "data")
            data = data_result["values"]
    if data is None:
        return {"status": "ERROR", "message": "Missing data", "path": ["data"]}
    if properties is None:
        return {
            "status": "ERROR",
            "message": "Missing properties",
            "path": ["properties"],
        }

    return {
        "status": "OK",
        "values": {
            "data": data,
            "properties": properties,
            "transform": transform,
            "parent": parent,
        },
    }


def parse_children_objects(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["children"]}
    reference_indices = pointcloud.attributes[".reference_index"]
    instance_transforms = pointcloud.attributes["instance_transform"]
    parents = pointcloud.attributes["parent"]
    children = []
    for transform, i, parent in zip(
        instance_transforms.data, reference_indices.data, parents.data
    ):
        child = instance_references[i.value]
        object_result = parse_object(
            transform.value.copy().freeze(), parent.value, child
        )
        if object_result["status"] == "ERROR":
            return concat_error_path(object_result, child.name)
        children.append(object_result["values"])
    return {"status": "OK", "values": children}


def parse_reference_geometry(geometry_set):
    return {"status": "OK", "values": geometry_set.mesh}


def parse_root_object(transform, geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {
            "status": "ERROR",
            "message": "Malformed data",
            "path": [geometry_set.name],
        }
    reference_indices = pointcloud.attributes[".reference_index"]
    types = pointcloud.attributes["type"]
    children = None
    properties = None
    data = None
    reference_geometry = None
    for i, type in zip(reference_indices.data, types.data):
        child = instance_references[i.value]
        type_id = type.value
        if reversed_type_ids["PROPERTIES"] == type_id:
            properties_result = parse_properties(child)
            if properties_result["status"] == "ERROR":
                return concat_error_path(properties_result, geometry_set.name)
            properties = properties_result["values"]
        elif reversed_type_ids["DATA"] == type_id:
            data_result = parse_object_data(child)
            if data_result["status"] == "ERROR":
                return concat_error_path(data_result, geometry_set.name)
            data = data_result["values"]
        elif reversed_type_ids["CHILDREN"] == type_id:
            children_result = parse_children_objects(child)
            if children_result["status"] == "ERROR":
                return concat_error_path(children_result, geometry_set.name)
            children = children_result["values"]
        elif reversed_type_ids["REFERENCE_GEOMETRY"] == type_id:
            reference_geometry_result = parse_reference_geometry(child)
            if reference_geometry_result["status"] == "ERROR":
                return concat_error_path(reference_geometry_result, geometry_set.name)
            reference_geometry = reference_geometry_result["values"]
        else:
            continue

    if children is not None:
        objects = children
    else:
        objects = []
    if properties is None:
        return {
            "status": "ERROR",
            "message": "Missing properties",
            "path": ["properties"],
        }
    if data is None:
        return {
            "status": "ERROR",
            "message": "Missing data",
            "path": ["data"],
        }
    objects.insert(
        0,
        {
            "data": data,
            "properties": properties,
            "parent": -1,
            "transform": transform.copy().freeze(),
        },
    )
    return {
        "status": "OK",
        "values": {
            "objects": objects,
            "reference_geometry": reference_geometry,
            "transform": transform.copy().freeze(),
        },
    }
