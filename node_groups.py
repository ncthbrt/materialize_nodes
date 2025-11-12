import bpy
import bpy.utils

def get_package_user_folder():
    bpy.utils.extension_path_user(__package__, create=True)