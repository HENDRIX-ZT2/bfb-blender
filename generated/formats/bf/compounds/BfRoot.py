from generated.array import Array
from generated.base_struct import BaseStruct
from generated.formats.bf.compounds.BfFooter import BfFooter
from generated.formats.bf.compounds.BfHeader import BfHeader
from generated.formats.bf.compounds.BfNode import BfNode


class BfRoot(BaseStruct):

	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.header = BfHeader(self.context, 0, None)
		self.nodes = Array((self.header.num_nodes,), BfNode, self.context, 0, None)
		self.footer = BfFooter(self.context, 0, None)
		if set_default:
			self.set_defaults()

	def set_defaults(self):
		super().set_defaults()
		self.header = BfHeader(self.context, 0, None)
		self.nodes = Array((self.header.num_nodes,), BfNode, self.context, 0, None)
		self.footer = BfFooter(self.context, 0, None)

	@classmethod
	def read_fields(cls, stream, instance):
		super().read_fields(stream, instance)
		instance.header = BfHeader.from_stream(stream, instance.context, 0, None)
		instance.nodes = Array.from_stream(stream, instance.context, 0, None, (instance.header.num_nodes,), BfNode)
		instance.footer = BfFooter.from_stream(stream, instance.context, 0, None)

	@classmethod
	def write_fields(cls, stream, instance):
		super().write_fields(stream, instance)
		BfHeader.to_stream(stream, instance.header)
		Array.to_stream(stream, instance.nodes, (instance.header.num_nodes,), BfNode, instance.context, 0, None)
		BfFooter.to_stream(stream, instance.footer)

	@classmethod
	def _get_filtered_attribute_list(cls, instance):
		yield from super()._get_filtered_attribute_list(instance)
		yield 'header', BfHeader, (0, None), (False, None)
		yield 'nodes', Array, ((instance.header.num_nodes,), BfNode, 0, None), (False, None)
		yield 'footer', BfFooter, (0, None), (False, None)

	def get_info_str(self, indent=0):
		return f'BfRoot [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self, indent=0):
		s = ''
		s += super().get_fields_str()
		s += f'\n	* header = {self.fmt_member(self.header, indent+1)}'
		s += f'\n	* nodes = {self.fmt_member(self.nodes, indent+1)}'
		s += f'\n	* footer = {self.fmt_member(self.footer, indent+1)}'
		return s

	def __repr__(self, indent=0):
		s = self.get_info_str(indent)
		s += self.get_fields_str(indent)
		s += '\n'
		return s
