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
}

name_type_map = {}
for type_name, module in type_module_name_map.items():
	name_type_map[type_name] = getattr(import_module(module), type_name)
for class_object in name_type_map.values():
	if callable(getattr(class_object, 'init_attributes', None)):
		class_object.init_attributes()
