import logging
import os
from xml.etree import ElementTree as ET

import bpy
import mathutils

from modules_import.anim import get_rna_path

def export_material_channel(parent, name, data):
	offsetv = ET.SubElement(parent, name)
	for t, v in data:
		ET.SubElement(offsetv, "key", {"time": fmt_float(t), "value": fmt_float(v)})


def fmt_float(f):
	return f"{f:.6f}"

def write_bfmat(reporter, b_ob, b_mat, export_dir, mat_name):
	options = {
		"AmbientMaterialSource": 1,
		"ColorApplyMode": 4,
		"CullMode": 1,
		"DiffuseMaterialSource": 1,
		"EmissiveMaterialSource": 0,
		"MaterialAmbient": [1.0, 1.0, 1.0, 1.0],
		"MaterialDiffuse": [1.0, 1.0, 1.0, 1.0],
		"MaterialEmissive": [0.0, 0.0, 0.0, 1.0],
		"MaterialPower": 1.0,
		"ShadeMode": 2,
		"SpecularEnable": False}

	logging.info(f"Exporting BFMAT file for {b_mat.name}")
	bfmat = ET.Element('material')
	fps = bpy.context.scene.render.fps

	alpha_node = b_mat.node_tree.nodes.get("Transparent BSDF")
	options["AlphaBlendEnable"] = False
	options["AlphaTestEnable"] = False
	options["AlphaApplyMode"] = 4
	if alpha_node:
		options["AlphaFunc"] = 5
		if b_mat.surface_render_method == "DITHERED":
			options["AlphaTestEnable"] = True
		elif b_mat.surface_render_method == "BLENDED":
			options["AlphaBlendEnable"] = True
			if b_mat.use_transparent_shadow:
				options["AlphaTestEnable"] = True
			options["DestBlend"] = 6
			options["SrcBlend"] = 5
	if options["AlphaTestEnable"]:
		options["AlphaRef"] = int(255.0 - b_mat.alpha_threshold * 255.0)
	# todo maybe import
	# bpy.data.materials["bathroomlarge_xt_falling_water_mod0"].diffuse_color
	texture_nodes = []
	for i in range(3):
		texture_node = b_mat.node_tree.nodes.get(f"Texture{i}")
		if texture_node:
			texture_nodes.append(texture_node)
			if texture_node.image:
				image = texture_node.image.filepath
				# fallback for generated images
				if not image:
					image = texture_node.image.name
				# strip the extension and save it
				options[f"Texture{i}"] = os.path.splitext(os.path.basename(image))[0]
			else:
				reporter.show_warning(f"Texture {texture_node.texture.name} in material {b_mat.name} contains no image!")
		transform_node = b_mat.node_tree.nodes.get(f"TextureTransform{i}")
		if transform_node:
			options[f"TextureTransformFlags{i}"] = 2
			# UV anim
			dp = get_rna_path(transform_node.name, n_node_input=1)
			u = find_fcurve(b_mat.node_tree, dp, 0)
			v = find_fcurve(b_mat.node_tree, dp, 1)
			if u:
				animate = ET.SubElement(bfmat, "animate",{
					"name": f"TextureTransform{i}",
					"type": "UVTransform",
					"loop": "wrap",
					"length": str(max(u.range()[1], v.range()[1])/fps)})
				export_material_channel(animate, "offsetv", [(k.co[0] / fps, -k.co[1]) for k in v.keyframe_points])
				export_material_channel(animate, "offsetu", [(k.co[0] / fps, k.co[1]) for k in u.keyframe_points])
				# not exactly sure what these are for? - not supported atm
				export_material_channel(animate, "tileu", [(0.0, 1.0), ])
				export_material_channel(animate, "tilev", [(0.0, 1.0), ])
				export_material_channel(animate, "rotw", [(0.0, 0.0), ])
			else:
				# static tex transform matrix
				matrix_4x4 = mathutils.Matrix.LocRotScale(
					transform_node.inputs["Location"].default_value,
					transform_node.inputs["Rotation"].default_value,
					transform_node.inputs["Scale"].default_value)
				matrix_4x4.translation.y *= -1.0
				options[f"TextureTransform{i}"] = matrix_4x4
		texcoord_node = b_mat.node_tree.nodes.get(f"TexCoordIndex{i}")
		if texcoord_node:
			# try to grab texcoord from node
			try:
				texcoord = int(texcoord_node.uv_map)
			except:
				logging.warning(f"{texcoord_node.name} does not follow the UV layer naming convention (numbers only), TexCoordIndex set to 0")
				texcoord = 0
			options[f"TexCoordIndex{i}"] = texcoord
			# these are probably only used when static UV coords are given
			options[f"AddressU{i}"] = 1
			options[f"AddressV{i}"] = 1

	if len(texture_nodes) == 1:
		options["LightingEnable"] = True
	# first try to get imported fx from output_node.label, then fall back
	try:
		output_node = b_mat.node_tree.nodes.get("Material Output")
		fx = output_node.label
	except:
		fx = "Base"
		if len(texture_nodes) == 2:
			fx += "Decal"
		if len(texture_nodes) == 3:
			fx += "DecalDetail"
		if 'fx_wind' in b_ob.vertex_groups:
			fx += "_wind"
			# this is for some shaders to make sure the decal set uses the UV1
			if len(b_ob.data.uv_layers) > 1:
				fx += "_uv11"
		reporter.show_warning(f"Guessed {fx} shader for {b_mat.name}")
	bfmat.set("fx", fx)
	# todo - support alternative mat_name from property or node
	bfmat.set("name", mat_name)

	dt_map = {list: "vector4", int: "dword", bool: "bool", float: "float", str: "texture", mathutils.Matrix: "matrix"}
	for name, default in options.items():
		param = ET.SubElement(bfmat, "param", {"name": name, "type": dt_map[type(default)]})
		if isinstance(default, list):
			param.text = ", ".join([fmt_float(x) for x in default])
		elif isinstance(default, mathutils.Matrix):
			param.text = ", ".join([fmt_float(x) for xs in default for x in xs])
		else:
			param.text = str(default).lower()
	# sort children by name
	bfmat[:] = sorted(bfmat, key=lambda child: child.get("name"))
	material_tree = ET.ElementTree(bfmat)
	indent(bfmat)
	material_dir = os.path.join(export_dir, "Materials")
	if not os.path.exists(material_dir):
		os.makedirs(material_dir)
	material_tree.write(os.path.join(material_dir, f"{mat_name}.bfmat"))


def get_mat_names(reporter, b_ob, export_dir, export_materials):

	if len(b_ob.data.materials):
		# sometimes there will be empty slots before a material
		for material in b_ob.data.materials:
			if material:
				mat_name = material.name.replace(".", "")
				if export_materials:
					try:
						write_bfmat(reporter, b_ob, material, export_dir, mat_name)
					except:
						logging.exception(f"Bfmat export failed")
				yield mat_name
	# else:
		# log_error(f'Mesh {b_ob.name} has no Material, no BFMAT was exported!')
		# mat_name = 'none'


def indent(elem, level=0):
	i = "\n" + level * "	"
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "	"
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level + 1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


def find_fcurve(id_data, path, index=0):
	# little utility function for searching fcurves
	anim_data = id_data.animation_data
	if anim_data:
		for fcurve in anim_data.action.fcurves:
			if fcurve.data_path == path and fcurve.array_index == index:
				return fcurve
