import bpy
import mathutils


def filter_materialize_obj(self, obj):
    if "materialize" in obj:
        return False
    if self.target_type == "OBJECT":
        return True
    return obj.type == "ARMATURE"


profile_curve_node = "ProfileCurve"


def curve_update(self):
    print("UPDATED CURVE")


class MTLZ_NG_GN_ProfileCurve(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_ProfileCurve"
    bl_label = "Profile Curve"
    bl_description = """Creates a profile curve to control the area of effect of modifiers and constraints"""

    tree_type = "GeometryNodeTree"
    color_tag = "INPUT"
    initialized: bpy.props.BoolProperty(name="Initialized")

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
        if self.initialized:
            self.register_busses()

    def update_signal(self, context):
        # self.profile_curve
        return None

    bl_width_default = 300

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        node_group = load_node_group("MTLZ_Profile Curve")
        self.node_tree = node_group.copy()
        self.width = 300
        self.register_busses()
        self.initialized = True
        return None

    def register_busses(self):
        bpy.msgbus.subscribe_rna(
            key=self.node_tree.nodes[profile_curve_node],
            owner=self,
            args=(self,),
            notify=curve_update,
        )

    def copy(self, node):
        """fct run when dupplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.node_tree = node.node_tree.copy()
            self.width = node.width
            self.register_busses()
            self.initialized = True

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return "Profile Curve"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""
        layout.template_curve_mapping(
            self.node_tree.nodes[profile_curve_node], "mapping"
        )
        return None

    def draw_panel(self, layout, context):
        pass
