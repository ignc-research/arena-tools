"""
    This file contains a blender script used to generate a mesh file from a OccupancyMap in SVG format.
"""
import bpy
import sys
import math

argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

width = argv[0]
height = argv[1]
in_path = argv[2]
out_path = argv[3]

# Get rid of any existing objects
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# Import the SVG as a curve
bpy.ops.import_curve.svg(
    filepath=f"{in_path}/output.svg",
    filter_glob="*.svg",
)

# Extrude the curve to reach desired depth/height
curve = bpy.data.objects["Curve"]
bpy.ops.object.select_all(action="SELECT")
curve.select_set( state = True, view_layer = bpy.context.view_layer )
bpy.context.view_layer.objects.active = curve
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.curve.select_all(action="SELECT")
curve.data.extrude = 0.16
bpy.ops.object.mode_set(mode="OBJECT")

# Change the dimensions of the curve according to the map image and resolution
curve.dimensions = (float(width), float(height), 2.0)

# Convert into mesh and export as .DAE file
bpy.ops.object.convert(target="MESH")
bpy.ops.wm.collada_export(
    filepath=f"{out_path}/map.dae"
)
