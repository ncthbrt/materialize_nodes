import bpy

from .base_reference_node import (
    MTLZ_NG_GN_BaseReference,
    filter_materialize_obj,
    update_node,
)


class MTLZ_NG_GN_ObjectReference(MTLZ_NG_GN_BaseReference):
    bl_idname = "MTLZ_NG_GN_ObjectReference"
    bl_label = "Object Reference"
    bl_description = """A reference to an object that is not managed by materialize"""
    color_tag = "COLOR"
    type_label = "Object"
    reference_type = 4

    value: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object",
        update=update_node,
        poll=filter_materialize_obj,
    )  # pyright: ignore[reportInvalidTypeForm]
