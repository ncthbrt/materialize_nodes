import os
import pathlib
import shutil
import bpy


def _get_data_dir():
    data_dir = bpy.utils.extension_path_user(
        __package__, path="blend/1_0_0", create=True
    )
    return data_dir


def get_path(library_name="materialize.blend"):
    data_dir = _get_data_dir()
    path = os.path.join(data_dir, library_name)
    return path


def load(library_name="materialize.blend"):
    path = get_path(library_name=library_name)
    return bpy.data.libraries.load(path, link=True)


def _create_or_update_linked_lib_impl(library_name="materialize.blend"):
    print(_create_or_update_linked_lib_impl, library_name)
    data_dir = _get_data_dir()
    shutil.copy2(
        os.path.join(os.path.dirname(__file__), library_name),
        os.path.join(data_dir, library_name),
    )
    with load(library_name=library_name) as (data_from, data_to):
        for group in bpy.data.node_groups:
            if group.library.name == library_name:
                data_to.node_groups.append(group.name)


def create_or_update_linked_lib(_):
    _create_or_update_linked_lib_impl()


def create_or_update_linked_template_lib(_):
    _create_or_update_linked_lib_impl(library_name="materialize_templates.blend")


def _find_node_group(group_name, library_name="materialize.blend"):
    for node_group in bpy.data.node_groups:
        if (
            node_group.name == group_name
            and node_group.library is not None
            and node_group.library.name == library_name
        ):
            return node_group
    return None


def load_node_group(group_name, library_name="materialize.blend"):
    found_group = _find_node_group(group_name, library_name)
    if found_group is None:
        with load(library_name=library_name) as (_, data_to):
            data_to.node_groups.append(group_name)
        return _find_node_group(group_name, library_name)
    else:
        return found_group


def load_template_node_group(group_name):
    return load_node_group(group_name, library_name="materialize_templates.blend")
