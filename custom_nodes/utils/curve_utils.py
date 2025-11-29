# NOTE: The `reverseengineer_curve_to_bezsegs` function below was copied nearly verbatim from
# the `reverseengineer_curvemapping_to_bezsegs` function in the `bezier2d_utils` module in the https://github.com/DB3D/Node-Booster repository.
#
# Accordingly, the attribution and license information has been preserved as mandated by the terms of the
# "GPL-2.0-or-later" license.
#
# Changes were made to accomodate profile curves in addition to mapping curves.

# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later
import numpy as np
import bpy

# NOTE
# a blender curvemapping bezier has a lot of logic to it with the handles.
# this function tries to reverse engineer that logic into a list of cubic beziers segments.
# could be largly improved and cleaned up.


def _guess_handles(current_pt, prev_pt, next_pt):
    """Calculates handle positions mimicking Blender C function calchandle_curvemap."""

    handle_type = current_pt.handle_type

    p2 = np.array(current_pt.location, dtype=float)

    if prev_pt is None:
        if next_pt is None:
            p1 = p2.copy()
            p3 = p2.copy()
        else:
            p3 = np.array(next_pt.location, dtype=float)
            p1 = 2.0 * p2 - p3
    else:
        p1 = np.array(prev_pt.location, dtype=float)
        if next_pt is None:
            p3 = 2.0 * p2 - p1
        else:
            p3 = np.array(next_pt.location, dtype=float)

    dvec_a = np.subtract(p2, p1)
    dvec_b = np.subtract(p3, p2)
    len_a = np.linalg.norm(dvec_a)
    len_b = np.linalg.norm(dvec_b)

    if abs(len_a) < 1e-5:
        len_a = 1.0
    if abs(len_b) < 1e-5:
        len_b = 1.0

    h1_calc = p2.copy()
    h2_calc = p2.copy()

    if (handle_type == "AUTO") or (handle_type == "AUTO_CLAMPED"):
        tvec = (dvec_b / len_b) + (dvec_a / len_a)
        len_tvec = np.linalg.norm(tvec)
        len_factor = len_tvec * 2.5614

        if abs(len_factor) > 1e-5:
            scale_a = len_a / len_factor
            scale_b = len_b / len_factor
            base_h1 = p2 - tvec * scale_a
            base_h2 = p2 + tvec * scale_b
            h1_calc = base_h1.copy()
            h2_calc = base_h2.copy()

            if (
                (handle_type == "AUTO_CLAMPED")
                and (prev_pt is not None)
                and (next_pt is not None)
            ):
                y_prev = prev_pt.location[1]
                y_curr = current_pt.location[1]
                y_next = next_pt.location[1]
                ydiff1 = y_prev - y_curr
                ydiff2 = y_next - y_curr
                is_extremum = (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (
                    ydiff1 >= 0.0 and ydiff2 >= 0.0
                )
                if is_extremum:
                    h1_calc[1] = y_curr
                else:
                    if ydiff1 <= 0.0:
                        h1_calc[1] = max(y_prev, base_h1[1])
                    else:
                        h1_calc[1] = min(y_prev, base_h1[1])

            if (
                (handle_type == "AUTO_CLAMPED")
                and (prev_pt is not None)
                and (next_pt is not None)
            ):
                y_prev = prev_pt.location[1]
                y_curr = current_pt.location[1]
                y_next = next_pt.location[1]
                ydiff1 = y_prev - y_curr
                ydiff2 = y_next - y_curr
                is_extremum = (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (
                    ydiff1 >= 0.0 and ydiff2 >= 0.0
                )
                if is_extremum:
                    h2_calc[1] = y_curr
                else:
                    if ydiff1 <= 0.0:
                        h2_calc[1] = min(y_next, base_h2[1])
                    else:
                        h2_calc[1] = max(y_next, base_h2[1])

    elif handle_type == "VECTOR":
        h1_calc = p2 - dvec_a / 3.0
        h2_calc = p2 + dvec_b / 3.0

    if np.any(np.isnan(h1_calc)):
        h1_calc = p2.copy()
    if np.any(np.isnan(h2_calc)):
        h2_calc = p2.copy()

    return h1_calc, h2_calc


def _ensure_monotonic_handles(points, all_left_h, all_right_h):
    """
    Adjusts calculated handle X-coordinates to ensure X-monotonicity for each segment.
    Enforces x0 <= x1 <= x2 <= x3 where P1=HR_i, P2=HL_i+1.

    Args:
        points: List of CurveMapPoint objects.
        all_left_h: List of calculated left handle positions (np.arrays).
        all_right_h: List of calculated right handle positions (np.arrays).

    Returns:
        tuple: (final_left_h, final_right_h) - Lists of adjusted handle positions.
    """
    n_points = len(points)
    if n_points < 2:
        return list(all_left_h), list(all_right_h)

    # Create copies to modify
    final_left_h = [h.copy() for h in all_left_h]
    final_right_h = [h.copy() for h in all_right_h]

    # Iterate through segments [i, i+1]
    for i in range(n_points - 1):
        # P0 = knot[i], P1 = HR[i], P2 = HL[i+1], P3 = knot[i+1]
        x_k_i = points[i].location[0]
        x_k_i1 = points[i + 1].location[0]
        # X-coords of handles relevant to this segment
        x_hr_i_orig = final_right_h[i][0]  # P1.x original
        x_hl_i1_orig = final_left_h[i + 1][0]  # P2.x original

        # Apply clamping based on x0 <= x1 <= x2 <= x3
        # 1. Clamp P1.x (x_hr_i) >= P0.x (x_k_i)
        x_hr_i_clamped = max(x_k_i, x_hr_i_orig)
        # 2. Clamp P2.x (x_hl_i1) <= P3.x (x_k_i1)
        x_hl_i1_clamped = min(x_k_i1, x_hl_i1_orig)
        # 3. Check for crossover: P1.x > P2.x after clamping
        if x_hr_i_clamped > x_hl_i1_clamped:
            # Crossover occurred. Handles need to meet.
            # Calculate the midpoint of the conflicting interval.
            x_split = (x_hr_i_clamped + x_hl_i1_clamped) / 2.0
            # Ensure the split point is strictly within the knot interval.
            x_split = max(x_k_i, min(x_k_i1, x_split))
            # Set both handles' X to the split point.
            final_right_h[i][0] = x_split
            final_left_h[i + 1][0] = x_split
        else:
            # No crossover, just apply the individual clamps.
            final_right_h[i][0] = x_hr_i_clamped
            final_left_h[i + 1][0] = x_hl_i1_clamped
        continue

    return final_left_h, final_right_h


def reverseengineer_curve_to_bezsegs(
    points, monotonic=False, calculate_intercept=False
):
    """
    Convert a Blender CurveProfile or CurveMapping object to a NumPy array of Bézier segments,
    calculating handle positions based on Blender's internal C functions,
    Returns: np.ndarray: An (N-1) x 8 NumPy array [P0x, P0y, P1x, P1y, P2x, P2y, P3x, P3y] or None if a segments list cannot be obtained.
    """
    n_points = len(points)

    if n_points < 2:
        return np.empty((0, 8), dtype=float)

    # Calculate initial handle positions
    all_left_h = [np.zeros(2) for _ in range(n_points)]
    all_right_h = [np.zeros(2) for _ in range(n_points)]

    for i in range(n_points):
        current_pt = points[i]
        prev_pt = points[i - 1] if i > 0 else None
        next_pt = points[i + 1] if i < n_points - 1 else None

        left_h, right_h = _guess_handles(current_pt, prev_pt, next_pt)
        all_left_h[i] = left_h
        all_right_h[i] = right_h
        continue

    # Apply Endpoint Handle Correction (if applicable)
    # This is a simplified version, adjust if needed for specific handle types/logic
    if n_points > 2:
        if points[0].handle_type == "AUTO":
            P0 = np.array(points[0].location, dtype=float)
            P1_orig = all_right_h[0]
            hlen = np.linalg.norm(np.subtract(P0, P1_orig))  #
            if hlen > 1e-7:
                neighbor_handle = all_left_h[1]
                clamped_neighbor_x = max(neighbor_handle[0], P0[0])
                direction_vec = np.array(
                    [clamped_neighbor_x - P0[0], neighbor_handle[1] - P0[1]]
                )
                nlen = np.linalg.norm(direction_vec)
                if nlen > 1e-7:
                    scaled_direction = direction_vec * (hlen / nlen)
                    all_right_h[0] = P0 + scaled_direction

        last_idx = n_points - 1
        if points[last_idx].handle_type == "AUTO":
            P3 = np.array(points[last_idx].location, dtype=float)
            P2_orig = all_left_h[last_idx]
            hlen = np.linalg.norm(np.subtract(P3, P2_orig))  #
            if hlen > 1e-7:
                neighbor_handle = all_right_h[last_idx - 1]
                clamped_neighbor_x = min(neighbor_handle[0], P3[0])
                direction_vec = np.array(
                    [clamped_neighbor_x - P3[0], neighbor_handle[1] - P3[1]]
                )
                nlen = np.linalg.norm(direction_vec)
                if nlen > 1e-7:
                    scaled_direction = direction_vec * (hlen / nlen)
                    all_left_h[last_idx] = P3 + scaled_direction

    # Apply X-Monotonicity
    final_left_h = None
    final_right_h = None
    if monotonic:
        final_left_h, final_right_h = _ensure_monotonic_handles(
            points, all_left_h, all_right_h
        )
    else:
        final_left_h = [h.copy() for h in all_left_h]
        final_right_h = [h.copy() for h in all_right_h]

    # Build segments
    segments_list = []
    for i in range(0, n_points - 1):

        P0 = np.array(points[i].location, dtype=float)
        P3 = np.array(points[i + 1].location, dtype=float)

        P1 = final_right_h[i]
        P2 = final_left_h[i + 1]

        if (
            np.any(np.isnan(P0))
            or np.any(np.isnan(P1))
            or np.any(np.isnan(P2))
            or np.any(np.isnan(P3))
        ):
            continue

        segment_row = np.concatenate((P0, P1, P2, P3))
        segments_list.append(segment_row)
        continue

    if not segments_list:
        return None
    return np.array(segments_list, dtype=float)


def reverseengineer_curveprofile_to_bezsegs(curve: bpy.types.CurveProfile):
    """
    Convert a Blender CurveProfile object to a NumPy array of Bézier segments,
    calculating handle positions based on Blender's internal C functions.
    Returns: np.ndarray: An (N-1) x 8 NumPy array [P0x, P0y, P1x, P1y, P2x, P2y, P3x, P3y] or None if a segments list cannot be obtained.
    """
    return reverseengineer_curve_to_bezsegs(curve.points, monotonic=False)


def reverseengineer_curvemapping_to_bezsegs(curve: bpy.types.CurveMap):
    """
    Convert a Blender CurveProfile object to a NumPy array of Bézier segments,
    calculating handle positions based on Blender's internal C functions,
    ensuring X-monotonicity.
    Returns: np.ndarray: An (N-1) x 8 NumPy array [P0x, P0y, P1x, P1y, P2x, P2y, P3x, P3y] or None if a segments list cannot be obtained.
    """

    return reverseengineer_curve_to_bezsegs(
        curve.points, monotonic=True, calculate_intercept=True
    )
