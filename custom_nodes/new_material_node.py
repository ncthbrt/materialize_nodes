import bpy
from .utils.nodetree_interface_utils import copy_interface_input_items


def filter_material_tree(self, material_tree: bpy.types.NodeTree):
    for item in material_tree.interface.items_tree:
        if item.item_type == "SOCKET" and item.in_out == "OUTPUT":
            socket: bpy.types.NodeTreeInterfaceSocket = item
            if socket.socket_type == "NodeSocketShader":
                return True
    return False


class MTLZ_NG_GN_NewMaterial(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_NewMaterial"
    bl_label = "New Material"
    bl_description = """Creates a material from a node tree"""

    def update_signal(self, context):
        if self.material_tree is not None:
            copy_interface_input_items(
                self.material_tree.interface, self.node_tree.interface
            )
        return None

    material_tree: bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        name="Material Tree",
        description="Material Tree",
        update=update_signal,
        poll=filter_material_tree,
    )  # pyright: ignore[reportInvalidTypeForm]

    bl_width_default = 250

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        self.node_tree = bpy.data.node_groups.new(
            name=f"{self.name} Impl", type="GeometryNodeTree"
        )  # type: ignore
        self.width = 250

        return None

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.node_tree = node.node_tree.copy()
            self.material_tree = node.material_tree

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return "New Material"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""

        row = layout.row(align=True)
        row.prop(
            self, "material_tree", text="", icon="MATERIAL", placeholder="Material Tree"
        )

    def draw_panel(self, layout, context):
        pass
