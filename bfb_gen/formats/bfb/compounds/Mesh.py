from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bfb.imports import name_type_map


class Mesh(BaseStruct):

	__name__ = 'Mesh'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.flag = name_type_map['Ubyte'].from_value(0)
		self.dataid = name_type_map['Uint'](self.context, 0, None)
		self.u_int = name_type_map['Uint'](self.context, 0, None)
		self.t_sta = name_type_map['Uint'](self.context, 0, None)
		self.t_num = name_type_map['Uint'](self.context, 0, None)
		self.v_sta = name_type_map['Uint'](self.context, 0, None)
		self.v_num = name_type_map['Uint'](self.context, 0, None)
		self.f_num = name_type_map['Uint'](self.context, 0, None)
		self.bounds_extent = name_type_map['Vector3'](self.context, 0, None)
		self.bounds_radius = name_type_map['Float'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 0), (None, None)
		yield 'dataid', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'u_int', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 't_sta', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 't_num', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'v_sta', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'v_num', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'f_num', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'bounds_extent', name_type_map['Vector3'], (0, None), (False, None), (None, None)
		yield 'bounds_radius', name_type_map['Float'], (0, None), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'flag', name_type_map['Ubyte'], (0, None), (False, 0)
		yield 'dataid', name_type_map['Uint'], (0, None), (False, None)
		yield 'u_int', name_type_map['Uint'], (0, None), (False, None)
		yield 't_sta', name_type_map['Uint'], (0, None), (False, None)
		yield 't_num', name_type_map['Uint'], (0, None), (False, None)
		yield 'v_sta', name_type_map['Uint'], (0, None), (False, None)
		yield 'v_num', name_type_map['Uint'], (0, None), (False, None)
		yield 'f_num', name_type_map['Uint'], (0, None), (False, None)
		yield 'bounds_extent', name_type_map['Vector3'], (0, None), (False, None)
		yield 'bounds_radius', name_type_map['Float'], (0, None), (False, None)
