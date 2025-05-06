import logging

import bpy


def set_auto_smooth_safe(b_me):
	"""Blender 4.1 removes the property and uses custom normals automatically if they are present"""
	if hasattr(b_me, "use_auto_smooth"):
		b_me.use_auto_smooth = True


def ob_postpro(use_mirror_mesh):
	logging.debug("Postprocessing geometry")
	bpy.ops.object.mode_set(mode='EDIT')
	if use_mirror_mesh:
		bpy.ops.mesh.bisect(plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
		bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.uv.select_all(action='SELECT')
	bpy.ops.uv.seams_from_islands()
	# todo add flag or use safe code that does not break UVs
	bpy.ops.mesh.tris_convert_to_quads()
	bpy.ops.object.mode_set(mode='OBJECT')


def append_mirror_modifier(b_ob):
	mod = b_ob.modifiers.new('Mirror', 'MIRROR')
	mod.use_clip = True
	mod.use_mirror_merge = True
	mod.use_mirror_vertex_groups = True
	# mod.use_x = True
	mod.use_axis = (True, False, False)
	mod.merge_threshold = 0.001


def get_valid_lod_objects(m_lod):
	"""Get objects, but skip later shells for JWE2"""
	for m_ob in m_lod.objects:
		mesh = m_ob.mesh
		if hasattr(mesh, "vert_chunks"):
			tri_chunk = mesh.tri_chunks[0]
			if tri_chunk.shell_index:
				logging.debug(f"Skipping import of shell duplicate {tri_chunk.shell_index}")
				continue
		yield m_ob


def import_mesh_properties(b_me, mesh):
	try:
		# store mesh unknowns
		# cast the bitfield to int
		b_me["flag"] = int(mesh.flag)
		if mesh.context.version > 13:
			b_me["unk_f0"] = float(mesh.unk_float_0)
		if mesh.context.version > 32:
			b_me["unk_f1"] = float(mesh.unk_float_1)
		if hasattr(mesh, "vert_chunks"):
			tri_chunk = mesh.tri_chunks[0]
			b_me["shell_count"] = tri_chunk.shell_count
	except:
		logging.exception("Setting unks failed")