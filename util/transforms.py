import math

from bpy_extras.io_utils import axis_conversion
import mathutils


class Corrector:
	def __init__(self):
		self.local = axis_conversion(from_forward='X', from_up='Y', to_forward='Y', to_up='Z').to_4x4()
		# self.local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
		self.local_inv = self.local.inverted()

	def import_keymat(self, rest_rot_inv, key_matrix):
		key_matrix = rest_rot_inv @ key_matrix
		return self.local @ key_matrix @ self.local_inv

	def export_keymat(self, rest_rot, key_matrix):
		key_matrix = self.local_inv @ key_matrix @ self.local
		return rest_rot @ key_matrix

	# # https://stackoverflow.com/questions/1263072/changing-a-matrix-from-right-handed-to-left-handed-coordinate-system
	# def to_blender(self, nif_armature_space_matrix):
	# 	# post multiplication: local space
	# 	# position of xflip does not matter
	# 	return self.xflip @ self.correction_glob @ nif_armature_space_matrix @ self.correction_inv @ self.xflip
	#
	# def from_blender(self, blender_armature_space_matrix):
	# 	# xflip must be done before the conversions
	# 	bind = self.xflip @ blender_armature_space_matrix @ self.xflip
	# 	return self.correction_glob_inv @ bind @ self.correction


def center_origin_to_matrix(n_center, n_dir):
	"""Helper for capsules to transform nif data into a local matrix """
	# get the rotation that makes (1,0,0) match m_dir
	m_dir = mathutils.Vector(n_dir).normalized()
	rot = m_dir.to_track_quat("Z", "Y").to_matrix().to_4x4()
	rot.translation = n_center
	return rot


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
