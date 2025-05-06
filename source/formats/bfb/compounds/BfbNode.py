# START_GLOBALS
import logging

from bfb_gen.base_struct import BaseStruct


# END_GLOBALS


class BfbNode(BaseStruct):

	# START_CLASS


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		if instance.start_children:
			child = BfbNode.from_stream(stream, context, instance)
			instance.children.append(child)
		if instance.start_sibling:
			assert isinstance(arg, BfbNode)
			try:
				sibling = BfbNode.from_stream(stream, context, arg)
				arg.children.append(sibling)
			except:
				logging.exception("failed reading sibling")
		return instance

	@classmethod
	def get_size(cls, instance, context, arg=0, template=None, include_children=False):
		"""arguments is optional because it is not required for _get_filtered_attribute_list"""
		size = 0
		for f_name, f_type, arguments, _ in cls._get_filtered_attribute_list(instance, include_abstract=include_children):
			size += f_type.get_size(cls.get_field(instance, f_name), context, *arguments)
		return size

	@classmethod
	def write_fields(cls, stream, instance):
		if instance.children:
			instance.start_children = instance.io_start + instance.get_size(instance, instance.context, include_children=False)
		# is there a sibling?
		parent_node = instance.arg
		if parent_node:
			if parent_node.children.index(instance) < len(parent_node.children) - 1:
				instance.start_sibling = instance.io_start + instance.get_size(instance, instance.context, include_children=True)
		instance.end = instance.io_start + instance.get_size(instance, instance.context)
		super().write_fields(stream, instance)
		for child in instance.children:
			child.to_stream(child, stream, child.context)
