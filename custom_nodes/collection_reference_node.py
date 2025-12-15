import bpy

from .base_reference_node import (
    MTLZ_NG_GN_BaseReference,
    filter_materialize_obj,
    update_node,
)


class MTLZ_NG_GN_CollectionReference(MTLZ_NG_GN_BaseReference):
    bl_idname = "MTLZ_NG_GN_CollectionReference"
    bl_label = "Collection Reference"
    bl_description = """A reference to a collection"""
    color_tag = "COLOR"
    type_label = "Collection"

    value: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="Collection",
        update=update_node,
        poll=filter_materialize_obj,
    )  # pyright: ignore[reportInvalidTypeForm]
