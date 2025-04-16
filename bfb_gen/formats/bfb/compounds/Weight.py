from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Weight(BaseStruct):

	__name__ = 'Weight'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.b_0 = name_type_map['Ubyte'](self.context, 0, None)
		self.b_1 = name_type_map['Ubyte'](self.context, 0, None)
		self.b_2 = name_type_map['Ubyte'](self.context, 0, None)
		self.b_3 = name_type_map['Ubyte'](self.context, 0, None)
		self.w_0 = name_type_map['Float'](self.context, 0, None)
		self.w_1 = name_type_map['Float'](self.context, 0, None)
		self.w_2 = name_type_map['Float'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'b_0', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'b_1', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'b_2', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'b_3', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'w_0', name_type_map['Float'], (0, None), (False, None), (None, None)
		yield 'w_1', name_type_map['Float'], (0, None), (False, None), (None, None)
		yield 'w_2', name_type_map['Float'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'b_0', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'b_1', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'b_2', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'b_3', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'w_0', name_type_map['Float'], (0, None), (False, None)
		yield 'w_1', name_type_map['Float'], (0, None), (False, None)
		yield 'w_2', name_type_map['Float'], (0, None), (False, None)
