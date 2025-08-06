import mathutils

from common_bfb import name_export
from util.transforms import Corrector


def clear_pose(b_armature_ob):
	# clear pose to ensure no distorted pose is applied
	for p_bone in b_armature_ob.pose.bones:
		p_bone.matrix_basis = mathutils.Matrix().to_4x4()


def get_valid_bones(b_armature):
	return [bone for bone in b_armature.data.bones.values() if bone.parent or bone.name == "Bip01"]


def export_bones(b_armature, mesh_block):
	b_bones = get_valid_bones(b_armature)
	# export bones
	mesh_block.data.num_bones = len(b_bones)
	mesh_block.data.reset_field("bones")
	for b_bone, p_bone, bfb_bone in zip(b_bones, b_armature.pose.bones, mesh_block.data.bones):
		bfb_bone.id = b_bones.index(b_bone) + 1
		if b_bone.parent:
			bfb_bone.parent_id = b_bones.index(b_bone.parent) + 1
		else:
			bfb_bone.parent_id = 0
		scale_matrix = get_rest_scale_matrix(b_bone)
		bfb_bone.priority = p_bone.get("priority", -1)
		bfb_bone.name = name_export(b_bone.name).lower()
		bfb_bone.matrix.set_rows(scale_matrix @ Corrector.get_bfb_matrix(b_bone))


def get_rest_scale_matrix(b_bone):
	# rest scale support
	try:
		group = b_scale_action.groups[b_bone.name]
		scales = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("scale")]
		scale = scales[0].keyframe_points[0].co[1]
	except:
		scale = 1.0
	return mathutils.Matrix.Scale(scale, 4)
