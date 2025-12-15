from .collection_reference_node import MTLZ_NG_GN_CollectionReference
from .image_reference_node import MTLZ_NG_GN_ImageReference
from .material_reference_node import MTLZ_NG_GN_MaterialReference
from .object_reference_node import MTLZ_NG_GN_ObjectReference
from .new_material_node import MTLZ_NG_GN_NewMaterial
from .geometry_node_node import MTLZ_NG_GN_GeometryNode
from .external_target_node import MTLZ_NG_GN_ExternalTarget
from .profile_curve_node import MTLZ_NG_GN_ProfileCurve
from .mapping_curve_node import MTLZ_NG_GN_MappingCurve

classes = (
    MTLZ_NG_GN_ExternalTarget,
    MTLZ_NG_GN_ProfileCurve,
    MTLZ_NG_GN_MappingCurve,
    MTLZ_NG_GN_GeometryNode,
    MTLZ_NG_GN_NewMaterial,
    MTLZ_NG_GN_ObjectReference,
    MTLZ_NG_GN_ImageReference,
    MTLZ_NG_GN_MaterialReference,
    MTLZ_NG_GN_CollectionReference,
)

custom_nodes = {
    "External Target": MTLZ_NG_GN_ExternalTarget,
    "Profile Curve": MTLZ_NG_GN_ProfileCurve,
    "Mapping Curve": MTLZ_NG_GN_MappingCurve,
    "Geometry Node": MTLZ_NG_GN_GeometryNode,
    "New Material": MTLZ_NG_GN_NewMaterial,
    "Object Reference": MTLZ_NG_GN_ObjectReference,
    "Image Reference": MTLZ_NG_GN_ImageReference,
    "Material Reference": MTLZ_NG_GN_MaterialReference,
    "Collection Reference": MTLZ_NG_GN_CollectionReference,
}
