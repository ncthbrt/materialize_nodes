import bpy
import mathutils
import numpy as np


def filter_materialize_obj(self, obj):
    if "materialize" in obj:
        return False
    if self.target_type == "OBJECT":
        return True
    return obj.type == "ARMATURE"


profile_curve_object = "MTLZ_ProfileCurveObject"
profile_curve_modifier_name = "ProfileCurve"


def create_profile_curve(obj):
    bevel_modifier = obj.modifiers.new(profile_curve_modifier_name, "BEVEL")
    return bevel_modifier.name


def get_or_create_profile_curve_object(obj):
    if obj is not None and obj.name in bpy.data.objects:
        return obj
    data = bpy.data.meshes.new(profile_curve_object)
    obj = bpy.data.objects.new(profile_curve_object, data)
    obj.visible_camera = False
    obj.hide_render = True
    obj.hide_select = True
    create_profile_curve(obj)
    return obj


def curve_update(self):
    if self.curve_update_timer is None or not bpy.app.timers.is_registered(
        self.curve_update_timer
    ):

        def update():
            if self is not None:
                self.curve_update_timer = None
                return None

        self.curve_update_timer = update
        bpy.app.timers.register(self.curve_update_timer, first_interval=0.25)


class MTLZ_NG_GN_ProfileCurve(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_ProfileCurve"
    bl_label = "Profile Curve"
    bl_description = """Creates a profile curve to control the profile of modifiers and constraints"""

    tree_type = "GeometryNodeTree"
    color_tag = "INPUT"
    initialized: bpy.props.BoolProperty(name="Initialized")

    def profile_object_updated(self, context):
        if self.profile_object is None:
            self.obj_initialize()
        return None

    profile_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Profile Object",
        description="Profile Object",
        update=profile_object_updated,
    )  # pyright: ignore[reportInvalidTypeForm]

    def __init__(self, strct=None) -> None:
        super().__init__(strct)
        self.curve_update_timer = None
        if self.initialized:
            self.register_busses()

    bl_width_default = 300

    def obj_initialize(self):
        self.profile_object = get_or_create_profile_curve_object(self.profile_object)
        self.register_busses()
        self.initialized = True

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context: bpy.types.Context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        node_group = load_node_group("MTLZ_Profile Curve")
        self.node_tree = node_group.copy()
        self.width = 300
        self.obj_initialize()
        return None

    def is_valid(self):
        return (
            self.profile_object is not None
            and profile_curve_modifier_name in self.profile_object.modifiers
        )

    def register_busses(self):
        if self.is_valid():
            bpy.msgbus.subscribe_rna(
                key=self.profile_object.modifiers[profile_curve_modifier_name],
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
            if node.is_valid():
                self.profile_object = node.profile_object.copy()
            self.obj_initialize()

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(self):
        """node label"""
        if self.label == "":
            return "Profile Curve"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""
        if not self.is_valid():
            self.obj_initialize()
        layout.template_curveprofile(
            self.profile_object.modifiers[profile_curve_modifier_name],
            "custom_profile",
        )
        return None

    def draw_panel(self, layout, context):
        pass

    def free(self) -> None:
        """Clean up node on removal"""
        if self.is_valid():
            obj = self.profile_object
            bpy.data.objects.remove(obj)
            self.initialized = False
