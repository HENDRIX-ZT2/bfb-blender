from importlib import import_module


type_module_name_map = {
	'Byte': 'bfb_gen.formats.base.basic',
	'Ubyte': 'bfb_gen.formats.base.basic',
	'Uint64': 'bfb_gen.formats.base.basic',
	'Int64': 'bfb_gen.formats.base.basic',
	'Uint': 'bfb_gen.formats.base.basic',
	'Ushort': 'bfb_gen.formats.base.basic',
	'Int': 'bfb_gen.formats.base.basic',
	'Short': 'bfb_gen.formats.base.basic',
	'Char': 'bfb_gen.formats.base.basic',
	'Float': 'bfb_gen.formats.base.basic',
	'Double': 'bfb_gen.formats.base.basic',
	'ZString': 'bfb_gen.formats.base.basic',
	'FixedString': 'bfb_gen.formats.base.basic',
	'SizedString': 'bfb_gen.formats.base.basic',
	'Vector3': 'bfb_gen.formats.base.compounds.Vector3',
	'Matrix': 'bfb_gen.formats.base.compounds.Matrix',
	'Matrix44': 'bfb_gen.formats.base.compounds.Matrix44',
	'Matrix33': 'bfb_gen.formats.base.compounds.Matrix33',
	'BlockType': 'bfb_gen.formats.bfb.enums.BlockType',
	'NodeType': 'bfb_gen.formats.bfb.enums.NodeType',
	'Sphere': 'bfb_gen.formats.bfb.compounds.Sphere',
	'BoundingBox': 'bfb_gen.formats.bfb.compounds.BoundingBox',
	'Capsule': 'bfb_gen.formats.bfb.compounds.Capsule',
	'MeshReader': 'bfb_gen.formats.bfb.compounds.MeshReader',
	'MeshData': 'bfb_gen.formats.bfb.compounds.MeshData',
	'Chunk': 'bfb_gen.formats.bfb.compounds.Chunk',
	'Mesh': 'bfb_gen.formats.bfb.compounds.Mesh',
	'Bone': 'bfb_gen.formats.bfb.compounds.Bone',
	'Weight': 'bfb_gen.formats.bfb.compounds.Weight',
	'MeshSkinned': 'bfb_gen.formats.bfb.compounds.MeshSkinned',
	'BfbBlock': 'bfb_gen.formats.bfb.compounds.BfbBlock',
	'MeshLink': 'bfb_gen.formats.bfb.compounds.MeshLink',
	'BillboardLink': 'bfb_gen.formats.bfb.compounds.BillboardLink',
	'BfbNode': 'bfb_gen.formats.bfb.compounds.BfbNode',
	'BfbHeader': 'bfb_gen.formats.bfb.compounds.BfbHeader',
	'BfbRoot': 'bfb_gen.formats.bfb.compounds.BfbRoot',
}

name_type_map = {}
for type_name, module in type_module_name_map.items():
	name_type_map[type_name] = getattr(import_module(module), type_name)
for class_object in name_type_map.values():
	if callable(getattr(class_object, 'init_attributes', None)):
		class_object.init_attributes()
