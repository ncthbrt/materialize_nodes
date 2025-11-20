import json
import bpy
import bpy.utils.previews
import os
import pathlib

dir_path = os.path.dirname(__file__)
custom_icons = bpy.utils.previews.new()


def get_icons():
    global custom_icons
    return custom_icons


def load_icons():
    global custom_icons
    icons_dir = os.path.join(dir_path, "icons")
    for icon in os.listdir(icons_dir):
        icon_path = pathlib.Path(icon)
        icon_name = icon_path.stem
        if icon != "ATTRIBUTION":
            custom_icons.load(icon_name, os.path.join(icons_dir, icon), "IMAGE")
