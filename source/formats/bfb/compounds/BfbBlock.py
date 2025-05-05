# START_GLOBALS
from bfb_gen.base_struct import BaseStruct


# END_GLOBALS


class BfbNode(BaseStruct):

	# START_CLASS


	@classmethod
	def write_fields(cls, stream, instance):
		instance.end = instance.io_start + instance.get_size(instance, instance.context)
		super().write_fields(stream, instance)
