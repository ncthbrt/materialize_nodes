# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ..__init__ import isdebug, dprint
from ..custom_nodes import allcustomnodes
from collections.abc import Iterable


def register_msgbusses():
    return None


def unregister_msgbusses():
    return None


def on_plugin_installation():
    """is executed either right after plugin installation (when user click on install checkbox),
    or when blender is booting, it will also load plugin"""

    def wait_restrict_state_timer():
        """wait until bpy.context is not bpy_restrict_state._RestrictContext anymore
        BEWARE: this is a function from a bpy.app timer, context is trickier to handle
        """

        dprint(
            f"HANDLER: on_plugin_installation(): Still in restrict state?",
        )

        # don't do anything until context is cleared out
        if str(bpy.context).startswith("<bpy_restrict_state"):
            return 0.01

        dprint(
            f"HANDLER: on_plugin_installation(): Loading Plugin: Running few functions..",
        )

        return None

    bpy.app.timers.register(wait_restrict_state_timer)

    return None



def upd_all_custom_nodes(classes: list):
    """automatically run the update_all() function of all custom nodes passed"""
    from ..utils.node_utils import get_all_nodes
    # NOTE function below will simply collect all instances of 'RigNodes' nodes.
    # NOTE there's a lot of classes, and this functions might loop over a lot of data.
    # for optimization purpose, instead of each cls using the function, we create it once
    # here, then pass the list to the update functions with the 'using_nodes' param.

    if not classes:
        return None    

    matching_blid = [cls.bl_idname for cls in classes]

    nodes = get_all_nodes(exactmatch_idnames=matching_blid)

    for n in nodes:
        # cls with auto_update property are eligible for automatic execution.
        if (not hasattr(n, "update_all")) or (not hasattr(n, "auto_update")):
            continue
        
        n.update_all(signal_from_handlers=True, using_nodes=nodes)
        continue

    return None


DEPSPOST_UPD_NODES = [cls for cls in allcustomnodes if ("DEPS_POST" in cls.auto_update)]


@bpy.app.handlers.persistent
def materialize_nodes_handler_depspost(scene, desp):
    """update on depsgraph change"""

    # updates for our custom nodes
    upd_all_custom_nodes(DEPSPOST_UPD_NODES)
    return None


FRAMEPRE_UPD_NODES = [cls for cls in allcustomnodes if ("FRAME_PRE" in cls.auto_update)]


@bpy.app.handlers.persistent
def materialize_nodes_handler_framepre(scene, desp):
    """update on frame change"""

    if isdebug():
        print("materialize_nodes_handler_framepre(): frame_pre signal")

    # updates for our custom nodes
    upd_all_custom_nodes(FRAMEPRE_UPD_NODES)
    return None


LOADPOST_UPD_NODES = [cls for cls in allcustomnodes if ("LOAD_POST" in cls.auto_update)]


@bpy.app.handlers.persistent
def materialize_nodes_handler_loadpost(scene, desp):
    """Handler function when user is loading a file"""

    # need to add message bus on each blender load
    register_msgbusses()

    # updates for our custom nodes
    upd_all_custom_nodes(LOADPOST_UPD_NODES)
    return None


def all_handlers(name=False):
    """return a list of handler stored in .blend"""

    for oh in bpy.app.handlers:
        if isinstance(oh, Iterable):
            for h in oh:
                yield h


def load_handlers():

    # special timer 'handler' for plugin installation.
    # if we need to do things on plugin init, but there's an annoying restrict state.
    on_plugin_installation()

    handler_names = [h.__name__ for h in all_handlers()]

    if "materialize_nodes_handler_depspost" not in handler_names:
        bpy.app.handlers.depsgraph_update_post.append(materialize_nodes_handler_depspost)

    if "materialize_nodes_handler_framepre" not in handler_names:
        bpy.app.handlers.frame_change_pre.append(materialize_nodes_handler_framepre)

    if "materialize_nodes_handler_loadpost" not in handler_names:
        bpy.app.handlers.load_post.append(materialize_nodes_handler_loadpost)

    return None


def unload_handlers():

    for h in all_handlers():

        if h.__name__ == "materialize_nodes_handler_depspost":
            bpy.app.handlers.depsgraph_update_post.remove(h)

        if h.__name__ == "materialize_nodes_handler_framepre":
            bpy.app.handlers.frame_change_pre.remove(h)

        if h.__name__ == "materialize_nodes_handler_loadpost":
            bpy.app.handlers.load_post.remove(h)

    return None