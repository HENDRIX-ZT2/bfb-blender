# START_GLOBALS
import itertools
import logging
import numpy as np

from bfb_gen.base_struct import BaseStruct


# END_GLOBALS


class MeshReader(BaseStruct):

	# START_CLASS


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		instance.get_dtype_from_bfrvertex()
		instance.verts_data = np.empty(dtype=instance.dt, shape=arg.vertex_count)
		stream.readinto(instance.verts_data)
		return instance

	def get_dtype_from_bfrvertex(self, set_vert_size=False):
		# decodes the vertex format on the fly, should work on most if not all models. Some uncertainties about the last two, rare options.
		self.formatstr = self.arg.b_f_r_vertex[9:]
		# logging.info(self.formatstr)
		dt_map = {
			"P": [("pos", np.float32, (3,))],
			"N": [("normal", np.float32, (3,))],
			"D": [("rgba", np.ubyte, (4,))],
			"T0": [("u0", np.float32, (2,))],
			"T1": [("u1", np.float32, (2,))],
			"T2": [("u2", np.float32, (2,))],
			"T30": [("u0", np.float32, (2,)), ("w", np.float32)],
			"T31": [("u1", np.float32, (2,)), ("c", np.float32)],
			"T3D1": [("u3", np.float32, (2,)), ("abcd", np.ubyte, (4,))],
			"T3D2": [("u3", np.float32, (2,)), ("abcd", np.ubyte, (4,))],
			# BFRVertexPNDT0T1T3D2 - CrystalTunnel_df, 56 bytes
		}
		dt = []
		cur = 0
		while cur < len(self.formatstr):
			for k, dt_part in dt_map.items():
				if self.formatstr[cur:].startswith(k):
					cur += len(k)
					dt.extend(dt_part)
					break
			else:
				raise AttributeError(f"Encountered unknown format in {self.formatstr} at {self.formatstr[cur:]}")
		self.dt = np.dtype(dt)
		if set_vert_size:
			self.arg.size_of_vertex = self.dt.itemsize
		else:
			if self.dt.itemsize != self.arg.size_of_vertex:
				raise AttributeError(
					f"Vertex size for {self.arg.b_f_r_vertex} is wrong! Collected {self.dt.itemsize}, expected {self.arg.size_of_vertex} bytes.")

	def set_verts(self, verts):
		self.get_dtype_from_bfrvertex(set_vert_size=True)
		self.verts_data = np.array(verts, self.dt)
		self.verts_data[:] = verts

	@classmethod
	def write_fields(cls, stream, instance):
		stream.write(instance.verts_data.tobytes())

	@classmethod
	def format_indented(cls, instance, indent=0):
		if instance is not None:
			# return instance.get_info_str(indent) + instance.get_fields_str(instance, indent)
			return str(instance.verts_data)
		return "NONE"
