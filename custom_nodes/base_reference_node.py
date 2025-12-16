import bpy


def filter_materialize_obj(self, obj):
    if "materialize" in obj:
        return False
    return True


def update_node(custom_node, context):
    node: bpy.types.FunctionNodeInputString = custom_node.node_tree.nodes[
        "ReferenceValue"
    ]
    if custom_node.value != None:
        node.string = custom_node.value.name
    else:
        node.string = ""
    node = custom_node.node_tree.nodes["ReferenceType"]
    node.integer = custom_node.reference_type
    return None


class MTLZ_NG_GN_BaseReference(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MTLZ_NG_GN_BaseReference"
    bl_label = "Base Reference"
    bl_description = """A reference to an entity that is not managed by materialize"""
    color_tag = "COLOR"
    type_label = "Object"

    bl_width_default = 250

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        self.node_tree = load_node_group("MTLZ_External Reference").copy()
        self.width = 250

        return None

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.value = node.value
            self.node_tree = node.node_tree.copy()

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None

    def draw_label(
        self,
    ):
        """node label"""
        if self.label == "":
            return f"{self.type_label} Reference"
        return self.label

    def draw_buttons(self, context, layout):
        """node interface drawing"""
        row = layout.row(align=True)
        row.prop(self, "value", text=self.type_label)
        return None

    def draw_panel(self, layout, context):
        pass
