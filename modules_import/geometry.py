import logging

import bpy


def set_auto_smooth_safe(b_me):
	"""Blender 4.1 removes the property and uses custom normals automatically if they are present"""
	if hasattr(b_me, "use_auto_smooth"):
		b_me.use_auto_smooth = True


def ob_postpro(b_me, use_mirror_mesh, cleanup_geometry):
	logging.debug("Postprocessing geometry")
	bpy.ops.object.mode_set(mode='EDIT')
	if use_mirror_mesh:
		bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
		bpy.ops.mesh.select_all(action='SELECT')
	if b_me.uv_layers:
		bpy.ops.uv.select_all(action='SELECT')
		bpy.ops.uv.seams_from_islands()
	if cleanup_geometry:
		bpy.ops.mesh.tris_convert_to_quads(uvs=True, vcols=True, seam=True, sharp=True)
	bpy.ops.object.mode_set(mode='OBJECT')


def append_mirror_modifier(b_ob):
	mod = b_ob.modifiers.new('Mirror', 'MIRROR')
	mod.use_clip = True
	mod.use_mirror_merge = True
	mod.use_mirror_vertex_groups = True
	# mod.use_x = True
	mod.use_axis = (True, False, False)
	mod.merge_threshold = 0.001