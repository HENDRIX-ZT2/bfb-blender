import logging

from common_bfb import correction_local, box_from_extents, center_origin_to_matrix, set_b_collider


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
