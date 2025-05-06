from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Node(BaseStruct):

	__name__ = 'Node'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.unk_0 = name_type_map['Uint'](self.context, 0, None)
		self.unk_1 = name_type_map['Uint'](self.context, 0, None)
		self.num_colliders = name_type_map['Uint'](self.context, 0, None)
		self.collision_ids = Array(self.context, 0, None, (0,), name_type_map['Uint'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'unk_0', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'unk_1', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_colliders', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'collision_ids', Array, (0, None, (None,), name_type_map['Uint']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'unk_0', name_type_map['Uint'], (0, None), (False, None)
		yield 'unk_1', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_colliders', name_type_map['Uint'], (0, None), (False, None)
		yield 'collision_ids', Array, (0, None, (instance.num_colliders,), name_type_map['Uint']), (False, None)
