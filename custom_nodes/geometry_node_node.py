import bpy
import mathutils

exclude_nodes = (
    "Materialize Template [materialize.blend]",
    "Prepare Materialization [materialize.blend]",
)


def filter_node_group(self, obj: bpy.types.NodeTree):
    if obj.type == "GEOMETRY":
        return obj.is_modifier and obj.name_full not in exclude_nodes  # type: ignore
    return False


class MTLZ_NG_GN_GeometryNodeNode(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_GeometryNodeNode"
    bl_label = "Geometry Node"
    bl_description = """Creates a target to reference objects and bones that are not managed by materialize"""
    tree_type = "GeometryNodeTree"
    initialized: bpy.props.BoolProperty(name="Initialized")
    color_tag = "INPUT"

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
        if self.initialized:
            self.register_busses()

    def register_busses(self):
        pass

    def setup_connections_and_outputs(self):
        from ..materialize_blend_loader import load_node_group

        if self.referenced_node_tree == None:
            return
        input_node = self.node_tree.nodes.new("NodeGroupInput")
        input_node.location = mathutils.Vector((0, 500))
        to_instance_node = self.node_tree.nodes.new("GeometryNodeGeometryToInstance")
        to_instance_node.location = mathutils.Vector((0, 0))
        prev_socket = to_instance_node.outputs[0]
        index = -1
        for output in input_node.outputs:
            index = index + 1
            if not isinstance(output, bpy.types.NodeSocketVirtual):
                match output.type:
                    case (
                        "BOOLEAN"
                        | "INT"
                        | "MATRIX"
                        | "RGBA"
                        | "ROTATION"
                        | "VALUE"
                        | "VECTOR"
                        | "STRING"
                    ):
                        group = load_node_group(f"MTLZ_Node Store {output.type}")
                        geometry_node_group: bpy.types.GeometryNodeGroup = self.node_tree.nodes.new("GeometryNodeGroup")  # type: ignore
                        geometry_node_group.node_tree = group
                        geometry_node_group.location = mathutils.Vector(
                            ((index + 1) * 300, 0)
                        )
                        name_socket: bpy.types.NodeSocketString = (
                            geometry_node_group.inputs[1]
                        )
                        name_socket.default_value = output.name
                        input_socket = geometry_node_group.inputs[0]
                        self.node_tree.links.new(input=input_socket, output=prev_socket)
                        input_socket = geometry_node_group.inputs[2]
                        output_socket = input_node.outputs[index]
                        self.node_tree.links.new(
                            input=input_socket, output=output_socket
                        )
                        prev_socket = geometry_node_group.outputs[0]
                    case "IMAGE" | "MATERIAL" | "OBJECT":
                        print("UNSUPPORTED YET")
        prepare_node = load_node_group("MTLZ_Prepare Geometry Node")
        prepare_node_group: bpy.types.GeometryNodeGroup = self.node_tree.nodes.new("GeometryNodeGroup")  # type: ignore
        prepare_node_group.node_tree = prepare_node
        prepare_node_group.location = mathutils.Vector(((index + 1) * 300, 0))
        output_node: bpy.types.NodeGroupOutput = self.node_tree.nodes.new("NodeGroupOutput")  # type: ignore
        output_node.location = mathutils.Vector(((index + 2) * 300, 0))

        self.node_tree.links.new(
            output=prepare_node_group.outputs[0], input=output_node.inputs[0]
        )
        self.node_tree.links.new(output=prev_socket, input=prepare_node_group.inputs[0])
        prepare_node_group.inputs[1].default_value = self.referenced_node_tree.name_full

    def copy_interface_input_items(
        self,
        source_interface: bpy.types.NodeTreeInterface,
        target_interface: bpy.types.NodeTreeInterface,
    ):
        target_stack = []
        source_stack = []
        seen_geometry_input = False
        for item in source_interface.items_tree:
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
                elif item.parent.name != "":
                    source_stack.pop()
                    target_stack.pop()
            elif item.item_type == "SOCKET":
                if item.in_out == "OUTPUT":
                    continue
                if item.socket_type == "NodeSocketGeometry" and not seen_geometry_input:
                    seen_geometry_input = True
                    continue
                socket: bpy.types.NodeTreeInterfaceSocket = target_interface.copy(item)
                if len(target_stack) > 0:
                    target_interface.move_to_parent(
                        socket, target_stack[-1], len(target_stack[-1].interface_items)
                    )

    def clear_node_group(self):
        for item in reversed(self.node_tree.interface.items_tree):
            if item.item_type == "SOCKET" and item.in_out == "OUTPUT":
                continue
            self.node_tree.interface.remove(item)

        for node in reversed(self.node_tree.nodes):
            self.node_tree.nodes.remove(node)

    def update_node_group(self, context):
        self.clear_node_group()
        if self.referenced_node_tree == None:
            return

        self.copy_interface_input_items(
            self.referenced_node_tree.interface, self.node_tree.interface
        )

        self.setup_connections_and_outputs()

    def update_signal(self, context):
        if self.initialized:
            self.update_node_group(context)

    referenced_node_tree: bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        name="Node Tree",
        description="The node tree to be linked",
        update=update_signal,
        poll=filter_node_group,
    )  # pyright: ignore[reportInvalidTypeForm]

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        # from ..materialize_blend_loader import load_node_group
        self.node_tree = bpy.data.node_groups.new(
            f"{self.name} Impl", "GeometryNodeTree"
        )  # type: ignore

        self.node_tree.interface.new_socket(
            "Geometry Node", in_out="OUTPUT", socket_type="NodeSocketGeometry"
        )
        self.node_tree.color_tag = "INPUT"
        self.initialized = True
        self.width = 250

        return None

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.referenced_node_tree = node.referenced_node_tree
            self.node_tree = self.node_tree.copy()

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return "Geometry Node"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""
        row = layout.row(align=True)
        row.prop(
            self,
            "referenced_node_tree",
            text="",
            icon="NODETREE",
            expand=True,
        )
        return None

    def draw_panel(self, layout, context):
        return None
