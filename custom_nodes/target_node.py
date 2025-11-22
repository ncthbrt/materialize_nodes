import bpy


class MTLZ_NG_GN_Target(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_Target"
    bl_label = "External Target"
    bl_description = """Creates a target to reference objects and bones that are not managed by materialize"""
    auto_upd_flags = {
        "FRAME_PRE",
        "DEPS_POST",
    }
    tree_type = "GeometryNodeTree"

    def update_signal(self, context):
        return None

    target_type: bpy.props.EnumProperty(
        name="Target Type",
        description="The type of target to create",
        items=[
            (
                "OBJECT",
                "Object",
                "A target referencing an object",
                "OBJECT",
                1,
            ),
            (
                "BONE",
                "Bone",
                "A target referencing a bone",
                "BONE",
                2,
            ),
        ],
        default="OBJECT",
        update=update_signal,
    )  # type: ignore

    target: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object",
        update=update_signal,
    )  # pyright: ignore[reportInvalidTypeForm]

    subtarget: bpy.props.StringProperty(
        name="Bone",
        description="Bone property",
        update=update_signal,
    )  # pyright: ignore[reportInvalidTypeForm]

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"
        from ..materialize_blend_loader import load_node_group

        node_group = load_node_group("External Reference")
        self.node_tree = node_group
        self.sockets = {}
        self.width = 200
        self.target_out = self.outputs.new(
            type="NodeSocketBundle",
            name="Target",
            identifier="Target",
        )
        return None

    def copy(self, node):
        """fct run when dupplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.node_tree = node.node_tree

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def update(self):
        """generic update function"""

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return "External Target"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""

        row = layout.row(align=True)

        row.prop(self, "target_type", text="Target Type")

        return None

    def draw_panel(self, layout, context):
        pass
