
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.compounds.TxtKey import TxtKey


from bfb_gen.array import Array
from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.imports import name_type_map


class BfFooter(BaseStruct):

	__name__ = 'BfFooter'


	def __init__(self, context, arg=0, template=None, set_default=True):
		super().__init__(context, arg, template, set_default=False)
		self.txtkeys = Array(self.context, 0, None, (0,), name_type_map['TxtKey'])
		if set_default:
			self.set_defaults()

	@classmethod
	def _get_attribute_list(cls):
		yield from super()._get_attribute_list()
		yield 'txtkeys', Array, (0, None, (0,), name_type_map['TxtKey']), (False, None), (None, None)

	@classmethod
	def _get_filtered_attribute_list(cls, instance, include_abstract=True):
		yield from super()._get_filtered_attribute_list(instance, include_abstract)
		if include_abstract:
			yield 'txtkeys', Array, (0, None, (0,), name_type_map['TxtKey']), (False, None)


	@classmethod
	def read_fields(cls, stream, instance):
		while True:
			txtkey = TxtKey.from_stream(stream, instance.context)
			if txtkey.string:
				instance.txtkeys.append(txtkey)
			else:
				break

	@classmethod
	def write_fields(cls, stream, instance):
		for txtkey in instance.txtkeys:
			TxtKey.to_stream(txtkey, stream, instance.context)
		stream.write(b"\x00" * 7)



