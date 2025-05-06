from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Chunk(BaseStruct):

	__name__ = 'Chunk'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.tri_index_offset = name_type_map['Uint'](self.context, 0, None)
		self.num_tri_indices = name_type_map['Uint'](self.context, 0, None)
		self.vertex_offset = name_type_map['Uint'](self.context, 0, None)
		self.vertex_count = name_type_map['Uint'](self.context, 0, None)
		self.num_tris = name_type_map['Uint'](self.context, 0, None)
		self.bounds_extent = name_type_map['Vector3'](self.context, 0, None)
		self.bounds_radius = name_type_map['Float'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'tri_index_offset', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_tri_indices', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'vertex_offset', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'vertex_count', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_tris', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'bounds_extent', name_type_map['Vector3'], (0, None), (False, None), (None, None)
		yield 'bounds_radius', name_type_map['Float'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'tri_index_offset', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_tri_indices', name_type_map['Uint'], (0, None), (False, None)
		yield 'vertex_offset', name_type_map['Uint'], (0, None), (False, None)
		yield 'vertex_count', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_tris', name_type_map['Uint'], (0, None), (False, None)
		yield 'bounds_extent', name_type_map['Vector3'], (0, None), (False, None)
		yield 'bounds_radius', name_type_map['Float'], (0, None), (False, None)
