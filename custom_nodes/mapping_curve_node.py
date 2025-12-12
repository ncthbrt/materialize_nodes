import bpy

mapping_curve_node = "MappingCurve"
timers = {}


def curve_update(node_tree):
    global timers
    if (
        node_tree is not None
        and node_tree.name not in timers
        or not bpy.app.timers.is_registered(timers[node_tree.name])
    ):

        def update():
            if node_tree is not None:
                from .utils.curve_utils import reverseengineer_curvemapping_to_bezsegs
                from .utils.curve_nodegroup_utils import set_control_points

                del timers[node_tree.name]
                node = node_tree.nodes[mapping_curve_node]
                segments = reverseengineer_curvemapping_to_bezsegs(
                    node.mapping.curves[0]
                )
                set_control_points(segments, node.mapping, node_tree)

        timers[node_tree.name] = update
        bpy.app.timers.register(timers[node_tree.name], first_interval=0.25)


class MTLZ_NG_GN_MappingCurve(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_MappingCurve"
    bl_label = "Mapping Curve"
    bl_description = """Creates a mapping curve to control the area of effect of modifiers and constraints"""
    bl_width_default = 300

    tree_type = "GeometryNodeTree"
    initialized: bpy.props.BoolProperty(name="Initialized")

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
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
        self.color_tag = "INPUT"
        self.register_busses()
        return None

    def register_busses(self):
        bpy.msgbus.subscribe_rna(
            key=self.node_tree.nodes[mapping_curve_node],
            owner=self,
            args=(self.node_tree,),
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

    def free(self):
        bpy.data.node_groups.remove(self.node_tree)
