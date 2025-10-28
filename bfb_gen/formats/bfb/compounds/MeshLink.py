from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class MeshLink(BaseStruct):

	__name__ = 'MeshLink'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.num_objects = name_type_map['Uint'].from_value(1)
		self.object_ids = Array(self.context, 0, None, (0,), name_type_map['Uint'])
		self.num_materials = name_type_map['Uint'].from_value(1)
		self.materials = Array(self.context, 128, None, (0,), name_type_map['FixedString'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'num_objects', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'object_ids', Array, (0, None, (None,), name_type_map['Uint']), (False, None), (None, None)
		yield 'num_materials', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'materials', Array, (128, None, (None,), name_type_map['FixedString']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'num_objects', name_type_map['Uint'], (0, None), (False, 1)
		yield 'object_ids', Array, (0, None, (instance.num_objects,), name_type_map['Uint']), (False, None)
		yield 'num_materials', name_type_map['Uint'], (0, None), (False, 1)
		yield 'materials', Array, (128, None, (instance.num_materials,), name_type_map['FixedString']), (False, None)
