from generated.base_struct import BaseStruct
from generated.formats.base.basic import Float
from generated.formats.base.basic import Ushort
from generated.formats.ovl_base.compounds.FixedString import FixedString


class BfFooter(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.start_time = 0.0

		# 6
		self.unk_0 = 0

		# start
		self.start = FixedString(self.context, 6, None)
		self.end_time = 0.0

		# 6
		self.unk_1 = 0

		# end
		self.end = FixedString(self.context, 12, None)
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		self.start_time = 0.0
		self.unk_0 = 0
		self.start = FixedString(self.context, 6, None)
		self.end_time = 0.0
		self.unk_1 = 0
		self.end = FixedString(self.context, 12, None)

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		instance.start_time = Float.from_stream(stream, instance.context, 0, None)
		instance.unk_0 = Ushort.from_stream(stream, instance.context, 0, None)
		instance.start = FixedString.from_stream(stream, instance.context, 6, None)
		instance.end_time = Float.from_stream(stream, instance.context, 0, None)
		instance.unk_1 = Ushort.from_stream(stream, instance.context, 0, None)
		instance.end = FixedString.from_stream(stream, instance.context, 12, None)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		Float.to_stream(stream, instance.start_time)
		Ushort.to_stream(stream, instance.unk_0)
		FixedString.to_stream(stream, instance.start)
		Float.to_stream(stream, instance.end_time)
		Ushort.to_stream(stream, instance.unk_1)
		FixedString.to_stream(stream, instance.end)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		yield 'start_time', Float, (0, None), (False, None)
		yield 'unk_0', Ushort, (0, None), (False, None)
		yield 'start', FixedString, (6, None), (False, None)
		yield 'end_time', Float, (0, None), (False, None)
		yield 'unk_1', Ushort, (0, None), (False, None)
		yield 'end', FixedString, (12, None), (False, None)

	def get_info_str(self, indent=0):
		return f'BfFooter [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* start_time = {self.fmt_member(self.start_time, indent+1)}'
		s += f'\n	* unk_0 = {self.fmt_member(self.unk_0, indent+1)}'
		s += f'\n	* start = {self.fmt_member(self.start, indent+1)}'
		s += f'\n	* end_time = {self.fmt_member(self.end_time, indent+1)}'
		s += f'\n	* unk_1 = {self.fmt_member(self.unk_1, indent+1)}'
		s += f'\n	* end = {self.fmt_member(self.end, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
