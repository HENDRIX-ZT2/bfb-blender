from generated.formats.bf.compounds.BfRoot import BfRoot
from generated.io import IoFile


class BfContext(object):
	def __init__(self):
		self.version = 0

	def __repr__(self):
		return f"{self.version}"


class BfFile(BfRoot, IoFile):

	def __init__(self):
		super().__init__(BfContext())


if __name__ == "__main__":
	pass
