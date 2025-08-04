import bpy
import logging

from common_bfb import mesh_from_data
from util.transforms import center_origin_to_matrix, correction_local


def attach_capsule(b_armature_ob, b_ob, bone_name):
	b_ob.parent = b_armature_ob
	b_ob.parent_type = 'BONE'
	if bone_name in b_armature_ob.data.bones:
		parent_bone = b_armature_ob.data.bones[bone_name]
	else:
		parent_bone = b_armature_ob.data.bones[0]
		logging.warning(f"Attaching capsule to '{parent_bone.name}' instead of the missing '{bone_name}'")
	b_ob.parent_bone = parent_bone.name
	b_ob.location.y -= parent_bone.length


def create_capsule(name, start, end, r):
	# positions of the box verts
	start = correction_local @ start
	end = correction_local @ end
	minx = miny = -r
	maxx = maxy = +r
	extent = end-start
	minz = -(extent.length + 2 * r) / 2
	maxz = +(extent.length + 2 * r) / 2
	# print(name, start, end)
	# create blender object
	b_obj, b_me = box_from_extents(name, minx, maxx, miny, maxy, minz, maxz, None)
	# apply transform in local space
	bind = center_origin_to_matrix((start+end)/2, extent)
	b_obj.matrix_local = bind
	set_b_collider(b_obj, bounds_type="CAPSULE", display_type="CAPSULE")
	return b_obj


def create_sphere(name, x, y, z, r):
	b_obj, b_me = box_from_extents(name, -r, r, -r, r, -r, r, None)
	set_b_collider(b_obj, bounds_type="SPHERE", display_type="SPHERE")
	b_obj.location = (x, y, z)
	return b_obj


def create_bounding_box(name, matrix, x, y, z):
	b_obj, b_me = box_from_extents(name, -x/2, x/2, -y/2, y/2, -z/2, z/2, None)
	b_obj.matrix_local = matrix
	set_b_collider(b_obj)
	return b_obj


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
