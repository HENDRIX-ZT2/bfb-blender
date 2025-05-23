# START_GLOBALS

from bfb_gen.base_struct import BaseStruct
from bfb_gen.formats.bf.compounds.TxtKey import TxtKey


# END_GLOBALS


class BfFooter(BaseStruct):

	# START_CLASS


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


