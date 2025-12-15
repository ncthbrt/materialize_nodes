import bpy

from .base_reference_node import (
    MTLZ_NG_GN_BaseReference,
    filter_materialize_obj,
    update_node,
)


class MTLZ_NG_GN_ImageReference(MTLZ_NG_GN_BaseReference):
    bl_idname = "MTLZ_NG_GN_ImageReference"
    bl_label = "Image Reference"
    bl_description = """A reference to an image"""
    color_tag = "COLOR"
    type_label = "Image"

    value: bpy.props.PointerProperty(
        type=bpy.types.Image,
        name="Image",
        description="Image",
        update=update_node,
        poll=filter_materialize_obj,
    )  # pyright: ignore[reportInvalidTypeForm]
