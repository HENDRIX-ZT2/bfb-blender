from generated.array import Array
from generated.base_struct import BaseStruct
from generated.formats.base.basic import Short
from generated.formats.base.basic import Uint
from generated.formats.bf.compounds.EulerQuadratic import EulerQuadratic
from generated.formats.bf.compounds.LocLinear import LocLinear
from generated.formats.bf.compounds.LocQuadratic import LocQuadratic
from generated.formats.bf.compounds.QuaternionLinear import QuaternionLinear
from generated.formats.bf.compounds.QuaternionQuadratic import QuaternionQuadratic
from generated.formats.bf.compounds.ScaleLinear import ScaleLinear
from generated.formats.bf.compounds.ScaleQuadratic import ScaleQuadratic
from generated.formats.bf.enums.KeyType import KeyType


class BfModifier(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.key_type = KeyType(self.context, 0, None)
		self.num_keys = 0
		self.num_bytes = 0
		self.keys = Array((self.num_keys,), ScaleLinear, self.context, 0, None)
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		self.key_type = KeyType(self.context, 0, None)
		self.num_keys = 0
		self.num_bytes = 0
		if self.key_type == 1:
			self.keys = Array((self.num_keys,), LocQuadratic, self.context, 0, None)
		if self.key_type == 2:
			self.keys = Array((self.num_keys,), LocLinear, self.context, 0, None)
		if self.key_type == 6:
			self.keys = Array((self.num_keys,), EulerQuadratic, self.context, 0, None)
		if self.key_type == 7:
			self.keys = Array((self.num_keys,), EulerQuadratic, self.context, 0, None)
		if self.key_type == 8:
			self.keys = Array((self.num_keys,), EulerQuadratic, self.context, 0, None)
		if self.key_type == 12:
			self.keys = Array((self.num_keys,), QuaternionQuadratic, self.context, 0, None)
		if self.key_type == 14:
			self.keys = Array((self.num_keys,), QuaternionLinear, self.context, 0, None)
		if self.key_type == 16:
			self.keys = Array((self.num_keys,), ScaleQuadratic, self.context, 0, None)
		if self.key_type == 17:
			self.keys = Array((self.num_keys,), ScaleLinear, self.context, 0, None)

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		instance.key_type = KeyType.from_stream(stream, instance.context, 0, None)
		instance.num_keys = Short.from_stream(stream, instance.context, 0, None)
		instance.num_bytes = Uint.from_stream(stream, instance.context, 0, None)
		if instance.key_type == 1:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), LocQuadratic)
		if instance.key_type == 2:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), LocLinear)
		if instance.key_type == 6:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), EulerQuadratic)
		if instance.key_type == 7:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), EulerQuadratic)
		if instance.key_type == 8:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), EulerQuadratic)
		if instance.key_type == 12:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), QuaternionQuadratic)
		if instance.key_type == 14:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), QuaternionLinear)
		if instance.key_type == 16:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), ScaleQuadratic)
		if instance.key_type == 17:
			instance.keys = Array.from_stream(stream, instance.context, 0, None, (instance.num_keys,), ScaleLinear)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		KeyType.to_stream(stream, instance.key_type)
		Short.to_stream(stream, instance.num_keys)
		Uint.to_stream(stream, instance.num_bytes)
		if instance.key_type == 1:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), LocQuadratic, instance.context, 0, None)
		if instance.key_type == 2:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), LocLinear, instance.context, 0, None)
		if instance.key_type == 6:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), EulerQuadratic, instance.context, 0, None)
		if instance.key_type == 7:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), EulerQuadratic, instance.context, 0, None)
		if instance.key_type == 8:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), EulerQuadratic, instance.context, 0, None)
		if instance.key_type == 12:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), QuaternionQuadratic, instance.context, 0, None)
		if instance.key_type == 14:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), QuaternionLinear, instance.context, 0, None)
		if instance.key_type == 16:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), ScaleQuadratic, instance.context, 0, None)
		if instance.key_type == 17:
			Array.to_stream(stream, instance.keys, (instance.num_keys,), ScaleLinear, instance.context, 0, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		yield 'key_type', KeyType, (0, None), (False, None)
		yield 'num_keys', Short, (0, None), (False, None)
		yield 'num_bytes', Uint, (0, None), (False, None)
		if instance.key_type == 1:
			yield 'keys', Array, ((instance.num_keys,), LocQuadratic, 0, None), (False, None)
		if instance.key_type == 2:
			yield 'keys', Array, ((instance.num_keys,), LocLinear, 0, None), (False, None)
		if instance.key_type == 6:
			yield 'keys', Array, ((instance.num_keys,), EulerQuadratic, 0, None), (False, None)
		if instance.key_type == 7:
			yield 'keys', Array, ((instance.num_keys,), EulerQuadratic, 0, None), (False, None)
		if instance.key_type == 8:
			yield 'keys', Array, ((instance.num_keys,), EulerQuadratic, 0, None), (False, None)
		if instance.key_type == 12:
			yield 'keys', Array, ((instance.num_keys,), QuaternionQuadratic, 0, None), (False, None)
		if instance.key_type == 14:
			yield 'keys', Array, ((instance.num_keys,), QuaternionLinear, 0, None), (False, None)
		if instance.key_type == 16:
			yield 'keys', Array, ((instance.num_keys,), ScaleQuadratic, 0, None), (False, None)
		if instance.key_type == 17:
			yield 'keys', Array, ((instance.num_keys,), ScaleLinear, 0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'BfModifier [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* key_type = {self.fmt_member(self.key_type, indent+1)}'
		s += f'\n	* num_keys = {self.fmt_member(self.num_keys, indent+1)}'
		s += f'\n	* num_bytes = {self.fmt_member(self.num_bytes, indent+1)}'
		s += f'\n	* keys = {self.fmt_member(self.keys, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
