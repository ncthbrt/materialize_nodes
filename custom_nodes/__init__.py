from .external_target_node import MTLZ_NG_GN_Target
from .profile_curve_node import MTLZ_NG_GN_ProfileCurve

classes = (MTLZ_NG_GN_Target, MTLZ_NG_GN_ProfileCurve)

custom_nodes = {
    "External Target": MTLZ_NG_GN_Target,
    "Profile Curve": MTLZ_NG_GN_ProfileCurve,
}
