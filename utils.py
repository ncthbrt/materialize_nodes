import bpy.types


def is_materialize_modifier(obj):
    index = len(obj.modifiers) - 1
    if index < 0:
        return False
    modifier = obj.modifiers[index]
    if modifier.type != "NODES":
        return False
    if "materialize" not in modifier.node_group:
        return False
    return (obj, modifier)


def get_evaluated_geometry(obj, context):
    depsgraph: bpy.types.Depsgraph = context.evaluated_depsgraph_get()
    object_eval = obj.evaluated_get(depsgraph)
    data = object_eval.evaluated_geometry()
    return data
