from generated.formats.bf.compounds.BfRoot import BfRoot
from generated.io import IoFile
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
		with io.BytesIO() as dummy:
			self.to_stream(dummy, self)
		for node in self.nodes:
			node.num_bytes = node.io_size
			for mod in node.modifiers:
				mod.num_bytes = mod.io_size
		super().save(filepath)


if __name__ == "__main__":
	pass
