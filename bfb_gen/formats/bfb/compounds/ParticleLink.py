from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class ParticleLink(BaseStruct):

	"""
	76 bytes - CavePaintingHall
	"""

	__name__ = 'ParticleLink'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.u_0 = name_type_map['Uint'].from_value(1)
		self.u_1 = name_type_map['Uint'].from_value(1)
		self.u_2 = name_type_map['Uint'].from_value(1)

		# case-insensitive
		self.emitter = name_type_map['FixedString'](self.context, 64, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'u_0', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'u_1', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'u_2', name_type_map['Uint'], (0, None), (False, 1), (None, None)
		yield 'emitter', name_type_map['FixedString'], (64, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'u_0', name_type_map['Uint'], (0, None), (False, 1)
		yield 'u_1', name_type_map['Uint'], (0, None), (False, 1)
		yield 'u_2', name_type_map['Uint'], (0, None), (False, 1)
		yield 'emitter', name_type_map['FixedString'], (64, None), (False, None)
