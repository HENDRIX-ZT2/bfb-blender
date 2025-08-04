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