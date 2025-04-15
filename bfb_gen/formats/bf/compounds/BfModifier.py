from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfModifier(BaseStruct):

	__name__ = 'BfModifier'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.key_type = name_type_map['KeyType'](self.context, 0, None)
		self.num_keys = name_type_map['Short'](self.context, 0, None)
		self.num_bytes = name_type_map['Uint'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'key_type', name_type_map['KeyType'], (0, None), (False, None), (None, None)
		yield 'num_keys', name_type_map['Short'], (0, None), (False, None), (None, None)
		yield 'num_bytes', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'keys', Array, (0, None, (None,), name_type_map['LocQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['LocLinear']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['EulerQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['EulerQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['EulerQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['QuaternionQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['QuaternionLinear']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['ScaleQuadratic']), (False, None), (None, True)
		yield 'keys', Array, (0, None, (None,), name_type_map['ScaleLinear']), (False, None), (None, True)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'key_type', name_type_map['KeyType'], (0, None), (False, None)
		yield 'num_keys', name_type_map['Short'], (0, None), (False, None)
		yield 'num_bytes', name_type_map['Uint'], (0, None), (False, None)
		if instance.key_type == 1:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['LocQuadratic']), (False, None)
		if instance.key_type == 2:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['LocLinear']), (False, None)
		if instance.key_type == 6:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['EulerQuadratic']), (False, None)
		if instance.key_type == 7:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['EulerQuadratic']), (False, None)
		if instance.key_type == 8:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['EulerQuadratic']), (False, None)
		if instance.key_type == 12:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['QuaternionQuadratic']), (False, None)
		if instance.key_type == 14:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['QuaternionLinear']), (False, None)
		if instance.key_type == 16:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['ScaleQuadratic']), (False, None)
		if instance.key_type == 17:
			yield 'keys', Array, (0, None, (instance.num_keys,), name_type_map['ScaleLinear']), (False, None)
