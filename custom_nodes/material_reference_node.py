import bpy

from .base_reference_node import (
    MTLZ_NG_GN_BaseReference,
    filter_materialize_obj,
    update_node,
)


class MTLZ_NG_GN_MaterialReference(MTLZ_NG_GN_BaseReference):
    bl_idname = "MTLZ_NG_GN_MaterialReference"
    bl_label = "Material Reference"
    bl_description = """A reference to a material not managed by Materialize"""
    color_tag = "COLOR"
    type_label = "Material"
    reference_type = 3

    value: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="Material",
        update=update_node,
        poll=filter_materialize_obj,
    )  # pyright: ignore[reportInvalidTypeForm]
