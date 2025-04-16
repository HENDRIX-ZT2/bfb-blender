from bfb_gen.formats.bf.compounds.QuaternionLinear import QuaternionLinear
from bfb_gen.formats.bf.imports import name_type_map


class QuaternionQuadratic(QuaternionLinear):

	__name__ = 'QuaternionQuadratic'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.t = name_type_map['Float'](self.context, 0, None)
		self.b = name_type_map['Float'](self.context, 0, None)
		self.c = name_type_map['Float'](self.context, 0, None)
		self.t = name_type_map['Short10000'](self.context, 0, None)
		self.b = name_type_map['Short10000'](self.context, 0, None)
		self.c = name_type_map['Short10000'](self.context, 0, None)
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 't', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'b', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 'c', name_type_map['Float'], (0, None), (False, None), (lambda context: context.version <= 1, None)
		yield 't', name_type_map['Short10000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'b', name_type_map['Short10000'], (0, None), (False, None), (lambda context: context.version >= 2, None)
		yield 'c', name_type_map['Short10000'], (0, None), (False, None), (lambda context: context.version >= 2, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		if instance.context.version <= 1:
			yield 't', name_type_map['Float'], (0, None), (False, None)
			yield 'b', name_type_map['Float'], (0, None), (False, None)
			yield 'c', name_type_map['Float'], (0, None), (False, None)
		if instance.context.version >= 2:
			yield 't', name_type_map['Short10000'], (0, None), (False, None)
			yield 'b', name_type_map['Short10000'], (0, None), (False, None)
			yield 'c', name_type_map['Short10000'], (0, None), (False, None)
