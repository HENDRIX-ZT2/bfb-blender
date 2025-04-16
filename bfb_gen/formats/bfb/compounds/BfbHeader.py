from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BfbHeader(BaseStruct):

	__name__ = 'BfbHeader'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.magic = name_type_map['FixedString'].from_value('BFB!*000')
		self.version = name_type_map['Uint64'].from_value(4295098369)
		self.author = name_type_map['FixedString'](self.context, 64, None)
		self.num_blocks = name_type_map['Uint'](self.context, 0, None)
		self.num_blocks_2 = name_type_map['Uint'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'magic', name_type_map['FixedString'], (8, None), (False, 'BFB!*000'), (None, None)
		yield 'version', name_type_map['Uint64'], (0, None), (False, 4295098369), (None, None)
		yield 'author', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'num_blocks', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_blocks_2', name_type_map['Uint'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'magic', name_type_map['FixedString'], (8, None), (False, 'BFB!*000')
		yield 'version', name_type_map['Uint64'], (0, None), (False, 4295098369)
		yield 'author', name_type_map['FixedString'], (64, None), (False, None)
		yield 'num_blocks', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_blocks_2', name_type_map['Uint'], (0, None), (False, None)
