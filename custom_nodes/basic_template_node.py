import bpy
from ..materialize_blend_loader import load_node_group


class MTLZ_NG_GN_BasicTemplateNode(bpy.types.GeometryNodeCustomGroup):
    node_group = None

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this is run when appending the node for the first time"""
        name = f".{self.bl_idname}"

        from ..materialize_blend_loader import load_node_group

        ng = load_node_group(self.node_group)
        self.node_tree = ng
        self.width = ng.default_group_node_width

        return None

    def copy(self, node):
        """fct run when duplicating the node"""

        # NOTE: copy/paste can cause crashes, we use a timer to delay the action
        def delayed_copy():
            self.node_group = node.node_group
            self.node_tree = node.node_tree

        bpy.app.timers.register(delayed_copy, first_interval=0.01)

        return None
