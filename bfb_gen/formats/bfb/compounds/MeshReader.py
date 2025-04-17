import logging
import numpy as np

from bfb_gen.base_struct import BaseStruct


from bfb_gen.base_struct import BaseStruct


class MeshReader(BaseStruct):

	__name__ = 'MeshReader'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		# This decodes the vertex format on the fly, should work on most if not all models. Some uncertainties about the last two, rare options.
		instance.formatstr = arg.b_f_r_vertex[9:]
		dt_map = {
			"P": [("pos", np.float32, (3,))],
			"N": [("normal", np.float32, (3,))],
			"D": [("rgba", np.ubyte, (4,))],
			"T0": [("uv0", np.float32, (2,))],
			"T1": [("uv1", np.float32, (2,))],
			"T2": [("uv2", np.float32, (2,))],
			"T30": [("uv0", np.float32, (2,)), ("w", np.float32)],
			"T31": [("uv1", np.float32, (2,)), ("c", np.float32)],
			"T3D1": [("uv3", np.float32, (2,)), ("abcd", np.ubyte, (4,))],
		}
		dt = []
		cur = 0
		while cur < len(instance.formatstr):
			for k, dt_part in dt_map.items():
				if instance.formatstr[cur:].startswith(k):
					cur += len(k)
					dt.extend(dt_part)

		instance.dt = np.dtype(dt)
		if instance.dt.itemsize != arg.size_of_vertex:
			raise AttributeError(
				f"Vertex size for {arg.b_f_r_vertex} is wrong! Collected {instance.dt.itemsize}, expected {arg.size_of_vertex} bytes.")

		instance.verts_data = np.empty(dtype=instance.dt, shape=arg.vertex_count)
		stream.readinto(instance.verts_data)
		return instance

	@classmethod
	def write_fields(cls, stream, instance):
		stream.write(instance.verts_data.tobytes())

	@classmethod
	def format_indented(cls, instance, indent=0):
		if instance is not None:
			# return instance.get_info_str(indent) + instance.get_fields_str(instance, indent)
			return str(instance.verts_data)
		return "NONE"
