import bpy

class MaterializeAddonPreferences(bpy.types.AddonPreferences):
    # This must match the add-on name, use `__package__`
    # when defining this for add-on extensions or a sub-module of a Python package.
    bl_idname = "materialize_nodes"

    debug_mode: bpy.types.BoolProperty(
        name="Debug Mode",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Preferences for Materialize Nodes")
        layout.prop(self, "debug_mode")


classes = (MaterializeAddonPreferences)