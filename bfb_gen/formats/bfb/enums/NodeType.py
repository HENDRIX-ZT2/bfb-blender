from bfb_gen.base_enum import BaseEnum
from bfb_gen.formats.base.basic import Uint


class NodeType(BaseEnum):

	__name__ = 'NodeType'
	_storage = Uint

	NODE = 1
	LOD_GROUP = 2
	MESH_LINK = 3
	BILLBOARD_LINK = 4
	CAPSULE_LINK = 5
	PARTICLE_LINK = 6
