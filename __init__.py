# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

# This is only here for supporting blender 4.1
bl_info = {
    "name": "Materialize Nodes",
    "author": "Natalie Cuthbert <natalie@cuthbert.co.za>",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "Node Editor",
    "description": "Procedural object creation with geometry nodes",
    "warning": "",
    "category": "Node",
}


def get_addon_prefs():
    """get preferences path from base_package, __package__ path change from submodules"""
    return bpy.context.preferences.addons[__package__].preferences


def isdebug():
    return get_addon_prefs().debug


def dprint(thing):
    if isdebug():
        print(thing)


def clean_modules():
    """remove all plugin modules from sys.modules for a clean uninstall (dev hotreload solution)"""
    # See https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040 fore more details.

    import sys

    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(), key=lambda x: x[0]))  # sort them

    for k, v in all_modules.items():
        if k.startswith(__package__):
            del sys.modules[k]

    return None


def get_addon_classes(revert=False):
    """gather all classes of this plugin that have to be reg/unreg"""

    from .properties import classes as properties_classes
    from .operators import classes as operators_classes
    from .custom_nodes import classes as nodes_classes
    from .ui import classes as ui_classes
    from .preferences import classes as preferences_classes

    classes = (+properties_classes +operators_classes + nodes_classes + ui_classes + preferences_classes)

    if revert:
        return reversed(classes)

    return classes


def register():
    """main addon register"""

    # register every single addon classes here
    for cls in get_addon_classes():
        bpy.utils.register_class(cls)

    from .properties import load_properties

    load_properties()

    from .handlers import load_handlers

    load_handlers()

    from .ui import load_ui

    load_ui()

    from .operators import load_operators_keymaps

    load_operators_keymaps()

    return None


def unregister():
    """main addon un-register"""

    from .operators import unload_operators_keymaps

    unload_operators_keymaps()

    from .ui import unload_ui

    unload_ui()

    from .handlers import unload_handlers

    unload_handlers()

    from .properties import unload_properties

    unload_properties()

    # unregister every single addon classes here
    for cls in get_addon_classes(revert=True):
        bpy.utils.unregister_class(cls)

    clean_modules()

    return None