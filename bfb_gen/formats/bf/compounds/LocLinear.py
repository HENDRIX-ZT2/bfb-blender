from bfb_gen.formats.bf.compounds.BaseKey import BaseKey
from bfb_gen.formats.bf.imports import name_type_map


class LocLinear(BaseKey):

	__name__ = 'LocLinear'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.x = name_type_map['Float'](self.context, 0, None)
		self.y = name_type_map['Float'](self.context, 0, None)
		self.z = name_type_map['Float'](self.context, 0, None)
		self.x = name_type_map['Short1000'](self.context, 0, None)
		self.y = name_type_map['Short1000'](self.context, 0, None)
		self.z = name_type_map['Short1000'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'x', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'y', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'z', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'x', name_type_map['Short1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'y', name_type_map['Short1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'z', name_type_map['Short1000'], (0, None), (False, None), (lambda context: context.version >= 2, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		if instance.context.version <= 1:
			yield 'x', name_type_map['Float'], (0, None), (False, None)
			yield 'y', name_type_map['Float'], (0, None), (False, None)
			yield 'z', name_type_map['Float'], (0, None), (False, None)
		if instance.context.version >= 2:
			yield 'x', name_type_map['Short1000'], (0, None), (False, None)
			yield 'y', name_type_map['Short1000'], (0, None), (False, None)
			yield 'z', name_type_map['Short1000'], (0, None), (False, None)
