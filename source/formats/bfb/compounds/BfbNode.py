# START_GLOBALS
import logging

from bfb_gen.base_struct import BaseStruct


# END_GLOBALS


class BfbNode(BaseStruct):

	# START_CLASS


	@classmethod
	def from_stream(cls, stream, context, arg=0, template=None):
		instance = super().from_stream(stream, context, arg, template)
		# todo - figure out why sorting is required to get them in the correct order, probably due to return instance after reading
		# logging.info(f"instance: {instance.io_start}  {instance.name}")
		if instance.start_children:
			if stream.tell() != instance.start_children:
				logging.warning(f"BfbNode.start_children: {stream.tell()} != {instance.start_children}")
			child = BfbNode.from_stream(stream, context, instance)
			# logging.info(f"	child: {child.io_start} {child.name}")
			instance.children.append(child)
			instance.children.sort(key=lambda child: child.io_start)
		if instance.start_sibling:
			assert isinstance(arg, BfbNode)
			if stream.tell() != instance.start_sibling:
				logging.warning(f"BfbNode.start_sibling: {stream.tell()} != {instance.start_sibling}")
			try:
				sibling = BfbNode.from_stream(stream, context, arg)
				arg.children.append(sibling)
				arg.children.sort(key=lambda child: child.io_start)
			except:
				logging.exception("failed reading sibling")
		return instance

	def get_children(self, children=[]):
		children.extend(self.children)
		for child in self.children:
			child.get_children(children)
		return children

	def get_size_rec(self):
		size = self.get_size(self, self.context)
		for child in self.children:
			size += child.get_size_rec()
		return size

	@classmethod
	def write_fields(cls, stream, instance):
		if instance.children:
			instance.start_children = instance.io_start + instance.get_size(instance, instance.context)
			instance.num_children = len(instance.get_children([]))
		# is there a sibling?
		parent_node = instance.arg
		if parent_node:
			if parent_node.children.index(instance) < len(parent_node.children) - 1:
				instance.start_sibling = instance.io_start + instance.get_size_rec()
		instance.end = instance.io_start + instance.get_size(instance, instance.context)
		super().write_fields(stream, instance)
		for child in instance.children:
			child.to_stream(child, stream, child.context)
