import bpy
import mathutils

from common_bfb import create_ob, name_import
from util.transforms import correction_local, correction_global


def import_bones(basename, data, scales):
	# create the b_armature_ob
	b_armature_data = bpy.data.armatures.new(basename[:-4])
	b_armature_data.show_axes = True
	b_armature_data.display_type = 'STICK'
	b_armature_ob = create_ob(bpy.context.scene, basename[:-4], b_armature_data)
	b_armature_ob.show_in_front = True
	bpy.ops.object.mode_set(mode='EDIT')
	mat_storage = {}
	for bfb_bone in data.bones:
		bone_name = name_import(bfb_bone.name)
		bind = get_matrix(bfb_bone.matrix)
		# support for bone scale
		scale = bind.to_scale()[0]
		if int(round(scale * 1000)) != 1000:
			scales[bone_name] = scale
		# create a bone
		b_edit_bone = b_armature_data.edit_bones.new(bone_name)
		# parent it and get the armature space matrix
		if bfb_bone.parent_id > 0:
			# calculate bfb armature space matrix
			bind = mat_storage[bfb_bone.parent_id] @ bind
			b_edit_bone.parent = b_armature_data.edit_bones[bfb_bone.parent_id - 1]
		# we store the bfb space armature matrix of each bone
		mat_storage[bfb_bone.id] = bind.copy()
		# set transformation
		bind = correction_global @ correction_local @ bind @ correction_local.inverted()
		tail, roll = bpy.types.Bone.AxisRollFromMatrix(bind.to_3x3())
		b_edit_bone.head = bind.to_translation()
		b_edit_bone.tail = tail + b_edit_bone.head
		b_edit_bone.roll = roll
	# fix the bone length
	for edit_bone in b_armature_data.edit_bones:
		fix_bone_length(edit_bone)
	bpy.ops.object.mode_set(mode='OBJECT')
	# priority
	for bfb_bone in data.bones:
		bone_name = name_import(bfb_bone.name)
		p_bone = b_armature_ob.pose.bones[bone_name]
		p_bone["priority"] = bfb_bone.priority
	return b_armature_ob

def get_matrix(matrix):
	matrix = mathutils.Matrix(matrix.data)
	matrix.transpose()
	return matrix


def fix_bone_length(edit_bone):
	# don't change Bip01
	if edit_bone.parent:
		if edit_bone.children:
			childheads = mathutils.Vector()
			for child in edit_bone.children:
				childheads += child.head
			bone_length = (edit_bone.head - childheads / len(edit_bone.children)).length
			if bone_length < 0.01:
				bone_length = 0.25
		# end of a chain
		else:
			bone_length = edit_bone.parent.length
		edit_bone.length = bone_length


def apply_rest_scale_correction(b_armature_ob, scales, anim, skinned_meshes):
	# handle scale on armature and meshes
	if b_armature_ob and scales:
		# set inverse scale to all bones
		for bone_name, scale in scales.items():
			p_bone = b_armature_ob.pose.bones[bone_name]
			p_bone.matrix_basis = mathutils.Matrix.Scale(1 / scale, 4)
		depsgraph = bpy.context.evaluated_depsgraph_get()
		# apply skin deformation
		for ob in skinned_meshes:
			object_eval = ob.evaluated_get(depsgraph)
			ob.data = bpy.data.meshes.new_from_object(object_eval)
		# remove scales from armature
		bpy.context.view_layer.objects.active = b_armature_ob
		bpy.ops.object.mode_set(mode='POSE')
		bpy.ops.pose.armature_apply()
		bpy.ops.object.mode_set(mode='OBJECT')
		# add scale back in as dummy action
		scale_action = anim.create_action(b_armature_ob, "!scale!")
		for bone_name, scale in scales.items():
			fcurves = [scale_action.fcurves.new(data_path=f'pose.bones["{bone_name}"].scale', index=i,
												action_group=bone_name) for i in range(3)]
			for fcurve in fcurves:
				fcurve.keyframe_points.insert(0, scale)
