from bfb_gen.base_enum import BaseEnum
from bfb_gen.formats.base.basic import Ushort


class BlockType(BaseEnum):

	__name__ = 'BlockType'
	_storage = Ushort

	SPHERE = 1
	BOUNDING_BOX = 3
	CAPSULE = 4
	MESH = 5
	MESH_DATA = 6
	MESH_SKINNED = 8
