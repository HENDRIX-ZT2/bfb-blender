from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BfbBlock(BaseStruct):

	__name__ = 'BfbBlock'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.id = name_type_map['Uint'](self.context, 0, None)
		self.type_id = name_type_map['Ushort'](self.context, 0, None)
		self.flag = name_type_map['Ushort'].from_value(32768)
		self.end = name_type_map['Uint'](self.context, 0, None)
		self.name = name_type_map['FixedString'](self.context, 64, None)
		self.data = name_type_map['MeshSkinned'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'id', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'type_id', name_type_map['Ushort'], (0, None), (False, None), (None, None)
		yield 'flag', name_type_map['Ushort'], (0, None), (False, 32768), (None, None)
		yield 'end', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None), (None, None)
		yield 'data', name_type_map['Sphere'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['BoundingBox'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['Capsule'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['Mesh'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['MeshData'], (0, None), (False, None), (None, True)
		yield 'data', name_type_map['MeshSkinned'], (0, None), (False, None), (None, True)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'id', name_type_map['Uint'], (0, None), (False, None)
		yield 'type_id', name_type_map['Ushort'], (0, None), (False, None)
		yield 'flag', name_type_map['Ushort'], (0, None), (False, 32768)
		yield 'end', name_type_map['Uint'], (0, None), (False, None)
		yield 'name', name_type_map['FixedString'], (64, None), (False, None)
		if instance.type_id == 1:
			yield 'data', name_type_map['Sphere'], (0, None), (False, None)
		if instance.type_id == 3:
			yield 'data', name_type_map['BoundingBox'], (0, None), (False, None)
		if instance.type_id == 4:
			yield 'data', name_type_map['Capsule'], (0, None), (False, None)
		if instance.type_id == 5:
			yield 'data', name_type_map['Mesh'], (0, None), (False, None)
		if instance.type_id == 6:
			yield 'data', name_type_map['MeshData'], (0, None), (False, None)
		if instance.type_id == 8:
			yield 'data', name_type_map['MeshSkinned'], (0, None), (False, None)
