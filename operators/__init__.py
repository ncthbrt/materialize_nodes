# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

ADDON_KEYMAPS = []

KMI_DEFS = ()

classes = ()


def load_operators_keymaps():
    # TODO, ideally we need to save these keys on addonprefs somehow, it will reset per blender sessions.

    ADDON_KEYMAPS.clear()

    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return None

    km = kc.keymaps.new(
        name="Node Editor",
        space_type="NODE_EDITOR",
    )
    for (
        identifier,
        key,
        action,
        ctrl,
        shift,
        alt,
        props,
        name,
        icon,
        enable,
    ) in KMI_DEFS:
        kmi = km.keymap_items.new(
            identifier,
            key,
            action,
            ctrl=ctrl,
            shift=shift,
            alt=alt,
        )
        kmi.active = enable
        if props:
            for prop, value in props:
                setattr(kmi.properties, prop, value)
        ADDON_KEYMAPS.append((km, kmi, name, icon))

    return None


def unload_operators_keymaps():

    for km, kmi, _, _ in ADDON_KEYMAPS:
        km.keymap_items.remove(kmi)
    ADDON_KEYMAPS.clear()

    return None