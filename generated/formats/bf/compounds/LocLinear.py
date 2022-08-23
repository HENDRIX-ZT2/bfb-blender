from generated.base_struct import BaseStruct
from generated.formats.base.basic import Float
from generated.formats.bf.basic import Short1000
from generated.formats.bf.basic import Ushort1000


class LocLinear(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.time = 0.0
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		self.time = 0.0
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		if self.context.version <= 1:
			self.time = 0.0
			self.x = 0.0
			self.y = 0.0
			self.z = 0.0
		if self.context.version >= 2:
			self.time = 0.0
			self.x = 0.0
			self.y = 0.0
			self.z = 0.0

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		if instance.context.version <= 1:
			instance.time = Float.from_stream(stream, instance.context, 0, None)
			instance.x = Float.from_stream(stream, instance.context, 0, None)
			instance.y = Float.from_stream(stream, instance.context, 0, None)
			instance.z = Float.from_stream(stream, instance.context, 0, None)
		if instance.context.version >= 2:
			instance.time = Ushort1000.from_stream(stream, instance.context, 0, None)
			instance.x = Short1000.from_stream(stream, instance.context, 0, None)
			instance.y = Short1000.from_stream(stream, instance.context, 0, None)
			instance.z = Short1000.from_stream(stream, instance.context, 0, None)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		if instance.context.version <= 1:
			Float.to_stream(stream, instance.time)
			Float.to_stream(stream, instance.x)
			Float.to_stream(stream, instance.y)
			Float.to_stream(stream, instance.z)
		if instance.context.version >= 2:
			Ushort1000.to_stream(stream, instance.time)
			Short1000.to_stream(stream, instance.x)
			Short1000.to_stream(stream, instance.y)
			Short1000.to_stream(stream, instance.z)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		if instance.context.version <= 1:
			yield 'time', Float, (0, None), (False, None)
			yield 'x', Float, (0, None), (False, None)
			yield 'y', Float, (0, None), (False, None)
			yield 'z', Float, (0, None), (False, None)
		if instance.context.version >= 2:
			yield 'time', Ushort1000, (0, None), (False, None)
			yield 'x', Short1000, (0, None), (False, None)
			yield 'y', Short1000, (0, None), (False, None)
			yield 'z', Short1000, (0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'LocLinear [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* time = {self.fmt_member(self.time, indent+1)}'
		s += f'\n	* x = {self.fmt_member(self.x, indent+1)}'
		s += f'\n	* y = {self.fmt_member(self.y, indent+1)}'
		s += f'\n	* z = {self.fmt_member(self.z, indent+1)}'
		s += f'\n	* time = {self.fmt_member(self.time, indent+1)}'
		s += f'\n	* x = {self.fmt_member(self.x, indent+1)}'
		s += f'\n	* y = {self.fmt_member(self.y, indent+1)}'
		s += f'\n	* z = {self.fmt_member(self.z, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
