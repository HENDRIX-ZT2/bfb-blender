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
	'Ubyte50': 'bfb_gen.formats.bf.basic',
	'Ushort1000': 'bfb_gen.formats.bf.basic',
	'Short1000': 'bfb_gen.formats.bf.basic',
	'Short10000': 'bfb_gen.formats.bf.basic',
	'KeyType': 'bfb_gen.formats.bf.enums.KeyType',
	'BfRoot': 'bfb_gen.formats.bf.compounds.BfRoot',
	'BfHeader': 'bfb_gen.formats.bf.compounds.BfHeader',
	'BfFooter': 'bfb_gen.formats.bf.compounds.BfFooter',
	'BfNode': 'bfb_gen.formats.bf.compounds.BfNode',
	'BfModifier': 'bfb_gen.formats.bf.compounds.BfModifier',
	'ScaleQuadratic': 'bfb_gen.formats.bf.compounds.ScaleQuadratic',
	'ScaleLinear': 'bfb_gen.formats.bf.compounds.ScaleLinear',
	'EulerQuadratic': 'bfb_gen.formats.bf.compounds.EulerQuadratic',
	'QuaternionQuadratic': 'bfb_gen.formats.bf.compounds.QuaternionQuadratic',
	'QuaternionLinear': 'bfb_gen.formats.bf.compounds.QuaternionLinear',
	'LocQuadratic': 'bfb_gen.formats.bf.compounds.LocQuadratic',
	'LocLinear': 'bfb_gen.formats.bf.compounds.LocLinear',
}

name_type_map = {}
for type_name, module in type_module_name_map.items():
	name_type_map[type_name] = getattr(import_module(module), type_name)
for class_object in name_type_map.values():
	if callable(getattr(class_object, 'init_attributes', None)):
		class_object.init_attributes()
