from bfb_gen.formats.bf.compounds.BfRoot import BfRoot
from bfb_gen.io import IoFile
import io


class BfContext(object):
	def __init__(self):
		self.version = 0

	def __repr__(self):
		return f"{self.version}"


class BfFile(BfRoot, IoFile):

	def __init__(self):
		super().__init__(BfContext())

	def save(self, filepath):
		# before saving, update sizes for the structs that have them
		for node in self.nodes:
			for mod in node.modifiers:
				mod.num_bytes = mod.get_size(mod, mod.context)
			node.num_bytes = node.get_size(node, node.context)
		super().save(filepath)


if __name__ == "__main__":
	pass
