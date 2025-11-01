# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

classes = ()


from .menus import append_menus, remove_menus


def load_ui():

    # add the menus to the nodes shift a menu
    append_menus()

    return None


def unload_ui():

    # remove the menus from the nodes shift a menu
    remove_menus()

    return None