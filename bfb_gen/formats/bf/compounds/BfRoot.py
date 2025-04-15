from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfRoot(BaseStruct):

	__name__ = 'BfRoot'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.header = name_type_map['BfHeader'](self.context, 0, None)
		self.nodes = Array(self.context, 0, None, (0,), name_type_map['BfNode'])
		self.footer = name_type_map['BfFooter'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'header', name_type_map['BfHeader'], (0, None), (False, None), (None, None)
		yield 'nodes', Array, (0, None, (None,), name_type_map['BfNode']), (False, None), (None, None)
		yield 'footer', name_type_map['BfFooter'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'header', name_type_map['BfHeader'], (0, None), (False, None)
		yield 'nodes', Array, (0, None, (instance.header.num_nodes,), name_type_map['BfNode']), (False, None)
		yield 'footer', name_type_map['BfFooter'], (0, None), (False, None)
