import bpy
import mathutils


def find_output_sockets(socket: bpy.types.NodeSocket, node_tree: bpy.types.NodeTree):
    result = []
    for node in node_tree.nodes:
        if node.bl_idname == "NodeGroupOutput":
            for input in node.inputs:
                if input.identifier == socket.identifier:
                    result.append(input)
    return result


def get_incoming_links(
    socket: bpy.types.NodeSocket, node_tree: bpy.types.NodeTree
) -> list[bpy.types.NodeLink]:
    if socket.links is None:
        return []
    result = []
    result.extend(
        [
            link
            for link in socket.links
            if link.from_node and link.from_node.bl_idname != "NodeGroupInput"
        ]
    )
    return result


def copy_node(from_node: bpy.types.Node, node_mapping, target_node_tree):
    new_node = target_node_tree.nodes.new(from_node.bl_idname)
    name = new_node.name
    node_mapping[from_node.name] = name
    for k, p in from_node.rna_type.properties.items():
        if k == "name" or p.is_readonly:
            continue
        #        if not from_node.is_property_readonly(k):
        setattr(new_node, k, getattr(from_node, k))
    for k in from_node.keys():
        setattr(new_node, k, getattr(from_node, k))
    return new_node


def clear_group(target_node_tree):
    for node in reversed(target_node_tree.nodes):
        target_node_tree.nodes.remove(node)


def copy_node_tree(
    node_mapping: dict[str, str],
    source_node: bpy.types.Node,
    source_node_tree: bpy.types.NodeTree,
    target_node_tree: bpy.types.NodeTree,
):
    remaining_links = []

    for input in source_node.inputs:
        remaining_links.extend(get_incoming_links(input, source_node_tree))

    while len(remaining_links) > 0:
        link = remaining_links.pop(0)
        from_node = link.from_node
        from_socket = link.from_socket
        to_socket = link.to_socket
        to_node = link.to_node
        if (
            from_node is None
            or to_socket is None
            or to_node is None
            or from_socket is None
        ):
            continue
        if to_node.name not in node_mapping:
            copy_node(to_node, node_mapping, target_node_tree)
        target_to_node = target_node_tree.nodes[node_mapping[to_node.name]]
        if from_node.bl_idname == "NodeGroupInput":
            continue
        if from_node.name not in node_mapping:
            copy_node(from_node, node_mapping, target_node_tree)
            for input in from_node.inputs:
                remaining_links.extend(get_incoming_links(input, source_node_tree))
        target_from_node = target_node_tree.nodes[node_mapping[from_node.name]]
        if target_to_node is None:
            continue
        target_to_socket = None
        target_from_socket = None
        for input in target_to_node.inputs:
            if to_socket.identifier == input.identifier:
                target_to_socket = input
        for output in target_from_node.outputs:
            if from_socket.identifier == input.identifier:
                target_from_socket = output
        if target_to_socket and target_from_socket:
            target_node_tree.links.new(target_from_socket, target_to_socket)


def ungroup_node_group(
    node_mapping: dict[str, str],
    source_node_group: bpy.types.GeometryNodeGroup,
    target_node_tree: bpy.types.NodeTree,
):
    source_node_tree = source_node_group.node_tree
    if source_node_tree is None:
        return
    for node in source_node_tree.nodes:
        if node.bl_idname == "NodeGroupOutput":
            copy_node_tree(
                node_mapping, node, source_node_tree, target_node_tree
            )  # copy the nodes from source_node_tree into node tree, along with all their connections
    for node in source_node_tree.nodes:
        if node.name not in node_mapping:
            continue
        if node.bl_idname == "NodeGroupOutput":
            # We need to create links between the sockets being fed to the output
            # node and usage
            new_output_node_name = node_mapping[node.name]
            new_output_node = target_node_tree.nodes[new_output_node_name]
            if new_output_node is None:
                continue
            for output in source_node_group.outputs:
                if output.links is None:
                    continue  # No links mean unused output
                for link in output.links:
                    if link.to_node is None:
                        continue  # to do warn, should be a node
                    # This has been added to node_tree so we're good
                    to_socket: bpy.types.NodeSocket = link.to_socket  # type: ignore
                    from_socket_identifier: str = link.from_socket.identifier  # type: ignore
                    target_node_tree.links.remove(
                        link
                    )  # We need to remove the existing link
                    from_socket: bpy.types.NodeSocket = node.outputs[
                        from_socket_identifier
                    ]
                    target_node_tree.links.new(input=to_socket, output=from_socket)
                    new_output_node.outputs[to_socket.identifier]
        elif node.bl_idname == "NodeGroupInput":
            for output in node.outputs:
                # We need to create a link between the values being fed to the input
                # socket and usage, or if no values are being fed to the input socket,
                # then create a value node to connect to the usages
                if (
                    not output.links
                    or output.identifier not in source_node_group.inputs
                ):
                    continue
                input_source_socket: None | bpy.types.NodeSocket = (
                    source_node_group.inputs[output.identifier]
                )
                if (
                    input_source_socket.links is None
                    or len(input_source_socket.links) == 0
                ):
                    # TODO: Create a default value node and link to output OR set default value in input
                    # linked node to input default value
                    # Special case: Matrix, which can use instance transform as input
                    # Special case: Int, which can use instance "index: OR "ID or Index" as input
                    # Special case: Vector, which can use instance "Normal" OR "Position" OR "Left Handle" OR "Right Handle" as input
                    match input_source_socket.type:
                        case (
                            "BOOLEAN"
                            | "COLLECTION"
                            | "CUSTOM"
                            | "IMAGE"
                            | "MATERIAL"
                            | "MENU"
                            | "OBJECT"
                            | "RGBA"
                            | "TEXTURE"
                            | "VALUE"
                        ):
                            default_value = input_source_socket.default_value  # type: ignore
                            for link in output.links:
                                if not link.to_node or not link.to_socket:
                                    continue
                                node = target_node_tree.nodes[
                                    node_mapping[link.to_node.name]
                                ]
                                node.inputs[link.to_socket.identifier].default_value = default_value  # type: ignore
                        case "BUNDLE" | "CLOSURE" | "GEOMETRY" | "ROTATION":
                            # No values to set here
                            pass
                        case "MATRIX":
                            matrix_socket: bpy.types.NodeTreeInterfaceSocketMatrix = source_node_tree.interface.items_tree[input_source_socket.identifier]  # type: ignore
                            match matrix_socket.default_input:
                                case "INSTANCE_TRANSFORM":
                                    transform_node: bpy.types.GeometryNodeInstanceTransform = target_node_tree.nodes.new("GeometryNodeInstanceTransform")  # type: ignore
                                    output_socket = transform_node.outputs[0]
                                    for link in output.links:
                                        if not link.to_node or not link.to_socket:
                                            continue
                                        node = target_node_tree.nodes[
                                            node_mapping[link.to_node.name]
                                        ]
                                        target_node_tree.links.new(
                                            output=output_socket,
                                            input=node.inputs[
                                                link.to_socket.identifier
                                            ],
                                        )
                                case "VALUE":
                                    pass  # No values to set here
                        case "INT":
                            int_socket: bpy.types.NodeTreeInterfaceSocketInt = source_node_tree.interface.items_tree[input_source_socket.identifier]  # type: ignore
                            output_socket = None
                            match int_socket.default_input:
                                case "INDEX":
                                    index_node: bpy.types.GeometryNodeInputIndex = target_node_tree.nodes.new("GeometryNodeInputIndex")  # type: ignore
                                    output_socket = index_node.outputs[0]
                                case "ID_OR_INDEX":
                                    id_node: bpy.types.GeometryNodeInputID = target_node_tree.nodes.new("GeometryNodeInputID")  # type: ignore
                                    output_socket = id_node.outputs[0]
                                case "VALUE":
                                    int_node: bpy.types.FunctionNodeInputInt = target_node_tree.nodes.new("FunctionNodeInputInt")  # type: ignore
                                    int_node.integer = input_source_socket.default_value  # type: ignore
                                    output_socket = int_node.outputs[0]
                                    pass  # No values to set here
                            for link in output.links:
                                if not link.to_node or not link.to_socket:
                                    continue
                                node = target_node_tree.nodes[
                                    node_mapping[link.to_node.name]
                                ]
                                target_node_tree.links.new(
                                    output=output_socket,  # type: ignore
                                    input=node.inputs[link.to_socket.identifier],
                                )
                        case "VECTOR":
                            vector_socket: bpy.types.NodeTreeInterfaceSocketVector = source_node_tree.interface.items_tree[input_source_socket.identifier]  # type: ignore
                            output_socket = None
                            match vector_socket.default_input:
                                case "HANDLE_LEFT":
                                    handle_node: bpy.types.GeometryNodeInputCurveHandlePositions = target_node_tree.nodes.new("GeometryNodeInputCurveHandlePositions")  # type: ignore
                                    output_socket = handle_node.outputs[0]
                                case "HANDLE_RIGHT":
                                    handle_node: bpy.types.GeometryNodeInputCurveHandlePositions = target_node_tree.nodes.new("GeometryNodeInputCurveHandlePositions")  # type: ignore
                                    output_socket = handle_node.outputs[1]
                                case "NORMAL":
                                    pass
                                case "POSITION":
                                    pass
                                case "VALUE":
                                    vector_node: bpy.types.FunctionNodeInputVector = target_node_tree.nodes.new("FunctionNodeInputVector")  # type: ignore
                                    vector_node.vector = input_source_socket.default_value  # type: ignore
                                    output_socket = vector_node.outputs[0]
                                    pass  # No values to set here
                            for link in output.links:
                                if not link.to_node or not link.to_socket:
                                    continue
                                node = target_node_tree.nodes[
                                    node_mapping[link.to_node.name]
                                ]
                                target_node_tree.links.new(
                                    output=output_socket,  # type: ignore
                                    input=node.inputs[link.to_socket.identifier],
                                )
                elif len(input_source_socket.links) > 1:
                    # Warn as a node group input socket should only ever have at most one link
                    # unless blender allows multi-input sockets in future
                    pass
                else:
                    link = input_source_socket.links[0]
                    if link.from_socket is None or link.from_node is None:
                        continue
                    from_node = target_node_tree.nodes[
                        node_mapping[link.from_node.name]
                    ]
                    if from_node is None:
                        continue  # to do warn, should be a node
                    from_socket_identifier = link.from_socket.identifier
                    output_socket = from_node.outputs[from_socket_identifier]
                    if output_socket is None:
                        continue  # to do warn, should be a socket
                    for link in output.links:
                        if link.to_socket is None or link.to_node is None:
                            continue  # to do warn, should be a socket or node
                        input_socket_identifier = link.to_socket.identifier
                        to_node = target_node_tree.nodes[
                            node_mapping[link.to_node.name]
                        ]
                        input_socket = to_node.inputs[input_socket_identifier]
                        target_node_tree.links.new(
                            input=input_socket, output=output_socket
                        )
    target_node_tree.nodes.remove(source_node_group)  # remove unneeded group at the end


# def copy_and_ungroup_node_group(
#     source_node: bpy.types.Node,
#     source_node_tree: bpy.types.NodeTree,
#     target_node_tree: bpy.types.NodeTree,
# ):
#     node_mapping: dict[str, str] = dict()
#     copy_node_tree(node_mapping, source_node, source_node_tree, target_node_tree)
#     has_node_group = True
#     new_nodes = list(node_mapping.values())
#     while has_node_group:
#         has_node_group = False
#         prev_new_nodes = list(new_nodes)
#         new_nodes = []
#         for node_name in prev_new_nodes:
#             node: bpy.types.GeometryNodeGroup = target_node_tree.nodes[node_name]  # type: ignore
#             if node.bl_idname != "GeometryNodeGroup":
#                 continue
#             has_node_group = True
#             node_mapping: dict[str, str] = dict()
#             ungroup_node_group(node_mapping, node, target_node_tree)
#             new_nodes.extend(node_mapping.values())

# def create_geo_nodes_region():
#     context.window.screen.areas


def copy_and_ungroup_node_group(
    context: bpy.types.Context,
    source_node: bpy.types.Node,
    source_node_tree: bpy.types.NodeTree,
):
    source_node_tree = source_node_tree.copy()
    source_node = source_node_tree.nodes[source_node.name]
    node_modifier = context.active_object.modifiers.new("TempModifier", "NODES")
    node_modifier.node_group = source_node_tree
    node_modifier.is_active = True
    bpy.ops.screen.area_split()
    area = context.area
    area.type = "NODE_EDITOR"
    rg = area.regions[0]
    context_override = context.copy()
    context_override["area"] = area
    context_override["region"] = rg
    context_override["selected_nodes"] = list(source_node_tree.nodes)
    try:        
        with context.temp_override(**context_override):
            if bpy.ops.node.group_ungroup.poll("INVOKE_AREA"):
                bpy.ops.node.group_ungroup("INVOKE_AREA")
            
    finally:
        #        pass
        context.object.modifiers.remove(node_modifier)
        bpy.ops.screen.area_close()


# clear_group(bpy.data.node_groups["Test"])
copy_and_ungroup_node_group(
    bpy.context,
    bpy.data.node_groups["TestGeoNode"].nodes["GroupOutput"],
    bpy.data.node_groups["TestGeoNode"],
)

# TODO: Account for modifier inputs
# for window in bpy.context.window_manager.windows:
#    for area in window.screen.areas:
#        for space in area.spaces:
#            print(space.type)
