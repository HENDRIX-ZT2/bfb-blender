import logging
import math
import bpy
import mathutils
import os
import numpy as np


def assign_to_lod(ob, level):
	"""Adds a newly created object to a lod collection, creates one if neeed, and sets their visibility"""
	lod_name = f"LOD{level}"
	if lod_name not in bpy.data.collections:
		coll = bpy.data.collections.new(lod_name)
		bpy.context.scene.collection.children.link(coll)
	else:
		coll = bpy.data.collections[lod_name]
	# Link active object to the new collection
	coll.objects.link(ob)
	# show lod 0, hide the others
	should_hide = level != 0
	# hide object in view layer
	hide_collection(lod_name, should_hide)
	# hide object in view layer
	ob.hide_set(should_hide, view_layer=bpy.context.view_layer)


def hide_collection(lod_name, should_hide):
	# get view layer, hide collection there
	# print(list(x for x in bpy.context.view_layer.layer_collection.children))
	bpy.context.view_layer.layer_collection.children[lod_name].hide_viewport = should_hide


def ensure_active_object():
	# ensure that we have objects in the scene
	if bpy.context.scene.objects:
		# operator needs an active object, set one if missing (eg. user had deleted the active object)
		if not bpy.context.view_layer.objects.active:
			bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
		# now enter object mode on the active object, if we aren't already in it
		bpy.ops.object.mode_set(mode="OBJECT")
	else:
		print("No objects in scene, nothing to export!")


def load_config():
	d = {}
	f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_bfb.ini"), 'rb')
	new_list = f.read().decode("utf-8").split("\n")
	f.close()
	for line in new_list:
		try:
			(key, val) = line.split("=")
			d[key] = val
		except:
			pass
	return d


def update_config(key, val):
	config = load_config()
	if key not in config.keys():
		config[key] = val
		stream = config_to_str(config)
	elif val != str(config[key]):
		config[key] = val
		stream = config_to_str(config)
	else:
		return
	f = open(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_bfb.ini")), 'wb')
	f.write(stream.encode("utf-8"))
	f.close()


def config_to_str(config):
	stream = ""
	for key in config:
		stream += (key + "=" + config[key] + "\n")
	return stream


def link_to_collection(scene, ob, coll_name):
	# turn any relative collection names to include the scene prefix
	if not coll_name.startswith(f"{scene.name}_"):
		coll_name = f"{scene.name}_{coll_name}"
	if coll_name not in bpy.data.collections:
		coll = bpy.data.collections.new(coll_name)
		scene.collection.children.link(coll)
	else:
		coll = bpy.data.collections[coll_name]
	# Link active object to the new collection
	coll.objects.link(ob)
	return coll_name


def create_ob(scene, ob_name, ob_data, coll_name=None, coll=None):
	logging.debug(f"Adding {ob_name} to scene {scene.name}")
	ob = bpy.data.objects.new(ob_name, ob_data)
	if coll_name is not None:
		link_to_collection(scene, ob, coll_name)
	elif coll is not None:
		coll.objects.link(ob)
	else:
		# link to scene root collection
		scene.collection.objects.link(ob)
	bpy.context.view_layer.objects.active = ob
	return ob


def create_anim(ob, anim_name):
	action = bpy.data.actions.new(name=anim_name)
	action.use_fake_user = True
	ob.animation_data_create()
	ob.animation_data.action = action
	return action


def per_loop(flattened_tris, per_vertex_input):
	return np.take(per_vertex_input, flattened_tris, axis=0)


def mesh_from_data(scene, name, verts, faces, wireframe=False, coll_name=None, coll=None):
	me = bpy.data.meshes.new(name)
	me.from_pydata(verts, [], faces)
	# me.update()
	ob = create_ob(scene, name, me, coll_name=coll_name, coll=coll)
	if wireframe:
		ob.display_type = 'WIRE'
	return ob, me


def create_sphere(name, x, y, z, r):
	verts = [(0.50, 0.00, 0.87), (0.87, 0.00, 0.50), (1.00, 0.00, -0.00), (0.87, 0.00, -0.50), (0.50, 0.00, -0.87),
			 (0.35, 0.35, -0.87), (0.61, 0.61, -0.50), (0.71, 0.71, 0.00), (0.61, 0.61, 0.50), (0.35, 0.35, 0.87),
			 (0.00, 0.00, 1.00), (-0.00, 0.50, 0.87), (-0.00, 0.87, 0.50), (-0.00, 1.00, 0.00), (-0.00, 0.87, -0.50),
			 (-0.00, 0.50, -0.87), (-0.35, 0.35, -0.87), (-0.61, 0.61, -0.50), (-0.71, 0.71, 0.00), (-0.61, 0.61, 0.50),
			 (-0.35, 0.35, 0.87), (-0.50, -0.00, 0.87), (-0.87, -0.00, 0.50), (-1.00, -0.00, 0.00),
			 (-0.87, -0.00, -0.50), (-0.50, -0.00, -0.87), (-0.00, -0.00, -1.00), (-0.35, -0.35, -0.87),
			 (-0.61, -0.61, -0.50), (-0.71, -0.71, 0.00), (-0.61, -0.61, 0.50), (-0.35, -0.35, 0.87),
			 (0.00, -0.50, 0.87), (0.00, -0.87, 0.50), (0.00, -1.00, 0.00), (0.00, -0.87, -0.50), (0.00, -0.50, -0.87),
			 (0.35, -0.35, -0.87), (0.61, -0.61, -0.50), (0.71, -0.71, 0.00), (0.61, -0.61, 0.50), (0.35, -0.35, 0.87)]
	faces = [(26, 5, 4), (4, 5, 6, 3), (3, 6, 7, 2), (2, 7, 8, 1), (9, 0, 1, 8), (0, 9, 10), (9, 11, 10),
			 (8, 12, 11, 9), (7, 13, 12, 8), (6, 14, 13, 7), (5, 15, 14, 6), (26, 15, 5), (26, 16, 15),
			 (15, 16, 17, 14), (14, 17, 18, 13), (13, 18, 19, 12), (12, 19, 20, 11), (11, 20, 10), (20, 21, 10),
			 (19, 22, 21, 20), (18, 23, 22, 19), (17, 24, 23, 18), (16, 25, 24, 17), (26, 25, 16), (26, 27, 25),
			 (25, 27, 28, 24), (24, 28, 29, 23), (23, 29, 30, 22), (22, 30, 31, 21), (21, 31, 10), (31, 32, 10),
			 (30, 33, 32, 31), (29, 34, 33, 30), (28, 35, 34, 29), (27, 36, 35, 28), (26, 36, 27), (26, 37, 36),
			 (36, 37, 38, 35), (35, 38, 39, 34), (34, 39, 40, 33), (33, 40, 41, 32), (32, 41, 10), (41, 0, 10),
			 (0, 41, 40, 1), (39, 2, 1, 40), (38, 3, 2, 39), (37, 4, 3, 38), (26, 4, 37)]
	ob, me = mesh_from_data(name, verts, faces)
	for v in me.vertices:
		v.co = v.co * r
	ob.location = (x, y, z)
	# ob.layers = select_layer(5)
	return ob


def create_bounding_box(name, matrix, x, y, z):
	verts = [(x / 2, y / 2, -z / 2), (x / 2, -y / 2, -z / 2), (-x / 2, -y / 2, -z / 2), (-x / 2, y / 2, -z / 2),
			 (x / 2, y / 2, z / 2), (x / 2, -y / 2, z / 2), (-x / 2, -y / 2, z / 2), (-x / 2, y / 2, z / 2)]
	faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
	ob, me = mesh_from_data(name, verts, faces)
	ob.matrix_local = matrix
	# ob.layers = select_layer(5)
	return ob


def set_b_collider(b_obj, bounds_type='BOX', display_type='BOX'):
	"""Helper function to set up b_obj so it becomes recognizable as a collision object"""
	# set bounds type
	if display_type == "MESH":
		b_obj.display_type = 'WIRE'
	else:
		b_obj.show_bounds = True
		b_obj.display_type = 'BOUNDS'
		b_obj.display_bounds_type = display_type

	# alternative
	bpy.context.view_layer.objects.active = b_obj
	with bpy.context.temp_override(selected_objects=[b_obj], object=b_obj, active_object=b_obj):
		logging.debug(f"Operating on obj '{b_obj.name}'")
		bpy.ops.rigidbody.object_add()

	#bpy.context.view_layer.objects.active = b_obj
	#bpy.ops.rigidbody.object_add()

	b_r_body = b_obj.rigid_body
	b_r_body.enabled = True
	# b_r_body.use_margin = True
	# b_r_body.collision_margin = radius
	b_r_body.collision_shape = bounds_type
	# if they are set to active they explode once you play back an anim
	b_r_body.type = "PASSIVE"


def box_from_extents(b_name, minx, maxx, miny, maxy, minz, maxz, coll=None):
	verts = []
	for x in [minx, maxx]:
		for y in [miny, maxy]:
			for z in [minz, maxz]:
				verts.append((x, y, z))
	faces = [[0, 1, 3, 2], [6, 7, 5, 4], [0, 2, 6, 4], [3, 1, 5, 7], [4, 5, 1, 0], [7, 6, 2, 3]]
	scene = bpy.context.scene
	return mesh_from_data(scene, b_name, verts, faces, coll_name=None, coll=coll)

def center_origin_to_matrix(n_center, n_dir):
	"""Helper for capsules to transform nif data into a local matrix """
	# get the rotation that makes (1,0,0) match m_dir
	m_dir = mathutils.Vector(n_dir).normalized()
	rot = m_dir.to_track_quat("Z", "Y").to_matrix().to_4x4()
	rot.translation = n_center
	return rot


def create_empty(parent, name, matrix):
	empty = create_ob(bpy.context.scene, name, None)
	if parent:
		empty.parent = parent
	empty.matrix_local = matrix
	empty.empty_display_type = "ARROWS"
	return empty


correction_local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
correction_global = mathutils.Euler((math.radians(-90), math.radians(-90), 0)).to_matrix().to_4x4()


def get_bfb_matrix(b_bone):
	bind = correction_global.inverted() @ correction_local.inverted() @ b_bone.matrix_local @ correction_local
	if b_bone.parent:
		p_bind_restored = correction_global.inverted() @ correction_local.inverted() @ b_bone.parent.matrix_local @ correction_local
		bind = p_bind_restored.inverted() @ bind

	return bind.transposed()


def decompose_srt(mat):
	mat.transpose()
	b_scale = 1.0
	b_rot = mat.to_quaternion().to_matrix()
	b_trans = mat.translation
	return b_scale, b_rot, b_trans


def blendername_to_bfbname(s):
	if 'Bip01 ' in s:
		if '.L' in s:
			s = s[:-2].replace('Bip01 ', 'Bip01 L ')
		elif '.R' in s:
			s = s[:-2].replace('Bip01 ', 'Bip01 R ')
	return s


def bfbname_to_blendername(b: bytes):
	s = b.rstrip(b"\x00").decode("utf-8")
	return name_import(s)


def name_import(s: str):
	if " l " in s:
		s += ".L"
	elif " L " in s:
		s += ".L"
	if " r " in s:
		s += ".R"
	elif " R " in s:
		s += ".R"
	return s.title().replace(" R ", " ").replace(" L ", " ").replace("back", "Back").replace("front", "Front").replace(
		"left", "Left").replace("right", "Right").replace("Nonaccum", "NonAccum").replace("Upperarm",
																						  "UpperArm").replace(
		"Horselink", "HorseLink")


def get_armature():
	src_armatures = [ob for ob in bpy.data.objects if ob.type == "ARMATURE"]
	# do we have armatures?
	if src_armatures:
		# see if one of these is selected -> get only that one
		if len(src_armatures) > 1:
			sel_armatures = [ob for ob in src_armatures if ob.select_get()]
			if sel_armatures:
				return sel_armatures[0]
		return src_armatures[0]
