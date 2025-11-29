import bpy
import numpy as np

positions_index_switch = "Positions"
left_index_switch = "LeftPositions"
right_index_switch = "RightPositions"
curve_points_count = "CurvePoints"


def set_control_points(control_points, node_tree: bpy.types.NodeTree):
    positions: bpy.types.GeometryNodeIndexSwitch = node_tree.nodes[
        positions_index_switch
    ]  # pyright: ignore[reportAssignmentType]
    left_positions: bpy.types.GeometryNodeIndexSwitch = node_tree.nodes[
        left_index_switch
    ]  # pyright: ignore[reportAssignmentType]
    right_positions: bpy.types.GeometryNodeIndexSwitch = node_tree.nodes[
        right_index_switch
    ]  # pyright: ignore[reportAssignmentType]
    count = node_tree.nodes[curve_points_count]

    new_length = len(control_points) + 1
    count.integer = new_length

    def _reconcile_length(positions: bpy.types.GeometryNodeIndexSwitch):
        existing_length = len(positions.index_switch_items)
        if existing_length > new_length:
            for i in range(existing_length - 1, new_length - 1, -1):
                item = positions.index_switch_items[i]
                positions.index_switch_items.remove(item)
        else:
            for i in range(existing_length, new_length):
                positions.index_switch_items.new()

    _reconcile_length(positions)
    _reconcile_length(left_positions)
    _reconcile_length(right_positions)

    # [P0x, P0y, P1x, P1y, P2x, P2y, P3x, P3y]
    for i in range(0, new_length - 1):
        prev = control_points[i]
        current = control_points[i]
        if i > 0:
            prev = control_points[i - 1]

        input_position: bpy.types.NodeSocket = positions.inputs[i + 1]
        input_left_position: bpy.types.NodeSocket = left_positions.inputs[i + 1]
        input_right_position: bpy.types.NodeSocket = right_positions.inputs[i + 1]

        position_x = current[0]
        position_y = current[1]
        next_cp_x = current[2]
        next_cp_y = current[3]
        prev_cp_x = prev[4]
        prev_cp_y = prev[5]
        if i == 0:
            prev_cp_x = position_x
            prev_cp_y = position_y
        input_position.default_value[0] = position_x
        input_position.default_value[1] = position_y
        input_right_position.default_value[0] = next_cp_x
        input_right_position.default_value[1] = next_cp_y
        input_left_position.default_value[0] = prev_cp_x
        input_left_position.default_value[1] = prev_cp_y

    input_position: bpy.types.NodeSocket = positions.inputs[len(positions.inputs) - 2]
    input_left_position: bpy.types.NodeSocket = left_positions.inputs[
        len(positions.inputs) - 2
    ]
    input_right_position: bpy.types.NodeSocket = right_positions.inputs[
        len(positions.inputs) - 2
    ]

    current = control_points[-1]
    position_x = current[6]
    position_y = current[7]
    next_cp_x = position_x
    next_cp_y = position_y
    prev_cp_x = current[4]
    prev_cp_y = current[5]
    input_position.default_value[0] = position_x
    input_position.default_value[1] = position_y
    input_right_position.default_value[0] = next_cp_x
    input_right_position.default_value[1] = next_cp_y
    input_left_position.default_value[0] = prev_cp_x
    input_left_position.default_value[1] = prev_cp_y

    return None
