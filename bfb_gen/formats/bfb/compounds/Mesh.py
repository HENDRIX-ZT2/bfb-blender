from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Mesh(BaseStruct):

	"""
	v 1: name may be junk bytes
	"""

	__name__ = 'Mesh'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)

		# 2 for lod0 when lods are used (meshdata flag: 10)
		# otherwise:
		# 0 (meshdata flag: 8)
		self.flag = name_type_map['Ubyte'].from_value(0)
		self.data_id = name_type_map['Uint'](self.context, 0, None)
		self.num_chunks = name_type_map['Uint'].from_value(1)
		self.chunks = Array(self.context, 0, None, (0,), name_type_map['Chunk'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 0), (None, None)
		yield 'data_id', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_chunks', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'chunks', Array, (0, None, (None,), name_type_map['Chunk']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 0)
		yield 'data_id', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_chunks', name_type_map['Uint'], (0, None), (False, 1)
		yield 'chunks', Array, (0, None, (instance.num_chunks,), name_type_map['Chunk']), (False, None)
