# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
import os
import json
import os

from bpy.types import Operator, Menu, NODE_MT_add
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty
from .custom_icons import get_icons, load_icons
from .materialize_blend_loader import create_or_update_linked_lib

geo_node_group_cache = {}
node_menu_list = []
custom_node_groups = []
dynamic_addon_classes = []


dir_path = os.path.dirname(__file__)


class NODE_MT_mtlz_geo_menu(Menu):
    bl_label = "Materialize"
    bl_idname = "NODE_MT_mtlz_geo_menu"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "GeometryNodeTree"

    def draw(self, context):
        pass


def add_mtlz_menu(self, context):
    if context.area.ui_type == "GeometryNodeTree":
        self.layout.menu(
            NODE_MT_mtlz_geo_menu.bl_idname,
            text="Materalize",
            icon_value=get_icons()["materialize_icon"].icon_id,
        )


def clean_modules():
    """remove all plugin modules from sys.modules for a clean uninstall (dev hotreload solution)"""
    # See https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040 fore more details.

    import sys

    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(), key=lambda x: x[0]))  # sort them

    for k, v in all_modules.items():
        if k.startswith(__package__):  # type: ignore
            del sys.modules[k]

    return None


class NODE_OT_group_add(Operator):
    """Add a node group"""

    bl_idname = "mtlz.add_node"
    bl_label = "Add node group"
    bl_description = "Append Node Group"
    bl_options = {"REGISTER", "UNDO"}

    is_custom_node: BoolProperty()
    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == "NODE_EDITOR"
            and context.space_data.tree_type == "GeometryNodeTree"
        )

    def execute(self, context):
        bpy.ops.node.add_node(type=self.group_name)
        bpy.ops.transform.translate("INVOKE_DEFAULT")
        return {"FINISHED"}


def get_addon_classes():
    global dynamic_addon_classes
    """gather all classes of this plugin that have to be reg/unreg"""
    from .materialize_operations import classes as materialize_operation_classes
    from .custom_nodes import classes as custom_node_classes

    these_classes = (NODE_OT_group_add, NODE_MT_mtlz_geo_menu)
    classes = (
        materialize_operation_classes
        + custom_node_classes
        + tuple(dynamic_addon_classes)
        + these_classes
    )
    return classes


def node_menu_generator():
    from .custom_nodes.basic_template_node import MTLZ_NG_GN_BasicTemplateNode
    from .custom_nodes import custom_nodes

    global node_menu_list
    global geo_node_group_cache
    global dynamic_addon_classes

    node_menu_list = []
    for category in geo_node_group_cache.items():
        category = category

        def get_bl_idname(group):
            global geo_node_group_cache
            bl_idname = "MTLZ_NG_GN_" + group["name"]
            bl_idname = bl_idname.replace(" ", "_")
            return bl_idname

        for group in geo_node_group_cache[category[0]]["items"]:
            if group["name"] not in custom_nodes:
                bl_idname = get_bl_idname(group)
                node_type = type(
                    bl_idname,
                    (MTLZ_NG_GN_BasicTemplateNode,),
                    {
                        "bl_idname": bl_idname,
                        "bl_description": group["description"],
                        "color_tag": geo_node_group_cache[category[0]]["color_tag"],
                        "bl_label": group["name"],
                        "node_group": group["name"],
                    },
                )
                bpy.utils.register_class(node_type)
                dynamic_addon_classes.append(node_type)

        def custom_draw(self, context):
            layout = self.layout
            icons = get_icons()
            for group in geo_node_group_cache[self.bl_label]["items"]:
                icon = group["icon"]
                props = None
                if icon in icons:
                    props = layout.operator(
                        NODE_OT_group_add.bl_idname,
                        text=group["name"],
                        icon_value=icons[icon].icon_id,
                    )
                else:
                    props = layout.operator(
                        NODE_OT_group_add.bl_idname, text=group["name"], icon=icon
                    )
                if group["name"] in custom_nodes:
                    props.group_name = custom_nodes[group["name"]].bl_idname
                else:
                    props.group_name = get_bl_idname(group)

        menu_type = type(
            "NODE_MT_category_" + category[0],
            (bpy.types.Menu,),
            {
                "bl_idname": "NODE_MT_category_"
                + category[0].replace(
                    " ", "_"
                ),  # replace whitespace with uderscore to avoid alpha-numeric suffix warning
                "bl_space_type": "NODE_EDITOR",
                "bl_label": category[0],
                "draw": custom_draw,
            },
        )

        if menu_type not in node_menu_list:
            bpy.utils.register_class(menu_type)
            dynamic_addon_classes.append(menu_type)

            def generate_menu_draw(
                name, label, icon
            ):  # Wrapper function to force unique references
                def draw_menu(self, context):
                    self.layout.menu(name, text=label, icon_value=icon)

                return draw_menu

            bpy.types.NODE_MT_mtlz_geo_menu.append(
                generate_menu_draw(
                    menu_type.bl_idname,
                    menu_type.bl_label,
                    get_icons()[category[1]["icon"]].icon_id,
                )
            )
            node_menu_list.append(menu_type)


registered = False


def register():
    """main addon register"""
    global geo_node_group_cache
    global registered
    if registered == True:
        return
    with open(os.path.join(os.path.dirname(__file__), "geometry_nodes.json"), "r") as f:
        geo_node_group_cache = json.loads(f.read())
    load_icons()

    from .materialize_operations import extend_modifier_panel

    extend_modifier_panel()
    # register every single addon classes here
    for cls in get_addon_classes():
        bpy.utils.register_class(cls)

    NODE_MT_add.append(add_mtlz_menu)

    node_menu_generator()

    bpy.app.handlers.load_factory_startup_post.append(create_or_update_linked_lib)
    bpy.app.handlers.load_post.append(create_or_update_linked_lib)

    registered = True
    return None


def unregister():
    """main addon un-register"""
    global registered
    if registered == False:
        return

    try:
        bpy.app.handlers.load_factory_startup_post.remove(create_or_update_linked_lib)
    except:
        pass
    try:
        NODE_MT_add.remove(add_mtlz_menu)
    except:
        pass
    try:
        bpy.app.handlers.load_post.remove(create_or_update_linked_lib)
    except:
        pass

    try:
        from .materialize_operations import remove_modifier_panel

        remove_modifier_panel()
    except:
        pass
    try:
        # unregister every single addon classes here
        for cls in reversed(get_addon_classes()):
            bpy.utils.unregister_class(cls)

        clean_modules()
    except:
        pass
    registered = False
    return None
