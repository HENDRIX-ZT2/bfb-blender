from bfb_gen.formats.bfb.compounds.BfbBlock import BfbBlock
from bfb_gen.formats.bfb.compounds.BfbNode import BfbNode
from bfb_gen.formats.bfb.compounds.BfbRoot import BfbRoot
from bfb_gen.io import IoFile
import io


class BfbContext(object):
	def __init__(self):
		self.version = 0

	def __repr__(self):
		return f"{self.version}"


class BfbFile(BfbRoot, IoFile):

	def __init__(self):
		super().__init__(BfbContext())
		self.block_id = 1
		self.node_id = 1
		self.ob_2_block_id = {}
		self.ob_2_node_id = {}
	
	def create_block(self, b_ob, bfb, block_type):
		block = BfbBlock(bfb.context)
		# increment ID here, store block in dict
		self.ob_2_block_id[b_ob] = self.block_id
		block.id = self.block_id
		self.block_id += 1
		block.type_id = block_type
		block.reset_field("data")
		block.flag = 32768  # -32768 in original, short
		block.name = b_ob.name
		bfb.blocks.append(block)
		return block

	def create_node(self, b_ob, bfb, node_type, bfb_parent=None):
		node = BfbNode(bfb.context, arg=bfb_parent)
		node.name = "end_post" if "end_post" in b_ob.name else b_ob.name
		self.ob_2_node_id[b_ob] = self.node_id
		node.id = self.node_id
		self.node_id += 1
		node.type_id = node_type
		# todo check transpose
		node.matrix.set_rows(b_ob.matrix_local.transposed())
		return node
		
	# def save(self, filepath):
	# 	# before saving, update sizes for the structs that have them
	# 	for node in self.nodes:
	# 		for mod in node.modifiers:
	# 			mod.num_bytes = mod.get_size(mod, mod.context)
	# 		node.num_bytes = node.get_size(node, node.context)
	# 	super().save(filepath)


if __name__ == "__main__":
	pass
