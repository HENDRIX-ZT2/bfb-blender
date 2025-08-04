from bpy_extras.io_utils import axis_conversion
import mathutils


class Corrector:
	# https://stackoverflow.com/questions/1263072/changing-a-matrix-from-right-handed-to-left-handed-coordinate-system

	# <Matrix 4x4 (-0.0000, 0.0000,  1.0000, 0.0000)
	#             ( 1.0000, 0.0000,  0.0000, 0.0000)
	#             (-0.0000, 1.0000, -0.0000, 0.0000)
	#             ( 0.0000, 0.0000,  0.0000, 1.0000)>
	local = axis_conversion(from_forward='X', from_up='Y', to_forward='Y', to_up='Z').to_4x4()
	local_inv = local.inverted()

	@classmethod
	def import_vec(cls, vec):
		return cls.local @ vec

	@classmethod
	def export_vec(cls, vec):
		return cls.local_inv @ vec

	@classmethod
	def import_keymat(cls, rest_rot_inv, key_matrix):
		key_matrix = rest_rot_inv @ key_matrix
		return cls.local @ key_matrix @ cls.local_inv

	@classmethod
	def export_keymat(cls, rest_rot, key_matrix):
		key_matrix = cls.local_inv @ key_matrix @ cls.local
		return rest_rot @ key_matrix

	@classmethod
	def get_blender_matrix(cls, bfb_armature_space):
		return cls.local_inv @ cls.local @ bfb_armature_space @ cls.local_inv

	@classmethod
	def get_bfb_matrix(cls, b_bone):
		"""Returns bone space matrix in bfb coordinates"""
		if b_bone.parent:
			bind = b_bone.parent.matrix_local.inverted() @ b_bone.matrix_local
			return cls.local_inv @ bind @ cls.local
		else:
			return b_bone.matrix_local @ cls.local


def center_origin_to_matrix(n_center, n_dir):
	"""Helper for capsules to transform nif data into a local matrix """
	# get the rotation that makes (1,0,0) match m_dir
	m_dir = mathutils.Vector(n_dir).normalized()
	rot = m_dir.to_track_quat("Z", "Y").to_matrix().to_4x4()
	rot.translation = n_center
	return rot

