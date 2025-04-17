from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class MeshData(BaseStruct):

	__name__ = 'MeshData'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.flag = name_type_map['Ubyte'].from_value(8)
		self.b_f_r_vertex = name_type_map['FixedString'](self.context, 64, None)
		self.size_of_vertex = name_type_map['Uint'](self.context, 0, None)
		self.vertex_count = name_type_map['Uint'](self.context, 0, None)
		self.verts = name_type_map['MeshReader'](self.context, self, None)
		self.u_cha = name_type_map['Byte'].from_value(2)
		self.t_num = name_type_map['Uint'](self.context, 0, None)
		self.tris = Array(self.context, 0, None, (0,), name_type_map['Ushort'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 8), (None, None)
		yield 'b_f_r_vertex', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'size_of_vertex', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'vertex_count', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'verts', name_type_map['MeshReader'], (None, None), (False, None), (None, None)
		yield 'u_cha', name_type_map['Byte'], (0, None), (False, 2), (None, None)
		yield 't_num', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'tris', Array, (0, None, (None,), name_type_map['Ushort']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 8)
		yield 'b_f_r_vertex', name_type_map['FixedString'], (64, None), (False, None)
		yield 'size_of_vertex', name_type_map['Uint'], (0, None), (False, None)
		yield 'vertex_count', name_type_map['Uint'], (0, None), (False, None)
		yield 'verts', name_type_map['MeshReader'], (instance, None), (False, None)
		yield 'u_cha', name_type_map['Byte'], (0, None), (False, 2)
		yield 't_num', name_type_map['Uint'], (0, None), (False, None)
		yield 'tris', Array, (0, None, (instance.t_num,), name_type_map['Ushort']), (False, None)
