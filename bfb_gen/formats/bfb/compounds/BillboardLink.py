from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class BillboardLink(BaseStruct):

	"""
	164 bytes in old spec, maybe wrong or conditional
	172 bytes - themedtank_mm_top_curve135_long.bfb - 44 bytes until matname, all before vec are zero
	"""

	__name__ = 'BillboardLink'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.u_0 = name_type_map['Uint'](self.context, 0, None)
		self.has_obj = name_type_map['Uint'].from_value(1)
		self.u_1 = name_type_map['Uint64'](self.context, 0, None)
		self.dummy = name_type_map['Uint64'](self.context, 0, None)
		self.axis = name_type_map['Vector3'](self.context, 0, None)
		self.u_2 = name_type_map['Uint'](self.context, 0, None)
		self.object_id = name_type_map['Uint'](self.context, 0, None)
		self.material = name_type_map['FixedString'](self.context, 128, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'u_0', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'has_obj', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'u_1', name_type_map['Uint64'], (0, None), (False, None), (None, None)
		yield 'dummy', name_type_map['Uint64'], (0, None), (False, None), (None, None)
		yield 'axis', name_type_map['Vector3'], (0, None), (False, None), (None, None)
		yield 'u_2', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'object_id', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'material', name_type_map['FixedString'], (128, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'u_0', name_type_map['Uint'], (0, None), (False, None)
		yield 'has_obj', name_type_map['Uint'], (0, None), (False, 1)
		yield 'u_1', name_type_map['Uint64'], (0, None), (False, None)
		yield 'dummy', name_type_map['Uint64'], (0, None), (False, None)
		yield 'axis', name_type_map['Vector3'], (0, None), (False, None)
		yield 'u_2', name_type_map['Uint'], (0, None), (False, None)
		yield 'object_id', name_type_map['Uint'], (0, None), (False, None)
		yield 'material', name_type_map['FixedString'], (128, None), (False, None)
