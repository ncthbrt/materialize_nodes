import bpy
import mathutils
from .utils.nodetree_interface_utils import copy_interface_input_items

exclude_nodes = (
    "Materialize Template [materialize.blend]",
    "Prepare Materialization [materialize.blend]",
)


def filter_node_group(self, obj: bpy.types.NodeTree):
    if obj.type == "GEOMETRY":
        return obj.is_modifier and obj.name_full not in exclude_nodes  # type: ignore
    return False


class MTLZ_NG_GN_GeometryNode(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_GeometryNodeNode"
    bl_label = "Geometry Node"
    bl_description = """A node that creates a lazily evaluated geometry node group"""
    initialized: bpy.props.BoolProperty(name="Initialized")  # type: ignore
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
                        | "GEOMETRY"
                    ):
                        group = load_node_group(f"MTLZ_Node Store {output.type}")
                        geometry_node_group: bpy.types.GeometryNodeGroup = self.node_tree.nodes.new("GeometryNodeGroup")  # type: ignore
                        geometry_node_group.node_tree = group
                        geometry_node_group.location = mathutils.Vector(
                            ((index + 1) * 300, 0)
                        )
                        name_socket: bpy.types.NodeSocketString = (
                            geometry_node_group.inputs[1]
                        )  # type: ignore
                        name_socket.default_value = output.identifier
                        input_socket = geometry_node_group.inputs[0]
                        self.node_tree.links.new(input=input_socket, output=prev_socket)
                        input_socket = geometry_node_group.inputs[2]
                        output_socket = input_node.outputs[index]
                        self.node_tree.links.new(
                            input=input_socket, output=output_socket
                        )
                        prev_socket = geometry_node_group.outputs[0]
                    case "IMAGE" | "MATERIAL" | "OBJECT":
                        error = AssertionError()
                        error.add_note(
                            "Image, material, or object socket types are not expected here"
                        )
                        raise error
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

    def clear_node_group(self):
        for item in reversed(self.node_tree.interface.items_tree):
            if item.item_type == "SOCKET" and item.in_out == "OUTPUT":
                continue
            self.node_tree.interface.remove(item)

        for node in reversed(self.node_tree.nodes):
            self.node_tree.nodes.remove(node)
        for k in self.keys():
            del self[k]

    def update_node_group(self, context):
        if self.prev_referenced_node_tree == self.referenced_node_tree:
            return
        self.clear_node_group()
        if self.referenced_node_tree == None:
            return
        self.prev_referenced_node_tree = self.referenced_node_tree
        copy_interface_input_items(
            self.referenced_node_tree.interface, self.node_tree.interface, self
        )
        self.setup_connections_and_outputs()

    def update_signal(self, context):
        if self.initialized:
            self.update_node_group(context)

    prev_referenced_node_tree = bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        name="Prev Node Tree",
        description="The node tree that was previously linked",
        update=update_signal,
        poll=filter_node_group,
    )
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
            self.prev_referenced_node_tree = node.prev_referenced_node_tree
            self.node_tree = self.node_tree.copy()
            for k in node.keys():
                self[k] = node[k]

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

    def free(self):
        bpy.data.node_groups.remove(self.node_tree)
