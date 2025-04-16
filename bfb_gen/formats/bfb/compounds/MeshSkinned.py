from bfb_gen.array import Array
from bfb_gen.formats.bfb.compounds.Mesh import Mesh
from bfb_gen.formats.bfb.imports import name_type_map


class MeshSkinned(Mesh):

	__name__ = 'MeshSkinned'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.num_bones = name_type_map['Uint'](self.context, 0, None)
		self.num_weights = name_type_map['Uint'](self.context, 0, None)
		self.bones = Array(self.context, 0, None, (0,), name_type_map['Bone'])
		self.weights = Array(self.context, 0, None, (0,), name_type_map['Weight'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'num_bones', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'num_weights', name_type_map['Uint'], (0, None), (False, None), (None, None)
		yield 'bones', Array, (0, None, (None,), name_type_map['Bone']), (False, None), (None, None)
		yield 'weights', Array, (0, None, (None,), name_type_map['Weight']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		yield 'num_bones', name_type_map['Uint'], (0, None), (False, None)
		yield 'num_weights', name_type_map['Uint'], (0, None), (False, None)
		yield 'bones', Array, (0, None, (instance.num_bones,), name_type_map['Bone']), (False, None)
		yield 'weights', Array, (0, None, (instance.num_weights,), name_type_map['Weight']), (False, None)
