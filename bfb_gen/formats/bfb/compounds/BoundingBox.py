from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BoundingBox(BaseStruct):

	__name__ = 'BoundingBox'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.flag = name_type_map['Ushort'].from_value(256)
		self.matrix = name_type_map['Matrix44'](self.context, 0, None)
		self.extent = name_type_map['Vector3'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'flag', name_type_map['Ushort'], (0, None), (False, 256), (None, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None), (None, None)
		yield 'extent', name_type_map['Vector3'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'flag', name_type_map['Ushort'], (0, None), (False, 256)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None)
		yield 'extent', name_type_map['Vector3'], (0, None), (False, None)
