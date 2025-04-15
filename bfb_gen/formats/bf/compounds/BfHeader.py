from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfHeader(BaseStruct):

	__name__ = 'BfHeader'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)

		# 1 for beta, 2 for release
		self.version = name_type_map['Uint'](self.context, 0, None)

		# duration of anim
		self.duration = name_type_map['Float'](self.context, 0, None)

		# Number of nodes in bf
		self.num_nodes = name_type_map['Ushort'](self.context, 0, None)
		self.unk = name_type_map['Ushort'].from_value(256)

		# unused
		self.reserved = Array(self.context, 0, None, (0,), name_type_map['Uint'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'version', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'duration', name_type_map['Float'], (0, None), (False, None), (None, None)
		yield 'num_nodes', name_type_map['Ushort'], (0, None), (False, None), (None, None)
		yield 'unk', name_type_map['Ushort'], (0, None), (False, 256), (None, None)
		yield 'reserved', Array, (0, None, (29,), name_type_map['Uint']), (False, None), (lambda context: context.version <= 1, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'version', name_type_map['Uint'], (0, None), (False, None)
		yield 'duration', name_type_map['Float'], (0, None), (False, None)
		yield 'num_nodes', name_type_map['Ushort'], (0, None), (False, None)
		yield 'unk', name_type_map['Ushort'], (0, None), (False, 256)
		if instance.context.version <= 1:
			yield 'reserved', Array, (0, None, (29,), name_type_map['Uint']), (False, None)
