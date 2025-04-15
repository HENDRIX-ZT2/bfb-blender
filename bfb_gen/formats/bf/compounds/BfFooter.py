from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfFooter(BaseStruct):

	__name__ = 'BfFooter'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.start_time = name_type_map['Float'](self.context, 0, None)
		self.start = name_type_map['SizedString'].from_value('start')
		self.end_time = name_type_map['Float'](self.context, 0, None)
		self.end = name_type_map['SizedString'].from_value('end')
		self.unused = Array(self.context, 0, None, (0,), name_type_map['Ubyte'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'start_time', name_type_map['Float'], (0, None), (False, None), (None, None)
		yield 'start', name_type_map['SizedString'], (0, None), (False, 'start'), (None, None)
		yield 'end_time', name_type_map['Float'], (0, None), (False, None), (None, None)
		yield 'end', name_type_map['SizedString'], (0, None), (False, 'end'), (None, None)
		yield 'unused', Array, (0, None, (7,), name_type_map['Ubyte']), (False, 0), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'start_time', name_type_map['Float'], (0, None), (False, None)
		yield 'start', name_type_map['SizedString'], (0, None), (False, 'start')
		yield 'end_time', name_type_map['Float'], (0, None), (False, None)
		yield 'end', name_type_map['SizedString'], (0, None), (False, 'end')
		yield 'unused', Array, (0, None, (7,), name_type_map['Ubyte']), (False, 0)
