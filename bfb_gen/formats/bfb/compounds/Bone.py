from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Bone(BaseStruct):

	__name__ = 'Bone'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.id = name_type_map['Ubyte'](self.context, 0, None)
		self.parent_id = name_type_map['Ubyte'](self.context, 0, None)
		self.priority = name_type_map['Byte'].from_value(-1)
		self.name = name_type_map['FixedString'](self.context, 64, None)
		self.matrix = name_type_map['Matrix44'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'id', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'parent_id', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'priority', name_type_map['Byte'], (0, None), (False, -1), (None, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'id', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'parent_id', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'priority', name_type_map['Byte'], (0, None), (False, -1)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None)
