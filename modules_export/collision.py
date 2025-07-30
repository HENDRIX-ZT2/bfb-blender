import logging

import mathutils

from bfb_gen.formats.bfb.enums.BlockType import BlockType
from common_bfb import correction_local


def get_collider_matrix(b_hitcheck):
	"""Return the matrix relative to the armature for an object parented to a bone"""
	# reflect the parenting: bone > hitchecks
	b_armature = b_hitcheck.parent
	b_bone = b_armature.data.bones[b_hitcheck.parent_bone]
	m = mathutils.Matrix(b_hitcheck.matrix_basis)
	m.translation.y += b_bone.length
	# print(b_bone.matrix_local)
	# print(b_hitcheck.matrix_local)
	# print(b_bone.matrix_local @ b_hitcheck.matrix_local)
	# return b_bone.matrix_local @ m
	return m
	# return b_bone.matrix_local.inverted() @ m @ b_hitcheck.matrix_local


def export_capsule(b_ob, bfb):
	matrix = get_collider_matrix(b_ob)
	# print(matrix)
	offset = matrix.translation
	# calculate the direction unit vector
	v_dir = (mathutils.Vector((0, 0, 1)) @ matrix.to_3x3().inverted()).normalized()

	extent = b_ob.dimensions.z - b_ob.dimensions.x
	v_dir *= extent / 2
	radius = b_ob.dimensions.x / 2
	# print(offset, v_dir, radius)
	start = offset - v_dir
	end = offset + v_dir
	start = correction_local.inverted() @ start
	end = correction_local.inverted() @ end
	print(start, end)
	block = bfb.create_block(b_ob, bfb, BlockType.CAPSULE)
	block.name = "capsule"
	block.data.start[:] = start
	block.data.end[:] = end
	block.data.radius = radius
	return block.id


def export_bounding_box(b_ob, bfb):
	logging.debug('Found bounding box collider')
	me = b_ob.data
	block = bfb.create_block(b_ob, bfb, BlockType.BOUNDING_BOX)
	block.name = "orientedbox"
	block.data.matrix.set_rows(b_ob.matrix_local)
	block.data.extent[:] = me.vertices[4].co * 2
	return block.id


def export_sphere(b_ob, bfb):
	logging.debug('Found sphere collider')
	me = b_ob.data
	block = bfb.create_block(b_ob, bfb, BlockType.SPHERE)
	block.name = "sphere"
	center = (me.vertices[2].co + me.vertices[23].co) / 2
	block.data.pos[:] = b_ob.location
	block.data.radius = (me.vertices[2].co - center).length
	return block.id
