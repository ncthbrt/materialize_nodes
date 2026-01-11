import bpy


def copy_interface_input_items(
    source_interface: bpy.types.NodeTreeInterface,
    target_interface: bpy.types.NodeTreeInterface,
    mapping: bpy.types.CollectionProperty,
):
    target_stack = []
    source_stack = []
    seen_geometry_input = False
    for item in source_interface.items_tree:
        while len(source_stack) > 0 and (
            item.parent.name == "" or source_stack[-1] != item.parent
        ):
            source_stack.pop()
            target_stack.pop()
        if item.item_type == "PANEL":
            has_input = False
            for subitem in item.interface_items:
                if subitem.item_type == "SOCKET" and subitem.in_out == "INPUT":
                    has_input = True
                    break
            if not has_input:
                continue
            panel = target_interface.new_panel(
                name=item.name,
                description=item.description,
                default_closed=item.default_closed,
            )
            if len(source_stack) == 0:
                source_stack.append(item)
                target_stack.append(panel)
            elif source_stack[-1] == item.parent:
                source_stack.append(item)
                target_stack.append(panel)
                target_interface.move_to_parent(
                    panel, target_stack[-1], len(target_stack[-1].interface_items)
                )
        elif item.item_type == "SOCKET":
            if item.in_out == "OUTPUT":
                continue
            socket = None
            match item.socket_type:
                case (
                    "NodeSocketImage"
                    | "NodeSocketMaterial"
                    | "NodeSocketObject"
                    | "NodeSocketCollection"
                    | "NodeSocketMaterial"
                ):
                    socket: bpy.types.NodeTreeInterfaceSocket = (
                        target_interface.new_socket(
                            item.name, in_out="INPUT", socket_type="NodeSocketGeometry"
                        )
                    )
                case _:
                    socket: bpy.types.NodeTreeInterfaceSocket = target_interface.copy(
                        item
                    )  # type: ignore
            mapping[socket.identifier] = item.socket_type
            if len(target_stack) > 0:
                target_interface.move_to_parent(
                    socket,
                    target_stack[-1],
                    len(target_stack[-1].interface_items),
                )
