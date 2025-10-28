from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Capsule(BaseStruct):

	__name__ = 'Capsule'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.unk_0 = name_type_map['Ubyte'].from_value(0)
		self.unk_1 = name_type_map['Ubyte'].from_value(8)
		self.start = name_type_map['Vector3'](self.context, 0, None)
		self.end = name_type_map['Vector3'](self.context, 0, None)
		self.radius = name_type_map['Float'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, 0), (None, None)
		yield 'unk_1', name_type_map['Ubyte'], (0, None), (False, 8), (None, None)
		yield 'start', name_type_map['Vector3'], (0, None), (False, None), (None, None)
		yield 'end', name_type_map['Vector3'], (0, None), (False, None), (None, None)
		yield 'radius', name_type_map['Float'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, 0)
		yield 'unk_1', name_type_map['Ubyte'], (0, None), (False, 8)
		yield 'start', name_type_map['Vector3'], (0, None), (False, None)
		yield 'end', name_type_map['Vector3'], (0, None), (False, None)
		yield 'radius', name_type_map['Float'], (0, None), (False, None)
