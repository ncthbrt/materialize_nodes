import os
import pathlib
import shutil
import bpy

file_name = "materialize.blend"


def _get_data_dir():
    data_dir = bpy.utils.extension_path_user(
        __package__, path="blend/1_0_0", create=True
    )
    return data_dir


def get_path():
    data_dir = _get_data_dir()
    path = os.path.join(data_dir, file_name)
    return path


def load():
    path = get_path()
    return bpy.data.libraries.load(path, link=True)


def create_or_update_linked_lib(_):
    data_dir = _get_data_dir()
    shutil.copy2(
        os.path.join(os.path.dirname(__file__), file_name),
        os.path.join(data_dir, file_name),
    )
    with load() as (data_from, data_to):
        for group in bpy.data.node_groups:
            if group.library.name == "materialize.blend":
                data_to.node_groups.append(group.name)


def _find_node_group(group_name):
    for node_group in bpy.data.node_groups:
        if (
            node_group.name == group_name
            and node_group.library is not None
            and node_group.library.name == "materialize.blend"
        ):
            return node_group
    return None


def load_node_group(group_name):
    full_name = f"{group_name} [materialize.blend]"
    found_group = None
    found_group = _find_node_group(group_name)
    if found_group == None:
        with load() as (_, data_to):
            data_to.node_groups.append(group_name)
        return _find_node_group(group_name)
    else:
        return found_group
