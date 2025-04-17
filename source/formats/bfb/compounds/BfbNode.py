# START_GLOBALS
import logging
from io import BytesIO

from bfb_gen.base_struct import BaseStruct


# END_GLOBALS


class BfbNode(BaseStruct):

	# START_CLASS


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		if instance.childstart:
			child = BfbNode.from_stream(stream, context, instance)
			instance.children.append(child)
		if instance.nextblockstart:
			assert isinstance(arg, BfbNode)
			sibling = BfbNode.from_stream(stream, context, arg)
			arg.children.append(sibling)
		return instance

	@classmethod
	def write_fields(cls, stream, instance):
		instance.io_start = stream.tell()
