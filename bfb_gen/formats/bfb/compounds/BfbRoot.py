from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BfbRoot(BaseStruct):

	__name__ = 'BfbRoot'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.header = name_type_map['BfbHeader'](self.context, 0, None)
		self.blocks = Array(self.context, 0, None, (0,), name_type_map['BfbBlock'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'header', name_type_map['BfbHeader'], (0, None), (False, None), (None, None)
		yield 'blocks', Array, (0, None, (None,), name_type_map['BfbBlock']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'header', name_type_map['BfbHeader'], (0, None), (False, None)
		yield 'blocks', Array, (0, None, (instance.header.num_blocks,), name_type_map['BfbBlock']), (False, None)
