import bpy
import bpy.types


def concat_error_path(error, part):
    error["path"].append(part)
    return error


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
            values[attribute_name] = attribute_value.value
    if found_values == False:
        return {
            "status": "ERROR",
            "message": "Missing attribute values",
            "path": ["values"],
        }
    print(values)
    return {"status": "OK", "values": values}


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


def parse_object(geometry_set):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": []}

    reference_indices = pointcloud.attributes[".reference_index"]

    values = []
    for i in reference_indices.data:
        child = instance_references[i.value]
        name = child.name
        if name == "properties":
            parse_properties()

    return {"status": "OK", "values": values}


def parse_children(geometry_set, values):
    pointcloud = geometry_set.instances_pointcloud()
    instance_references: list = geometry_set.instance_references()
    if pointcloud is None or instance_references is None:
        return {"status": "ERROR", "message": "Malformed data", "path": ["children"]}
    return {"status": "OK", values: []}
