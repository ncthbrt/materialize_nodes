import bpy
import mathutils


mapping_curve_node = "MappingCurve"


def curve_update(self):
    if self.curve_update_timer is None or not bpy.app.timers.is_registered(
        self.curve_update_timer
    ):

        def update():
            if self is not None:
                self.curve_update_timer = None
                print("Updating curve")

        self.curve_update_timer = update
        bpy.app.timers.register(self.curve_update_timer, first_interval=0.1)


class MTLZ_NG_GN_MappingCurve(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_MappingCurve"
    bl_label = "Mapping Curve"
    bl_description = """Creates a mapping curve to control the area of effect of modifiers and constraints"""
    bl_width_default = 300

    tree_type = "GeometryNodeTree"
    color_tag = "INPUT"
    initialized: bpy.props.BoolProperty(name="Initialized")

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
        self.curve_update_timer = None
        if self.initialized:
            self.register_busses()

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context: bpy.types.Context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        node_group = load_node_group("MTLZ_Mapping Curve")
        self.node_tree = node_group.copy()
        self.width = 300
        self.initialized = True
        self.register_busses()
        return None

    def register_busses(self):
        bpy.msgbus.subscribe_rna(
            key=self.node_tree.nodes[mapping_curve_node],
            owner=self,
            args=(self,),
            notify=curve_update,
        )

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.node_tree = node.node_tree.copy()
            self.width = node.width
            self.initialized = True
            self.register_busses()

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return "Mapping Curve"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""
        layout.template_curve_mapping(
            self.node_tree.nodes[mapping_curve_node], "mapping"
        )
        return None

    def draw_panel(self, layout, context):
        pass
