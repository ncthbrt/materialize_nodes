import bpy

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
    color_tag = "COLOR"

    initialized: bpy.props.BoolProperty(name="Initialized")

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
        if self.initialized:
            self.register_busses()

    def register_busses(self):
        pass

    def create_node_tree(self):

        pass

    def clear_node_group(self):
        # self.node_tree
        pass

    def update_node_group(self, context):
        self.clear_node_group()
        if self.referenced_node_tree == None:
            return

        source_iface: bpy.types.NodeTreeInterface = self.referenced_node_tree.interface
        target_iface: bpy.types.NodeTreeInterface = self.node_tree.interface  # type: ignore
        for item in source_iface.items_tree:
            if item.item_type == "SOCKET":
                socket: bpy.types.NodeTreeInterfaceSocket = item  # type: ignore
                if socket.in_out != "INPUT":
                    continue
                item = target_iface.copy(item)
            elif item.item_type == "PANEL":
                target_iface.copy(item)

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
