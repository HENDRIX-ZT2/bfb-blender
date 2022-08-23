import numpy
from generated.array import Array
from generated.base_struct import BaseStruct
from generated.formats.base.basic import Ubyte
from generated.formats.base.basic import Uint
from generated.formats.base.basic import Uint64
from generated.formats.base.basic import Ushort
from generated.formats.bf.compounds.BfModifier import BfModifier
from generated.formats.ovl_base.compounds.FixedString import FixedString


class BfNode(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)

		# start
		self.name = FixedString(self.context, 32, None)
		self.num_mod_types = 0
		self.unk_0 = 204
		self.unk_1 = 204
		self.size = 0

		# unused
		self.reserved = numpy.zeros((5,), dtype=numpy.dtype('uint64'))
		self.zero = 0
		self.unk_2 = 204
		self.unk_3 = 204
		self.modifiers = Array((self.num_mod_types,), BfModifier, self.context, 0, None)
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		self.name = FixedString(self.context, 32, None)
		self.num_mod_types = 0
		self.unk_0 = 204
		self.unk_1 = 204
		self.size = 0
		if self.context.version <= 1:
			self.reserved = numpy.zeros((5,), dtype=numpy.dtype('uint64'))
		self.zero = 0
		self.unk_2 = 204
		self.unk_3 = 204
		self.modifiers = Array((self.num_mod_types,), BfModifier, self.context, 0, None)

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		instance.name = FixedString.from_stream(stream, instance.context, 32, None)
		instance.num_mod_types = Ushort.from_stream(stream, instance.context, 0, None)
		instance.unk_0 = Ubyte.from_stream(stream, instance.context, 0, None)
		instance.unk_1 = Ubyte.from_stream(stream, instance.context, 0, None)
		instance.size = Uint.from_stream(stream, instance.context, 0, None)
		if instance.context.version <= 1:
			instance.reserved = Array.from_stream(stream, instance.context, 0, None, (5,), Uint64)
		instance.zero = Ushort.from_stream(stream, instance.context, 0, None)
		instance.unk_2 = Ubyte.from_stream(stream, instance.context, 0, None)
		instance.unk_3 = Ubyte.from_stream(stream, instance.context, 0, None)
		instance.modifiers = Array.from_stream(stream, instance.context, 0, None, (instance.num_mod_types,), BfModifier)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		FixedString.to_stream(stream, instance.name)
		Ushort.to_stream(stream, instance.num_mod_types)
		Ubyte.to_stream(stream, instance.unk_0)
		Ubyte.to_stream(stream, instance.unk_1)
		Uint.to_stream(stream, instance.size)
		if instance.context.version <= 1:
			Array.to_stream(stream, instance.reserved, (5,), Uint64, instance.context, 0, None)
		Ushort.to_stream(stream, instance.zero)
		Ubyte.to_stream(stream, instance.unk_2)
		Ubyte.to_stream(stream, instance.unk_3)
		Array.to_stream(stream, instance.modifiers, (instance.num_mod_types,), BfModifier, instance.context, 0, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		yield 'name', FixedString, (32, None), (False, None)
		yield 'num_mod_types', Ushort, (0, None), (False, None)
		yield 'unk_0', Ubyte, (0, None), (False, 204)
		yield 'unk_1', Ubyte, (0, None), (False, 204)
		yield 'size', Uint, (0, None), (False, None)
		if instance.context.version <= 1:
			yield 'reserved', Array, ((5,), Uint64, 0, None), (False, None)
		yield 'zero', Ushort, (0, None), (False, None)
		yield 'unk_2', Ubyte, (0, None), (False, 204)
		yield 'unk_3', Ubyte, (0, None), (False, 204)
		yield 'modifiers', Array, ((instance.num_mod_types,), BfModifier, 0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'BfNode [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* name = {self.fmt_member(self.name, indent+1)}'
		s += f'\n	* num_mod_types = {self.fmt_member(self.num_mod_types, indent+1)}'
		s += f'\n	* unk_0 = {self.fmt_member(self.unk_0, indent+1)}'
		s += f'\n	* unk_1 = {self.fmt_member(self.unk_1, indent+1)}'
		s += f'\n	* size = {self.fmt_member(self.size, indent+1)}'
		s += f'\n	* reserved = {self.fmt_member(self.reserved, indent+1)}'
		s += f'\n	* zero = {self.fmt_member(self.zero, indent+1)}'
		s += f'\n	* unk_2 = {self.fmt_member(self.unk_2, indent+1)}'
		s += f'\n	* unk_3 = {self.fmt_member(self.unk_3, indent+1)}'
		s += f'\n	* modifiers = {self.fmt_member(self.modifiers, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
