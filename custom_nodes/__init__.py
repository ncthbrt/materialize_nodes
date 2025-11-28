from .external_target_node import MTLZ_NG_GN_Target
from .profile_curve_node import MTLZ_NG_GN_ProfileCurve
from .mapping_curve_node import MTLZ_NG_GN_MappingCurve

classes = (MTLZ_NG_GN_Target, MTLZ_NG_GN_ProfileCurve, MTLZ_NG_GN_MappingCurve)

custom_nodes = {
    "External Target": MTLZ_NG_GN_Target,
    "Profile Curve": MTLZ_NG_GN_ProfileCurve,
    "Mapping Curve": MTLZ_NG_GN_MappingCurve,
}
