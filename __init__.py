# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
import os
import json
import os

from bpy.types import Operator, Menu, NODE_MT_add
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty
from .custom_icons import get_icons, load_icons

geo_node_group_cache = {}
node_menu_list = []
custom_node_groups = []

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

    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree

    def execute(self, context):
        old_groups = set(bpy.data.node_groups)

        for file in os.listdir(dir_path):
            if file.endswith(".blend"):
                filepath = os.path.join(dir_path, file)
                break
        else:
            raise FileNotFoundError("No .blend File in directory " + dir_path)

        with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
            if self.group_name not in bpy.data.node_groups:
                data_to.node_groups.append(self.group_name)
        added_groups = list(set(bpy.data.node_groups) - old_groups)
        for group in added_groups:
            for node in group.nodes:
                if node.type == "GROUP":
                    new_name = node.node_tree.name.split(".")[0]
                    node.node_tree = bpy.data.node_groups[new_name]
        for group in added_groups:
            if "." in group.name:
                bpy.data.node_groups.remove(group)

        bpy.ops.node.add_node(type="GeometryNodeGroup")
        node = context.selected_nodes[0]

        node.node_tree = bpy.data.node_groups[self.group_name]
        bpy.ops.transform.translate("INVOKE_DEFAULT")

        return {"FINISHED"}


def get_addon_classes(revert=False):
    """gather all classes of this plugin that have to be reg/unreg"""
    from .materialize_operation import classes as materialize_classes

    these_classes = (NODE_OT_group_add,)
    classes = these_classes + materialize_classes
    if revert:
        return reversed(classes)

    return classes


def node_menu_generator():
    global node_menu_list
    global geo_node_group_cache
    node_menu_list = []
    for item in geo_node_group_cache.items():
        item = item

        def custom_draw(self, context):
            layout = self.layout
            for group in geo_node_group_cache[self.bl_label]["items"]:
                props = layout.operator(
                    NODE_OT_group_add.bl_idname,
                    text=group["name"],
                    icon_value=get_icons()[group["icon"]].icon_id,
                )
                props.group_name = "MTLZ_" + group["name"]

        menu_type = type(
            "NODE_MT_category_" + item[0],
            (bpy.types.Menu,),
            {
                "bl_idname": "NODE_MT_category_"
                + item[0].replace(
                    " ", "_"
                ),  # replace whitespace with uderscore to avoid alpha-numeric suffix warning
                "bl_space_type": "NODE_EDITOR",
                "bl_label": item[0],
                "draw": custom_draw,
            },
        )
        if menu_type not in node_menu_list:

            def generate_menu_draw(
                name, label, icon
            ):  # Wrapper function to force unique references
                def draw_menu(self, context):
                    self.layout.menu(name, text=label, icon_value=icon)

                return draw_menu

            bpy.utils.register_class(menu_type)
            bpy.types.NODE_MT_mtlz_geo_menu.append(
                generate_menu_draw(
                    menu_type.bl_idname,
                    menu_type.bl_label,
                    get_icons()[item[1]["icon"]].icon_id,
                )
            )
            node_menu_list.append(menu_type)


def register():
    """main addon register"""
    global geo_node_group_cache

    with open(os.path.join(os.path.dirname(__file__), "geometry_nodes.json"), "r") as f:
        geo_node_group_cache = json.loads(f.read())
    load_icons()

    if not hasattr(bpy.types, NODE_MT_mtlz_geo_menu.bl_idname):
        bpy.utils.register_class(NODE_MT_mtlz_geo_menu)
        NODE_MT_add.append(add_mtlz_menu)
    from .materialize_operation import extend_modifier_panel

    extend_modifier_panel()
    # register every single addon classes here
    for cls in get_addon_classes():
        bpy.utils.register_class(cls)

    node_menu_generator()

    return None


def unregister():
    """main addon un-register"""
    from .custom_icons import get_icons

    bpy.utils.previews.remove(get_icons())

    if hasattr(bpy.types, NODE_MT_mtlz_geo_menu.bl_idname):
        bpy.utils.unregister_class(NODE_MT_mtlz_geo_menu)
        NODE_MT_add.remove(add_mtlz_menu)

    from .materialize_operation import remove_modifier_panel

    remove_modifier_panel()
    # unregister every single addon classes here
    for cls in get_addon_classes(revert=True):
        bpy.utils.unregister_class(cls)

    clean_modules()

    return None
