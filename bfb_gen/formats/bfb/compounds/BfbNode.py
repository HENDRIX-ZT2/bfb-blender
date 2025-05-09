import logging

from bfb_gen.base_struct import BaseStruct


from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BfbNode(BaseStruct):

	__name__ = 'BfbNode'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.id = name_type_map['Uint'](self.context, 0, None)
		self.type_id = name_type_map['NodeType'](self.context, 0, None)
		self.start_children = name_type_map['Uint'](self.context, 0, None)
		self.start_sibling = name_type_map['Uint'](self.context, 0, None)
		self.unk_0 = name_type_map['Ubyte'](self.context, 0, None)
		self.name = name_type_map['FixedString'](self.context, 64, None)
		self.matrix = name_type_map['Matrix44'](self.context, 0, None)
		self.unk_1 = name_type_map['Uint'](self.context, 0, None)
		self.num_children = name_type_map['Uint'](self.context, 0, None)
		self.num_colliders = name_type_map['Uint'](self.context, 0, None)
		self.collision_ids = Array(self.context, 0, None, (0,), name_type_map['Uint'])
		self.lodgroup = name_type_map['FixedString'].from_value('lodgroup')
		self.geometry = name_type_map['BillboardLink'](self.context, 0, None)

		# case-sensitive
		self.bone_name = name_type_map['FixedString'](self.context, 64, None)

		# case-insensitive, in CavePaintingHall
		self.emitter = name_type_map['FixedString'](self.context, 64, None)
		self.children = Array(self.context, 0, None, (0,), name_type_map['BfbNode'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'id', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'type_id', name_type_map['NodeType'], (0, None), (False, None), (None, None)
		yield 'start_children', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'start_sibling', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None), (None, None)
		yield 'unk_1', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_children', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_colliders', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'collision_ids', Array, (0, None, (None,), name_type_map['Uint']), (False, None), (None, None)
		yield 'lodgroup', name_type_map['FixedString'], (64, None), (False, 'lodgroup'), (None, True)
		yield 'geometry', name_type_map['MeshLink'], (0, None), (False, None), (None, True)
		yield 'geometry', name_type_map['BillboardLink'], (0, None), (False, None), (None, True)
		yield 'bone_name', name_type_map['FixedString'], (64, None), (False, None), (None, True)
		yield 'emitter', name_type_map['FixedString'], (64, None), (False, None), (None, True)
		yield 'children', Array, (0, None, (0,), name_type_map['BfbNode']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'id', name_type_map['Uint'], (0, None), (False, None)
		yield 'type_id', name_type_map['NodeType'], (0, None), (False, None)
		yield 'start_children', name_type_map['Uint'], (0, None), (False, None)
		yield 'start_sibling', name_type_map['Uint'], (0, None), (False, None)
		yield 'unk_0', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None)
		yield 'unk_1', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_children', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_colliders', name_type_map['Uint'], (0, None), (False, None)
		yield 'collision_ids', Array, (0, None, (instance.num_colliders,), name_type_map['Uint']), (False, None)
		if instance.type_id == 2:
			yield 'lodgroup', name_type_map['FixedString'], (64, None), (False, 'lodgroup')
		if instance.type_id == 3:
			yield 'geometry', name_type_map['MeshLink'], (0, None), (False, None)
		if instance.type_id == 4:
			yield 'geometry', name_type_map['BillboardLink'], (0, None), (False, None)
		if instance.type_id == 5:
			yield 'bone_name', name_type_map['FixedString'], (64, None), (False, None)
		if instance.type_id == 6:
			yield 'emitter', name_type_map['FixedString'], (64, None), (False, None)
		if include_abstract:
			yield 'children', Array, (0, None, (0,), name_type_map['BfbNode']), (False, None)


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		if instance.start_children:
			child = BfbNode.from_stream(stream, context, instance)
			instance.children.append(child)
		if instance.start_sibling:
			assert isinstance(arg, BfbNode)
			try:
				sibling = BfbNode.from_stream(stream, context, arg)
				arg.children.append(sibling)
			except:
				logging.exception("failed reading sibling")
		return instance

	def get_children(self, children=[]):
		children.extend(self.children)
		for child in self.children:
			child.get_children(children)
		return children

	@classmethod
	def get_size(cls, instance, context, arg=0, template=None, include_children=False):
		"""arguments is optional because it is not required for _get_filtered_attribute_list"""
		size = 0
		for f_name, f_type, arguments, _ in cls._get_filtered_attribute_list(instance, include_abstract=include_children):
			size += f_type.get_size(cls.get_field(instance, f_name), context, *arguments)
		return size

	@classmethod
	def write_fields(cls, stream, instance):
		if instance.children:
			instance.start_children = instance.io_start + instance.get_size(instance, instance.context, include_children=False)
			instance.num_children = len(instance.get_children([]))
		# is there a sibling?
		parent_node = instance.arg
		if parent_node:
			if parent_node.children.index(instance) < len(parent_node.children) - 1:
				instance.start_sibling = instance.io_start + instance.get_size(instance, instance.context, include_children=True)
		instance.end = instance.io_start + instance.get_size(instance, instance.context)
		super().write_fields(stream, instance)
		for child in instance.children:
			child.to_stream(child, stream, child.context)

