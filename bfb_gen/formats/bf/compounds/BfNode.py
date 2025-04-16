from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfNode(BaseStruct):

	__name__ = 'BfNode'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.name = name_type_map['FixedString'](self.context, 32, None)
		self.num_mod_types = name_type_map['Ushort'](self.context, 0, None)
		self.unk_0 = name_type_map['Ubyte'].from_value(204)
		self.unk_1 = name_type_map['Ubyte'].from_value(204)

		# 44 + len(key_bytes)
		self.num_bytes = name_type_map['Uint'](self.context, 0, None)

		# unused
		self.reserved = Array(self.context, 0, None, (0,), name_type_map['Uint64'])
		self.zero = name_type_map['Ushort'](self.context, 0, None)
		self.unk_2 = name_type_map['Ubyte'].from_value(204)
		self.unk_3 = name_type_map['Ubyte'].from_value(204)
		self.modifiers = Array(self.context, 0, None, (0,), name_type_map['BfModifier'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'name', name_type_map['FixedString'], (32, None), (False, None), (None, None)
		yield 'num_mod_types', name_type_map['Ushort'], (0, None), (False, None), (None, None)
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, 204), (None, None)
		yield 'unk_1', name_type_map['Ubyte'], (0, None), (False, 204), (None, None)
		yield 'num_bytes', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'reserved', Array, (0, None, (5,), name_type_map['Uint64']), (False, None), (lambda context: context.version <= 1, None)
		yield 'zero', name_type_map['Ushort'], (0, None), (False, None), (None, None)
		yield 'unk_2', name_type_map['Ubyte'], (0, None), (False, 204), (None, None)
		yield 'unk_3', name_type_map['Ubyte'], (0, None), (False, 204), (None, None)
		yield 'modifiers', Array, (0, None, (None,), name_type_map['BfModifier']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'name', name_type_map['FixedString'], (32, None), (False, None)
		yield 'num_mod_types', name_type_map['Ushort'], (0, None), (False, None)
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, 204)
		yield 'unk_1', name_type_map['Ubyte'], (0, None), (False, 204)
		yield 'num_bytes', name_type_map['Uint'], (0, None), (False, None)
		if instance.context.version <= 1:
			yield 'reserved', Array, (0, None, (5,), name_type_map['Uint64']), (False, None)
		yield 'zero', name_type_map['Ushort'], (0, None), (False, None)
		yield 'unk_2', name_type_map['Ubyte'], (0, None), (False, 204)
		yield 'unk_3', name_type_map['Ubyte'], (0, None), (False, 204)
		yield 'modifiers', Array, (0, None, (instance.num_mod_types,), name_type_map['BfModifier']), (False, None)
