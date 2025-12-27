import bpy
import mathutils


def find_output_sockets(socket: bpy.types.NodeSocket, node_tree: bpy.types.NodeTree):
    result = []
    for node in node_tree.nodes:
        if node.bl_idname == "NodeGroupOutput":
            group_output: bpy.types.NodeEnableOutput = node  # type: ignore
            for input in group_output.inputs:
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
            if link.from_node and link.from_node.bl_idname is not "NodeGroupInput"
        ]
    )
    return result


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
        target_to_node = target_node_tree.nodes[node_mapping[to_node.name]]
        if from_node.name not in node_mapping:
            new_node = target_node_tree.nodes.new(from_node.bl_idname)
            new_node.copy(from_node)
            node_mapping[from_node.name] = new_node.name
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
                            pass
                        case "BUNDLE" | "CLOSURE" | "GEOMETRY" | "ROTATION":
                            pass
                        case "MATRIX":
                            pass
                        case "INT":
                            pass
                        case "VECTOR":
                            pass
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


def copy_and_ungroup_node_group(
    source_node: bpy.types.Node,
    source_node_tree: bpy.types.NodeTree,
    target_node_tree: bpy.types.NodeTree,
):
    node_mapping: dict[str, str] = dict()
    copy_node_tree(node_mapping, source_node, source_node_tree, target_node_tree)
    has_node_group = True
    new_nodes = list(node_mapping.values())
    while has_node_group:
        has_node_group = False
        prev_new_nodes = new_nodes
        for node_name in prev_new_nodes:
            node: bpy.types.GeometryNodeGroup = target_node_tree.nodes[node_name]  # type: ignore
            if node.bl_idname != "GeometryNodeGroup":
                continue
            has_node_group = True
            node_mapping: dict[str, str] = dict()
            ungroup_node_group(node_mapping, node, target_node_tree)
            new_nodes.extend(node_mapping.values())
