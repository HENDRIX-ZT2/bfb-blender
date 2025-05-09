import logging
import os
from pathlib import Path

import numpy as np

from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
np.seterr(all='raise')
np.set_printoptions(precision=3, suppress=True)


def walk_type(start_dir, extension=".ovl"):
	logging.info(f"Scanning {Path(start_dir)} for {extension} files")
	ret = []
	for root, dirs, files in os.walk(start_dir, topdown=False):
		for name in files:
			if extension and not name.lower().endswith(extension):
				continue
			ret.append(os.path.abspath(os.path.join(root, name)))
	return ret


def explore_tree(node):
	# if not node.num_colliders and node.type_id == NodeType.NODE:
	if node.type_id == NodeType.LOD_GROUP:
		print(node.unk_0, node.unk_1, bfb_path)

	# if node.num_colliders:
	# 	print(node)
	for child in node.children:
		explore_tree(child)

start_dir = "C:/Users/arnfi/Desktop/Coding/BFB"
for bfb_path in walk_type(start_dir, extension=".bfb"):
	rel_path = os.path.relpath(bfb_path, start_dir)
	try:
		logging.info(f"Reading {rel_path}")
		bfb = BfbFile()
		bfb.load(bfb_path)
		logging.info(f"Version: {bfb.header.version}")
		# explore_tree(bfb.tree)
		for block in bfb.blocks:
			if block.type_id == BlockType.SPHERE:
				print(bfb_path, block.name, block.data.flag)
	except:
		logging.exception(f"Failed {rel_path}")

bfb_path = "C:/Users/arnfi/Desktop/Coding/BFB/bfb objects/objects/buildings/DiscoveryKiosk_df/DiscoveryKiosk_df.bfb"
# bfb_path = "C:/Users/arnfi/Desktop/Coding/BFB/bfb objects/objects/fences/ThemedTank_mm/themedtank_mm_top_curve135_long.bfb"
# bfb_path = "C:/Users/arnfi/Desktop/Coding/BFB/bfb objects/objects/buildings/CavePaintingHall/CavePaintingHall.bfb"
# bfb_path = "C:/Users/arnfi/Desktop/Coding/BFB/bfb objects/objects/scenery/zoopedia_redwoodtunnel/zoopedia_redwoodtunnel.bfb"
# bfb = BfbFile()
# try:
# 	bfb.load(bfb_path)
# except:
# 	logging.exception("failed")
# print(bfb)

logging.info("Done")

