import bpy
import mathutils
import numpy as np


def add_fx_wind(fixed_items, wmin, wmax):
	for ob in bpy.context.selected_objects:
		print(ob.name)
		me = ob.data
		if ob.type == "MESH":
			if "fx_wind" not in ob.vertex_groups:
				ob.vertex_groups.new(name="fx_wind")

			# set the center
			center = mathutils.Vector()
			if fixed_items == "1":
				for v in me.vertices:
					center += v.co
				center /= len(me.vertices)

			weights = np.empty(len(me.vertices), dtype=np.float32)
			if fixed_items == "0":
				weights[:] = [v.co.z for v in me.vertices]
			if fixed_items == "1":
				weights[:] = [(v.co - center).length for v in me.vertices]
			if fixed_items == "2":
				weights[:] = [(v.co - center).length for v in me.vertices]
			if fixed_items == "3":
				weights[:] = [v.co.xy.length for v in me.vertices]
			weights = (wmax-wmin) * (weights - np.min(weights)) / np.ptp(weights) + wmin
			for i in range(len(weights)):
				ob.vertex_groups["fx_wind"].add([i], weights[i], 'REPLACE')
