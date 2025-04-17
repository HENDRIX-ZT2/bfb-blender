import logging
from io import BytesIO

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
		self.childstart = name_type_map['Uint'](self.context, 0, None)
		self.nextblockstart = name_type_map['Uint'](self.context, 0, None)
		self.unk = name_type_map['Ubyte'](self.context, 0, None)
		self.name = name_type_map['FixedString'](self.context, 64, None)
		self.matrix = name_type_map['Matrix44'](self.context, 0, None)
		self.data = name_type_map['CapsuleLink'](self.context, 0, None)
		self.children = Array(self.context, 0, None, (0,), name_type_map['BfbNode'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'id', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'type_id', name_type_map['NodeType'], (0, None), (False, None), (None, None)
		yield 'childstart', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'nextblockstart', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'unk', name_type_map['Ubyte'], (0, None), (False, None), (None, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None), (None, None)
		yield 'data', name_type_map['Node'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['LodGroup'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['MeshLink'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['BillboardLink'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['CapsuleLink'], (0, None), (False, None), (None, True)
		yield 'children', Array, (0, None, (0,), name_type_map['BfbNode']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'id', name_type_map['Uint'], (0, None), (False, None)
		yield 'type_id', name_type_map['NodeType'], (0, None), (False, None)
		yield 'childstart', name_type_map['Uint'], (0, None), (False, None)
		yield 'nextblockstart', name_type_map['Uint'], (0, None), (False, None)
		yield 'unk', name_type_map['Ubyte'], (0, None), (False, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None)
		yield 'matrix', name_type_map['Matrix44'], (0, None), (False, None)
		if instance.type_id == 1:
			yield 'data', name_type_map['Node'], (0, None), (False, None)
		if instance.type_id == 2:
			yield 'data', name_type_map['LodGroup'], (0, None), (False, None)
		if instance.type_id == 3:
			yield 'data', name_type_map['MeshLink'], (0, None), (False, None)
		if instance.type_id == 4:
			yield 'data', name_type_map['BillboardLink'], (0, None), (False, None)
		if instance.type_id == 5:
			yield 'data', name_type_map['CapsuleLink'], (0, None), (False, None)
		if include_abstract:
			yield 'children', Array, (0, None, (0,), name_type_map['BfbNode']), (False, None)


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		if instance.childstart:
			child = BfbNode.from_stream(stream, context, instance)
			instance.children.append(child)
		if instance.nextblockstart:
			assert isinstance(arg, BfbNode)
			sibling = BfbNode.from_stream(stream, context, arg)
			arg.children.append(sibling)
		return instance

	@classmethod
	def write_fields(cls, stream, instance):
		instance.io_start = stream.tell()

