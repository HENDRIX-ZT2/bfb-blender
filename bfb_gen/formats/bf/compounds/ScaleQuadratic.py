from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class ScaleQuadratic(BaseStruct):

	__name__ = 'ScaleQuadratic'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.time = name_type_map['Float'](self.context, 0, None)
		self.scale = name_type_map['Float'](self.context, 0, None)
		self.a = name_type_map['Float'](self.context, 0, None)
		self.b = name_type_map['Float'](self.context, 0, None)
		self.time = name_type_map['Ushort1000'](self.context, 0, None)
		self.scale = name_type_map['Ubyte50'](self.context, 0, None)
		self.a = name_type_map['Short1000'](self.context, 0, None)
		self.b = name_type_map['Short1000'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'time', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'scale', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'a', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'b', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'time', name_type_map['Ushort1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'scale', name_type_map['Ubyte50'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'a', name_type_map['Short1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'b', name_type_map['Short1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		if instance.context.version <= 1:
			yield 'time', name_type_map['Float'], (0, None), (False, None)
			yield 'scale', name_type_map['Float'], (0, None), (False, None)
			yield 'a', name_type_map['Float'], (0, None), (False, None)
			yield 'b', name_type_map['Float'], (0, None), (False, None)
		if instance.context.version >= 2:
			yield 'time', name_type_map['Ushort1000'], (0, None), (False, None)
			yield 'scale', name_type_map['Ubyte50'], (0, None), (False, None)
			yield 'a', name_type_map['Short1000'], (0, None), (False, None)
			yield 'b', name_type_map['Short1000'], (0, None), (False, None)
