import bpy
import mathutils


def filter_materialize_obj(self, obj):
    if "materialize" in obj:
        return False
    if self.target_type == "OBJECT":
        return True
    return obj.type == "ARMATURE"


class MTLZ_NG_GN_ExternalTarget(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_ExternalTarget"
    bl_label = "External Target"
    bl_description = """Creates a target to reference objects and bones that are not managed by materialize"""
    tree_type = "GeometryNodeTree"
    color_tag = "COLOR"

    def update_signal(self, context):
        node = self.node_tree.nodes["ExternalTarget"]
        if self.target != None:
            node.inputs[0].default_value = self.target.name
        else:
            node.inputs[0].default_value = ""
        if self.target_type == "BONE":
            node.inputs[1].default_value = self.subtarget
        else:
            node.inputs[1].default_value = ""
        node.inputs[2].default_value = self.target_type == "BONE"
        return None

    target_type: bpy.props.EnumProperty(
        name="Type",
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
        poll=filter_materialize_obj,
    )  # pyright: ignore[reportInvalidTypeForm]

    subtarget: bpy.props.StringProperty(
        name="Bone",
        description="Bone property",
        update=update_signal,
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

        node_group = load_node_group("MTLZ_External Target")
        self.node_tree = node_group.copy()
        self.width = 250

        return None

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.target_type = node.target_type
            self.subtarget = node.subtarget
            self.node_tree = node.node_tree

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

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
        row.prop(self, "target_type", text="Type")

        row = layout.row(align=True)

        if self.target_type == "OBJECT":
            row.prop(self, "target", text="Object")
        else:
            row.prop(self, "target", text="Armature")
            if self.target is not None:
                row = layout.row(align=True)
                row.prop_search(
                    self, "subtarget", self.target.data, "bones", text="Bone"
                )
        row = layout.row(align=True)
        return None

    def draw_panel(self, layout, context):
        pass
