import itertools
import time
import bpy
import mathutils
import xml.etree.ElementTree as ET

from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType
from modules_export.collision import export_bounding_box, export_sphere, export_capsule
from modules_import.anim import get_rna_path
from .common_bfb import *


def flatten(mat):
	return [v for row in mat for v in row]


def log_error(error):
	print(error)
	global errors
	errors.append(error)


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


# little utility function for searching fcurves
def find_fcurve(id_data, path, index=0):
	anim_data = id_data.animation_data
	if anim_data:
		for fcurve in anim_data.action.fcurves:
			if fcurve.data_path == path and fcurve.array_index == index:
				return fcurve


def write_bfmat(b_ob, b_mat, mat_name):
	matoptions = [
		("AlphaApplyMode", "dword", "4"),
		("AlphaBlendEnable", "bool", "false"),
		("AlphaFunc", "dword", "5"),
		("AlphaRef", "dword", "127"),
		("AlphaTestEnable", "bool", "true"),
		("AmbientMaterialSource", "dword", "1"),
		("ColorApplyMode", "dword", "4"),
		("CullMode", "dword", "1"),
		("DiffuseMaterialSource", "dword", "1"),
		("EmissiveMaterialSource", "dword", "0"),
		("MaterialAmbient", "vector4", "1, 1, 1, 1"),
		("MaterialDiffuse", "vector4", "1, 1, 1, 1"),
		("MaterialEmissive", "vector4", "0, 0, 0, 1"),
		("MaterialPower", "float", "1"),
		("ShadeMode", "dword", "2"),
		("SpecularEnable", "bool", "false")]

	logging.info(f"Exporting BFMAT file for {b_mat.name}")
	mat_path = os.path.join(dir_path, "Materials")
	if not os.path.exists(mat_path):
		os.makedirs(mat_path)
	bfmat = ET.Element('material')
	fps = bpy.context.scene.render.fps

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
				matoptions.append((f"Texture{i}", "texture", os.path.splitext(os.path.basename(image))[0]))
			else:
				log_error(f"Texture {texture_node.texture.name} in material {b_mat.name} contains no image!")
		transform_node = b_mat.node_tree.nodes.get(f"TextureTransform{i}")
		if transform_node:
			# UV anim
			dp = get_rna_path(transform_node.name, n_node_input=1)
			u = find_fcurve(b_mat.node_tree, dp, 0)
			v = find_fcurve(b_mat.node_tree, dp, 1)

			if u:
				animate = ET.SubElement(bfmat, "animate",{"name": f"TextureTransform{i}", "type":"UVTransform", "loop": "wrap", "length": str(max(u.range()[1],v.range()[1])/fps)})
				offsetu = ET.SubElement(animate, "offsetu")
				for k in u.keyframe_points:
					ET.SubElement(offsetu, "key",{"time":str(k.co[0]/fps),"value":str(k.co[1])})
				offsetv = ET.SubElement(animate, "offsetv")
				for k in v.keyframe_points:
					ET.SubElement(offsetv, "key",{"time":str(k.co[0]/fps),"value":str(-k.co[1])})
				# not exactly sure what these are for? - not supported atm
				tileu =  ET.SubElement(animate, "tileu")
				ET.SubElement(tileu, "key",{"time":"0.0","value":"1.0"})
				tilev =  ET.SubElement(animate, "tilev")
				ET.SubElement(tilev, "key",{"time":"0.0","value":"1.0"})
				rotw =  ET.SubElement(animate, "rotw")
				ET.SubElement(rotw, "key",{"time":"0.0","value":"0.0"})

			matoptions.append((f"AddressU{i}", "dword", "1"))
			matoptions.append((f"AddressV{i}", "dword", "1"))
		texcoord_node = b_mat.node_tree.nodes.get(f"TexCoordIndex{i}")
		if texcoord_node:
			# try to grab texcoord from node
			try:
				texcoord = str(int(texcoord_node.uv_map))
			except:
				logging.warning(f"{texcoord_node.name} does not follow the UV layer naming convention (numbers only), TexCoordIndex set to 0")
				texcoord = "0"
			matoptions.append((f"TexCoordIndex{i}", "dword", texcoord))

	# todo: first try to get imported fx from output_node.label, then fall back
	fx = "Base"
	if len(texture_nodes) == 1:
		matoptions.append(("LightingEnable", "bool", "true"))
	elif len(texture_nodes) == 2:
		fx += "Decal"
	elif len(texture_nodes) == 3:
		fx += "DecalDetail"
	if b_ob in ob_2_fx_wind:
		fx += ob_2_fx_wind[b_ob]
	bfmat.set("fx", fx)
	bfmat.set("name", mat_name)

	for option in sorted(matoptions, key=lambda x: x[0]):
		param = ET.SubElement(bfmat, "param", {"name": option[0], "type": option[1]})
		param.text = str(option[2])

	material_tree = ET.ElementTree(bfmat)
	indent(bfmat)
	material_tree.write(os.path.join(mat_path, f"{mat_name}.bfmat"))


def attach_collision(bfb_node, new_collider_id):
	bfb_node.num_colliders += 1
	colliders = list(bfb_node.collision_ids)
	colliders.append(new_collider_id)
	bfb_node.reset_field("collision_ids")
	bfb_node.collision_ids[:] = colliders


def export_tree(b_ob, bfb, bfb_parent=None):
	logging.debug(f'Gathering block data for {b_ob.name}')
	if b_ob.type in ("EMPTY", "ARMATURE"):
		if b_ob.name.startswith('lodgroup'):
			# LOD group
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.LOD_GROUP, bfb_parent)
			bfb_node.unk_0 = 2
			bfb_node.unk_1 = 0
			bfb_node.lodgroup = "lodgroup"
		else:
			# node, with or without collision attached
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.NODE, bfb_parent)
			# with collision: unk_0 and unk_1 both = 0 or 1
			bfb_node.unk_0 = 0 # or 4 for lod0 nodes
			bfb_node.unk_1 = 0
	elif b_ob.type == "MESH":
		if b_ob.name.startswith('sphere'):
			attach_collision(bfb_parent, export_sphere(b_ob, bfb))
			return None
		elif b_ob.name.startswith('orientedbox'):
			attach_collision(bfb_parent, export_bounding_box(b_ob, bfb))
			return None
		elif b_ob.name.startswith('capsule'):
			if b_ob.parent_type != "BONE" or not b_ob.parent_bone:
				log_error(f"Capsule collider {b_ob.name} is not parented to a bone.")
			bone_name = blendername_to_bfbname(b_ob.parent_bone)
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.CAPSULE_LINK, bfb_parent)
			bfb_node.name = bone_name.lower()
			bfb_node.bone_name = bone_name
			attach_collision(bfb_node, export_capsule(b_ob, bfb))
		else:
			mesh_id = export_mesh(b_ob, bfb)
			if mesh_id is not None:
				if b_ob.constraints:
					bfb_node = bfb.create_node(b_ob, bfb, NodeType.BILLBOARD_LINK, bfb_parent)
					data = bfb_node.geometry
					data.axis[:] = mathutils.Vector((1.0, 0.0, -1.0))
				else:
					bfb_node = bfb.create_node(b_ob, bfb, NodeType.MESH_LINK, bfb_parent)
					bfb_node.unk_0 = 4
					bfb_node.unk_1 = 0
					bfb_node.name = "editable mesh"
					# or 0, 2, or rarely 0, 0
					data = bfb_node.geometry
				data.object_ids[0] = mesh_id
				data.materials[0] = get_mat_name(b_ob)
	else:
		# lamps etc, just ignore them
		return None
	for b_child in b_ob.children:
		bfb_child = export_tree(b_child, bfb, bfb_node)
		if bfb_child:
			bfb_node.children.append(bfb_child)
	return bfb_node


def get_mat_name(b_ob):
	mat_name = 'none'
	if len(b_ob.data.materials):
		# sometimes there will be empty slots before a material
		for material in b_ob.data.materials:
			if material:
				mat_name = material.name.replace(".", "")
				if write_materials:
					try:
						write_bfmat(b_ob, material, mat_name)
					except:
						logging.exception(f"Bfmat export failed")
				break
	else:
		log_error(f'Mesh {b_ob.name} has no Material, no BFMAT was exported!')
	return mat_name


def apply_transform(ob, ):
	identity = mathutils.Matrix()
	# the world space transform of every rigged mesh must be neutral
	# local space transforms of the mesh and its parents may be different as long as the mesh origin ends up on the b_scene origin
	if ob.matrix_world != identity:
		ob.data.transform(ob.matrix_world)
		ob.matrix_world = identity
		log_error(f"{ob.name} has had its transform applied to avoid ingame distortion!")


def export_mesh(b_ob, bfb):
	b_armature = b_ob.find_armature()
	# we have an armature on one mesh, means we can't export meshes without armature
	if has_armature and not b_armature:
		raise AttributeError(f"{b_ob.name} does not use an armature while other models do")
	if b_armature:
		bones_names = {name: i for i, name in enumerate(b_armature.data.bones.keys())}
	else:
		bones_names = {}

	# remove unneeded modifiers
	for b_mod in b_ob.modifiers:
		if b_mod.type in ('TRIANGULATE',):
			b_ob.modifiers.remove(b_mod)
		if b_mod.type in ('ARMATURE',):
			if not b_mod.object:
				raise AttributeError(f"{b_ob.name} has an armature modifier without object reference")
	b_ob.modifiers.new('Triangulate', 'TRIANGULATE')

	# make a copy with all modifiers applied
	dg = bpy.context.evaluated_depsgraph_get()
	eval_obj = b_ob.evaluated_get(dg)
	eval_me = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dg)

	if not eval_me.vertices:
		raise AttributeError(f"{b_ob.name} has no vertices. Delete the object and export again")

	if eval_me.uv_layers:
		# tangents have to be pre-calculated; this will also calculate loop normal
		try:
			eval_me.calc_tangents(uvmap=eval_me.uv_layers[0].name)
		except RuntimeError:
			raise RuntimeError(
				f"Tangent space calculation for model {b_ob.name} failed. Make sure it has valid geometry")
	else:
		logging.debug(f"No valid tangent space space for {b_ob.name} due to lack of UVs")
	mesh_vertices = []
	mesh_triangles = []
	# used to ignore the normals for checking equality
	dummy_vertices = {}

	weights_list = []
	if 'fx_wind' in b_ob.vertex_groups:
		weight_group_index = b_ob.vertex_groups['fx_wind'].index
		ob_2_fx_wind[b_ob] = "_wind"
		# this is for some shaders to make sure the decal set uses the UV1
		if len(eval_me.uv_layers) > 1:
			ob_2_fx_wind[b_ob] += "_uv11"
	# use this to look up the index of the uv layer
	# this is a little faster than
	BFRVertex = 'PN'
	if eval_me.vertex_colors:
		BFRVertex += 'D'
	for i in range(len(eval_me.uv_layers)):
		if 'fx_wind' in b_ob.vertex_groups:
			BFRVertex += f'T3{i}'
		else:
			BFRVertex += f'T{i}'
	# select all verts without weights
	unweighted_vertices = set()
	group_map = {vg.index: bones_names.get(vg.name, -1) for vg in b_ob.vertex_groups}
	for polygon in eval_me.polygons:
		tri = []
		for loop_index in polygon.loop_indices:
			vertex_index = eval_me.loops[loop_index].vertex_index
			vertex = eval_me.vertices[vertex_index]
			co = vertex.co
			no = eval_me.loops[loop_index].normal

			bfb_vertex = [(co.x, co.y, co.z), (no.x, no.y, no.z), ]
			if eval_me.vertex_colors:
				col = eval_me.vertex_colors[0].data[loop_index].color
				bfb_vertex += [(int(col[2] * 255), int(col[1] * 255), int(col[0] * 255), int(col[3] * 255)), ]
			for uv_layer in eval_me.uv_layers:
				uv_coord = uv_layer.data[loop_index].uv
				bfb_vertex += [(uv_coord.x, 1.0 - uv_coord.y), ]
				if 'T3' in BFRVertex:
					try:
						weight = vertex.groups[weight_group_index].weight
					except:
						weight = 0
					bfb_vertex.append(weight)
			key = tuple(bfb_vertex)
			if key not in dummy_vertices:
				dummy_vertices[key] = len(dummy_vertices)
				mesh_vertices.append(key)
				if b_armature:
					w = []
					for vertex_group in vertex.groups:
						try:
							w.append((group_map[vertex_group.group], vertex_group.weight))
						# dummy vertex groups without corresponding bones
						except:
							pass
					w_s = sorted(w, key=lambda x: x[1], reverse=True)[0:4]
					# pad the weight list to 4 bones, i.e. add empty bones if missing
					for i in range(0, 4 - len(w_s)):
						w_s.append((-1, 0.0))
					sw = w_s[0][1] + w_s[1][1] + w_s[2][1] + w_s[3][1]
					if sw > 0.0:
						weights_list.append((w_s[0][0], w_s[1][0], w_s[2][0], w_s[3][0],
											 w_s[0][1] / sw, w_s[1][1] / sw, w_s[2][1] / sw))
					else:
						unweighted_vertices.add(vertex_index)
			tri.append(dummy_vertices[key])
		mesh_triangles.append(tri)

	if unweighted_vertices:
		raise AttributeError(
			f'Found {len(unweighted_vertices)} unweighted vertices in {b_ob.name}! Add them to vertex groups!')

	if BFRVertex not in BFRVertex_2_meshData:
		mesh_data_block = bfb.create_block(b_ob.data, bfb, BlockType.MESH_DATA)
		mesh_data_block.name = "meshData"
		mesh_data_block.data.b_f_r_vertex = f"BFRVertex{BFRVertex}"
		mesh_data_block.users = []
		mesh_data_block.vertex_lists = []
		mesh_data_block.triangle_lists = []
		BFRVertex_2_meshData[BFRVertex] = mesh_data_block
	else:
		mesh_data_block = BFRVertex_2_meshData[BFRVertex]

	b_armature = b_ob.find_armature()
	if b_armature:
		mesh_block = bfb.create_block(b_ob, bfb, BlockType.MESH_SKINNED)
		mesh_block.data.num_weights = len(weights_list)
		mesh_block.data.reset_field("weights")
		mesh_block.data.weights[:] = weights_list

		export_bones(b_armature, mesh_block)
	else:
		mesh_block = bfb.create_block(b_ob, bfb, BlockType.MESH)

	mesh_block.data.data_id = mesh_data_block.id
	mesh_block.name = "mesh"
	mesh_data_block.users.append(mesh_block)
	mesh_data_block.vertex_lists.append(mesh_vertices)
	mesh_data_block.triangle_lists.append(mesh_triangles)
	return mesh_block.id


def save(operator, context, filepath='', author_name="HENDRIX", export_materials=True, create_lods=False,
		 fix_root_bones=False, numlods=1, rate=1):
	if create_lods:
		logging.info('Adding LODs')
		from . import batch_bfb
		batch_bfb.add_lods(numlods, rate)

	logging.info(f'Exporting {filepath}')
	global errors
	errors = []
	ensure_active_object()

	global write_materials
	write_materials = export_materials
	global dir_path
	dir_path = os.path.dirname(filepath)
	bfb = BfbFile()

	# if one model uses an armature, all have to. If they don't, they can't be exported.
	global has_armature
	has_armature = False
	global b_scale_action
	global ob_2_fx_wind
	ob_2_fx_wind = {}
	global BFRVertex_2_meshData
	BFRVertex_2_meshData = {}

	b_scene = bpy.context.scene
	start_time = time.time()
	logging.info('Generating block IDs for objects in b_scene')
	# keep track of objects without a parent, if >1 add an Auto Root
	roots = []
	for b_ob in b_scene.objects:
		if b_ob.type in ("EMPTY", "MESH", "ARMATURE"):
			if not b_ob.parent:
				roots.append(b_ob)
	if len(roots) == 1:
		b_root = roots[0]
		if b_root.name.startswith("lodgroup"):
			logging.warning('Lodgroup must not be root! Created an AutoRoot empty!')
			b_root = create_empty(None, 'AutoRoot', mathutils.Matrix())
			roots[0].parent = b_root
	else:
		logging.warning('Found more than one root object! Created an AutoRoot empty!')
		b_root = create_empty(None, 'AutoRoot', mathutils.Matrix())
		for b_ob in roots:
			logging.debug(f"{b_root.name} -> {b_ob.name}")
			b_ob.parent = b_root

	for b_ob in b_scene.objects:
		if b_ob.type == "MESH":
			b_armature = b_ob.find_armature()
			if b_armature:
				apply_transform(b_ob)
				has_armature = True
				ensure_valid_root_bones(b_armature, fix_root_bones, b_scene)
				# clear pose to ensure no distorted pose is applied
				for p_bone in b_armature.pose.bones:
					p_bone.matrix_basis = mathutils.Matrix()
				# apply the scale dummy action
				if "!scale!" in bpy.data.actions:
					b_scale_action = bpy.data.actions["!scale!"]
					b_armature.animation_data.action = b_scale_action
					b_scene.frame_set(0)
				else:
					logging.warning("Rest scale action is missing, assuming rest scale of 1.0 for all bones!")
					b_scale_action = None
			# fix meshes parented to a bone by adding vgroups
			if b_ob.parent_type == "BONE" and not b_ob.name.startswith('capsule'):
				log_error(
					f"{b_ob.name} was parented to a bone, which is not supported by BFBs. This has been fixed for you.")
				bone_name = b_ob.parent_bone
				b_ob.vertex_groups.new(name=bone_name)
				try:
					b_ob.data.transform(b_ob.parent.data.bones[bone_name].matrix_local)
				except:
					pass
				b_ob.vertex_groups[bone_name].add(range(len(b_ob.data.vertices)), 1.0, 'REPLACE')
				b_ob.parent_type = "OBJECT"
				b_scene.update()
				# apply again just to be sure
				apply_transform(b_ob)

	bfb.tree = export_tree(b_root, bfb)

	for BFRVertex, mesh_data_block in BFRVertex_2_meshData.items():
		logging.debug(f'Filling in BFRVertex{BFRVertex}')

		# fill in the meshData block
		verts = join_lists(mesh_data_block.vertex_lists)
		tris = join_lists(mesh_data_block.triangle_lists)
		mesh_data_block.data.verts.set_verts(verts)
		mesh_data_block.data.vertex_count = len(verts)
		mesh_data_block.data.num_tri_indices = len(tris) * 3
		mesh_data_block.data.reset_field("tris")
		mesh_data_block.data.tris[:] = tris
		# index into mesh_data_block
		vertex_offset = 0
		tris_offset = 0
		for mesh_block, vertex_list, triangle_list in zip(mesh_data_block.users, mesh_data_block.vertex_lists, mesh_data_block.triangle_lists):
			# create just 1 chunk
			chunk = mesh_block.data.chunks[0]
			chunk.vertex_offset = vertex_offset
			chunk.vertex_count = len(vertex_list)
			chunk.num_tris = len(triangle_list)
			chunk.tri_index_offset = tris_offset * 3
			chunk.num_tri_indices = chunk.num_tris * 3
			chunk_verts = mesh_data_block.data.verts.verts_data[chunk.vertex_offset: chunk.vertex_offset + chunk.vertex_count]["pos"]
			cog = np.mean(chunk_verts, axis=0)
			chunk.bounds_cog[:] = cog
			chunk.bounds_radius = np.max(np.linalg.norm(chunk_verts-cog, axis=1))

			vertex_offset += chunk.vertex_count
			tris_offset += chunk.num_tris

	bfb.header.author = author_name
	bfb.header.num_blocks = len(bfb.blocks)
	bfb.header.num_nodes = len(bfb.tree.get_children([])) + 1
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)
	bfb.save(filepath)
	print(bfb)
	logging.info(f'Finished BFB Export in {time.time() - start_time:.2f} seconds')
	return errors

def join_lists(lists):
	return list(itertools.chain(*lists))

def ensure_valid_root_bones(b_armature, fix_root_bones, b_scene):
	root_bones = [bone for bone in b_armature.data.bones.values() if not bone.parent]
	# fatal
	if len(root_bones) > 1:
		if fix_root_bones:
			# determine the proper root
			root_bone = root_bones[0]
			for bone in root_bones:
				if bone.name == "Bip01":
					root_bone = bone
					break
			b_scene.objects.active = b_armature
			bpy.ops.object.mode_set(mode='EDIT')
			# delete the other root bones
			for bone in root_bones:
				if bone != root_bone:
					e_bone = b_armature.data.edit_bones[bone.name]
					b_armature.data.edit_bones.remove(e_bone)
					logging.warning(f"Removed {bone.name} because it is a superfluous root bone")
			bpy.ops.object.mode_set(mode='OBJECT')
		else:
			raise AttributeError(f"{b_armature.name} has more than one root bone. Remove all other root bones so that only Bip01 remains. This usually means: Bake and export your animations and then remove all control bones before you export the model.")

def export_bones(b_armature, mesh_block):
	b_bones = b_armature.data.bones.values()
	# export bones
	mesh_block.data.num_bones = len(b_bones)
	mesh_block.data.reset_field("bones")
	for b_bone, p_bone, bfb_bone in zip(b_bones, b_armature.pose.bones, mesh_block.data.bones):
		bfb_bone.id = b_bones.index(b_bone) + 1
		if b_bone.parent:
			bfb_bone.parent_id = b_bones.index(b_bone.parent) + 1
		else:
			bfb_bone.parent_id = 0
		scale_matrix = get_rest_scale_matrix(b_bone)
		bfb_bone.priority = p_bone.get("priority", -1)
		bfb_bone.name = blendername_to_bfbname(b_bone.name).lower()
		bfb_bone.matrix.set_rows(scale_matrix @ get_bfb_matrix(b_bone).transposed())


def get_rest_scale_matrix(b_bone):
	# rest scale support
	try:
		group = b_scale_action.groups[b_bone.name]
		scales = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("scale")]
		scale = scales[0].keyframe_points[0].co[1]
	except:
		scale = 1.0
	return mathutils.Matrix.Scale(scale, 4)


