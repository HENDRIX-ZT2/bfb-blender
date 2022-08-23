import numpy
from generated.array import Array
from generated.base_struct import BaseStruct
from generated.formats.base.basic import Float
from generated.formats.base.basic import Uint
from generated.formats.base.basic import Ushort


class BfHeader(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)

		# 1 for beta, 2 for release
		self.version = 0

		# duration of anim
		self.duration = 0.0

		# Number of nodes in bf
		self.num_nodes = 0

		# unknown
		self.unk = 0

		# unused
		self.reserved = numpy.zeros((29,), dtype=numpy.dtype('uint32'))
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		self.version = 0
		self.duration = 0.0
		self.num_nodes = 0
		self.unk = 0
		if self.context.version <= 1:
			self.reserved = numpy.zeros((29,), dtype=numpy.dtype('uint32'))

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		instance.version = Uint.from_stream(stream, instance.context, 0, None)
		instance.context.version = instance.version
		instance.duration = Float.from_stream(stream, instance.context, 0, None)
		instance.num_nodes = Ushort.from_stream(stream, instance.context, 0, None)
		instance.unk = Ushort.from_stream(stream, instance.context, 0, None)
		if instance.context.version <= 1:
			instance.reserved = Array.from_stream(stream, instance.context, 0, None, (29,), Uint)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		Uint.to_stream(stream, instance.version)
		Float.to_stream(stream, instance.duration)
		Ushort.to_stream(stream, instance.num_nodes)
		Ushort.to_stream(stream, instance.unk)
		if instance.context.version <= 1:
			Array.to_stream(stream, instance.reserved, (29,), Uint, instance.context, 0, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		yield 'version', Uint, (0, None), (False, None)
		yield 'duration', Float, (0, None), (False, None)
		yield 'num_nodes', Ushort, (0, None), (False, None)
		yield 'unk', Ushort, (0, None), (False, None)
		if instance.context.version <= 1:
			yield 'reserved', Array, ((29,), Uint, 0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'BfHeader [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* version = {self.fmt_member(self.version, indent+1)}'
		s += f'\n	* duration = {self.fmt_member(self.duration, indent+1)}'
		s += f'\n	* num_nodes = {self.fmt_member(self.num_nodes, indent+1)}'
		s += f'\n	* unk = {self.fmt_member(self.unk, indent+1)}'
		s += f'\n	* reserved = {self.fmt_member(self.reserved, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
