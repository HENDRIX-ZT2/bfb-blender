from generated.base_struct import BaseStruct
from generated.formats.base.basic import Float
from generated.formats.bf.basic import Ubyte50
from generated.formats.bf.basic import Ushort1000


class ScaleLinear(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.time = 0.0
		self.scale = 0.0
		self.time = 0.0
		self.scale = 0.0
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		if self.context.version <= 1:
			self.time = 0.0
			self.scale = 0.0
		if self.context.version >= 2:
			self.time = 0.0
			self.scale = 0.0

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		if instance.context.version <= 1:
			instance.time = Float.from_stream(stream, instance.context, 0, None)
			instance.scale = Float.from_stream(stream, instance.context, 0, None)
		if instance.context.version >= 2:
			instance.time = Ushort1000.from_stream(stream, instance.context, 0, None)
			instance.scale = Ubyte50.from_stream(stream, instance.context, 0, None)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		if instance.context.version <= 1:
			Float.to_stream(stream, instance.time)
			Float.to_stream(stream, instance.scale)
		if instance.context.version >= 2:
			Ushort1000.to_stream(stream, instance.time)
			Ubyte50.to_stream(stream, instance.scale)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		if instance.context.version <= 1:
			yield 'time', Float, (0, None), (False, None)
			yield 'scale', Float, (0, None), (False, None)
		if instance.context.version >= 2:
			yield 'time', Ushort1000, (0, None), (False, None)
			yield 'scale', Ubyte50, (0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'ScaleLinear [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* time = {self.fmt_member(self.time, indent+1)}'
		s += f'\n	* scale = {self.fmt_member(self.scale, indent+1)}'
		s += f'\n	* time = {self.fmt_member(self.time, indent+1)}'
		s += f'\n	* scale = {self.fmt_member(self.scale, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
