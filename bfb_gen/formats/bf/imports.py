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
	'BaseKey': 'bfb_gen.formats.bf.compounds.BaseKey',
	'ScaleLinear': 'bfb_gen.formats.bf.compounds.ScaleLinear',
	'ScaleQuadratic': 'bfb_gen.formats.bf.compounds.ScaleQuadratic',
	'EulerQuadratic': 'bfb_gen.formats.bf.compounds.EulerQuadratic',
	'QuaternionLinear': 'bfb_gen.formats.bf.compounds.QuaternionLinear',
	'QuaternionQuadratic': 'bfb_gen.formats.bf.compounds.QuaternionQuadratic',
	'LocLinear': 'bfb_gen.formats.bf.compounds.LocLinear',
	'LocQuadratic': 'bfb_gen.formats.bf.compounds.LocQuadratic',
	'BfModifier': 'bfb_gen.formats.bf.compounds.BfModifier',
	'BfNode': 'bfb_gen.formats.bf.compounds.BfNode',
	'BfHeader': 'bfb_gen.formats.bf.compounds.BfHeader',
	'BfFooter': 'bfb_gen.formats.bf.compounds.BfFooter',
	'BfRoot': 'bfb_gen.formats.bf.compounds.BfRoot',
}

name_type_map = {}
for type_name, module in type_module_name_map.items():
	name_type_map[type_name] = getattr(import_module(module), type_name)
for class_object in name_type_map.values():
	if callable(getattr(class_object, 'init_attributes', None)):
		class_object.init_attributes()
