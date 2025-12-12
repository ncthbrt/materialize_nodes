from .geometry_node_node import MTLZ_NG_GN_GeometryNodeNode
from .external_target_node import MTLZ_NG_GN_ExternalTarget
from .profile_curve_node import MTLZ_NG_GN_ProfileCurve
from .mapping_curve_node import MTLZ_NG_GN_MappingCurve

classes = (
    MTLZ_NG_GN_ExternalTarget,
    MTLZ_NG_GN_ProfileCurve,
    MTLZ_NG_GN_MappingCurve,
    MTLZ_NG_GN_GeometryNodeNode,
)

custom_nodes = {
    "External Target": MTLZ_NG_GN_ExternalTarget,
    "Profile Curve": MTLZ_NG_GN_ProfileCurve,
    "Mapping Curve": MTLZ_NG_GN_MappingCurve,
    "Geometry Node": MTLZ_NG_GN_GeometryNodeNode,
}
