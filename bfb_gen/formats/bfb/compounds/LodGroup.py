from bfb_gen.formats.bfb.compounds.Node import Node
from bfb_gen.formats.bfb.imports import name_type_map


class LodGroup(Node):

	__name__ = 'LodGroup'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.lodgroup = name_type_map['FixedString'].from_value('lodgroup')
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'lodgroup', name_type_map['FixedString'], (64, None), (False, 'lodgroup'), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'lodgroup', name_type_map['FixedString'], (64, None), (False, 'lodgroup')
