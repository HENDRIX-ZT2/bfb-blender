import itertools
import logging
import os
import time
import bpy
import mathutils
import xml.etree.ElementTree as ET
from struct import pack

from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.compounds.BfbBlock import BfbBlock
from bfb_gen.formats.bfb.compounds.BfbNode import BfbNode
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType
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
	try:
		anim_data = id_data.animation_data
		for fcurve in anim_data.action.fcurves:
			if fcurve.data_path == path and fcurve.array_index == index:
				return fcurve
	except:
		pass


def write_bfmat(ob, mat):
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

	logging.info(f"Exporting BFMAT file for {mat.name}")
	matpath = os.path.join(dirname, "Materials")
	if not os.path.exists(matpath):
		os.makedirs(matpath)
	material = ET.Element('material')
	fps = bpy.context.scene.render.fps

	# updated for node material
	texture_slots = []
	output = None
	for node in mat.node_tree.nodes:
		if "Texture" in node.name:
			texture_slots.append(node)
	for i, texture_slot in enumerate(texture_slots):

		# todo: support UV anim
		# u = find_fcurve(mat, "texture_slots["+str(i)+"].offset", 0)
		# v = find_fcurve(mat, "texture_slots["+str(i)+"].offset", 1)
		#
		# if u:
		# 	animate = ET.SubElement(material, "animate",{"name":"TextureTransform"+str(index),"type":"UVTransform", "loop":"wrap", "length":str(max(u.range()[1],v.range()[1])/fps)})
		# 	offsetu =  ET.SubElement(animate, "offsetu")
		# 	for k in u.keyframe_points:
		# 		ET.SubElement(offsetu, "key",{"time":str(k.co[0]/fps),"value":str(k.co[1])})
		# 	offsetv =  ET.SubElement(animate, "offsetv")
		# 	for k in v.keyframe_points:
		# 		ET.SubElement(offsetv, "key",{"time":str(k.co[0]/fps),"value":str(k.co[1])})
		# 	#not exactly sure what these are for? - not supported atm
		# 	tileu =  ET.SubElement(animate, "tileu")
		# 	ET.SubElement(tileu, "key",{"time":"0.0","value":"1.0"})
		# 	tilev =  ET.SubElement(animate, "tilev")
		# 	ET.SubElement(tilev, "key",{"time":"0.0","value":"1.0"})
		# 	rotw =  ET.SubElement(animate, "rotw")
		# 	ET.SubElement(rotw, "key",{"time":"0.0","value":"0.0"})

		# matoptions.append(("AddressU"+str(index), "dword", "1"))
		# matoptions.append(("AddressV"+str(index), "dword", "1"))
		if texture_slot.image:
			image = texture_slot.image.filepath
			# fallback for generated images
			if not image:
				image = texture_slot.image.name
			# strip the extension and save it
			matoptions.append(("Texture" + str(i), "texture", os.path.splitext(os.path.basename(image))[0]))
		# todo: try to grab texcord from node
		# try:
		# 	texcoord = str(int(texture_slot.uv_layer))
		# except:
		# 	error = texture_slot.name+" does not follow the UV layer naming convention (numbers only), TexCoordIndex set to 0"
		# 	print(error)
		# 	texcoord = list(mat.texture_slots).index(texture_slot)
		# matoptions.append(("TexCoordIndex"+str(index),"dword",texcoord))
		else:
			log_error('Texture ' + texture_slot.texture.name + ' in material ' + mat.name + ' contains no image!')

	# todo: first try to get imported fx from output_node.label, then fall back
	fx = "Base"
	if len(texture_slots) == 1:
		matoptions.append(("LightingEnable", "bool", "true"))
	elif len(texture_slots) == 2:
		fx += "Decal"
	elif len(texture_slots) == 3:
		fx += "DecalDetail"
	if ob in ob_2_fx_wind:
		fx += ob_2_fx_wind[ob]
	material.set("fx", fx)
	# dots don't work in ZT2
	material.set("name", mat.name.replace(".", ""))

	for option in sorted(matoptions, key=lambda x: x[0]):
		param = ET.SubElement(material, "param", {"name": option[0], "type": option[1]})
		param.text = str(option[2])

	materialtree = ET.ElementTree()
	materialtree._setroot(material)
	indent(material)
	materialtree.write(os.path.join(matpath, mat.name.replace(".", "") + ".bfmat"))


def has_collider(ob):
	# does this empty contain a collider object?
	if ob.children and (ob.children[0].name.startswith('sphere') or ob.children[0].name.startswith('orientedbox')):
		return True
	return False


def export_tree(b_ob, bfb, bfb_parent=None):
	logging.debug(f'Gathering block data for {b_ob.name}')
	if b_ob.type in ("EMPTY", "ARMATURE"):
		# LOD group
		if b_ob.name.startswith('lodgroup'):
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.LOD_GROUP, bfb_parent)
			bfb_node.unk = 2
			bfb_node.reset_field("data")
			data = bfb_node.data
			data.unk_0 = 0
			data.unk_1 = 2
			data.has_collision = 0
		else:
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.NODE, bfb_parent)
			# Root Block
			if not b_ob.parent:
				bfb_node.unk = 0
				bfb_node.reset_field("data")
				data = bfb_node.data
				data.unk_0 = 0
				data.unk_1 = 5
				data.has_collision = 0
			# node, with collision attached
			elif has_collider(b_ob):
				bfb_node.unk = 1
				bfb_node.reset_field("data")
				data = bfb_node.data
				data.unk_0 = 1
				data.unk_1 = 1
				# support multiple colliders
				data.num_colliders = len(b_ob.children)
				data.reset_field("collision_ids")
				data.collision_ids[:] = [bfb.ob_2_block_id[b_child] for b_child in b_ob.children[0]]
			# standard node
			else:
				bfb_node.unk = 1
				bfb_node.reset_field("data")
				data = bfb_node.data
				data.unk_0 = 1
				data.unk_1 = 1
				data.has_collision = 0
	elif b_ob.type == "MESH":
		if b_ob.name.startswith('sphere') or b_ob.name.startswith('orientedbox'):
			pass
		elif b_ob.name.startswith('capsule'):
			if b_ob.parent_type != "BONE" or not b_ob.parent_bone:
				log_error(f"Capsule collider {b_ob.name} is not parented to a bone.")
			bone_name = blendername_to_bfbname(b_ob.parent_bone)
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.CAPSULE_LINK, bfb_parent)
			bfb_node.unk = 0
			bfb_node.name = bone_name.lower()
			bfb_node.reset_field("data")
			data = bfb_node.data
			data.unk_0 = 1
			data.unk_1 = 1
			data.has_collision = 1
			data.bone_name = bone_name
			data.collision_id = bfb.ob_2_block_id[b_ob]
		else:
			matname = 'none'
			if len(b_ob.data.materials):
				# sometimes the will be empty slots before a material
				for material in b_ob.data.materials:
					if material:
						if write_materials:
							write_bfmat(b_ob, material)
						matname = material.name.replace(".", "")
						break
			else:
				log_error(f'Mesh {b_ob.name} has no Material, no BFMAT was exported!')
			if b_ob.constraints:
				bfb_node = bfb.create_node(b_ob, bfb, NodeType.BILLBOARD_LINK, bfb_parent)
				bfb_node.unk = 4
				bfb_node.reset_field("data")
				data = bfb_node.data
				data.object_id = bfb.ob_2_block_id[b_ob]
				data.material = matname
				data.axis[:] = mathutils.Vector((1.0, 0.0, -1.0))
			else:
				bfb_node = bfb.create_node(b_ob, bfb, NodeType.MESH_LINK, bfb_parent)
				bfb_node.unk = 4
				bfb_node.reset_field("data")
				data = bfb_node.data
				data.object_id = bfb.ob_2_block_id[b_ob]
				data.material = matname
	else:
		return
	for b_child in b_ob.children:
		bfb_child = export_tree(b_child, bfb, bfb_node)
		bfb_node.children.append(bfb_child)
	return bfb_node


# # are there any more siblings of this node left to add? siblings follow after all children of this node
	# has_sibling = False
	# if b_ob.parent:
	# 	for sibling in b_ob.parent.children[b_ob.parent.children.index(b_ob) + 1:]:
	# 		if type(sibling.data) in (type(None), bpy.types.Armature, bpy.types.Mesh):
	# 			has_sibling = True
	# 			break
	# 	next_sibling = start + len(data) + 16 if has_sibling else 0
	# 	return pack('<4i', bfb.ob_2_block_id[b_ob], type_id, next_child, next_sibling) + data


def apply_transform(ob, ):
	identity = mathutils.Matrix()
	# the world space transform of every rigged mesh must be neutral
	# local space transforms of the mesh and its parents may be different as long as the mesh origin ends up on the scene origin
	if ob.matrix_world != identity:
		ob.data.transform(ob.matrix_world)
		ob.matrix_world = identity
		log_error(f"{ob.name} has had its transform applied to avoid ingame distortion!")


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
	global dirname
	dirname = os.path.dirname(filepath)
	bfb = BfbFile()

	# if one model uses an armature, all have to. If they don't, they can't be exported.
	has_armature = False

	global ob_2_weights_list
	ob_2_weights_list = {}
	global ob_2_fx_wind
	ob_2_fx_wind = {}
	BFRVertex_2_meshData = {}

	global stream
	scene = bpy.context.scene
	stream = b''
	start_time = time.time()
	logging.info('Generating block IDs for objects in scene')
	# keep track of objects without a parent, if >1 add an Auto Root
	roots = []
	for b_ob in scene.objects:
		if type(b_ob.data) in (type(None), bpy.types.Armature, bpy.types.Mesh):
			if not b_ob.parent:
				roots.append(b_ob)
	if len(roots) == 1:
		b_root = roots[0]
		if b_root.name.startswith("lodgroup"):
			logging.warning('Lodgroup must not be root! Created an Auto Root empty!')
			b_root = create_empty(None, 'Auto Root', mathutils.Matrix())
			roots[0].parent = b_root
	else:
		logging.warning('Found more than one root object! Created an Auto Root empty!')
		b_root = create_empty(None, 'Auto Root', mathutils.Matrix())
		for b_ob in roots:
			b_ob.parent = b_root

	global ID
	ID = 1
	for b_ob in scene.objects:
		if type(b_ob.data) == bpy.types.Mesh:
			if b_ob.find_armature():
				apply_transform(b_ob)
				has_armature = True
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
				scene.update()
				# apply again just to be sure
				apply_transform(b_ob)
	logging.info('Gathering mesh data')
	# get all objects, meshData, meshes + skeletons and collisions
	for b_ob in scene.objects:
		if b_ob.type == "MESH":
			if b_ob.name.startswith('capsule'):
				export_capsule(b_ob, bfb)
			elif b_ob.name.startswith('sphere'):
				export_sphere(b_ob, bfb)
			elif b_ob.name.startswith('orientedbox'):
				export_bounding_box(b_ob, bfb)
			else:
				# export the armature if not already done for a previous mesh
				armature = b_ob.find_armature()
				# we have an armature on one mesh, means we can't export meshes without armature
				if has_armature and not armature:
					log_error(f"{b_ob.name} is not exported because it does not use an armature while other models do.")
					continue

				if armature:
					root_bones = [bone for bone in armature.data.bones.values() if not bone.parent]
					# fatal
					if len(root_bones) > 1:
						if fix_root_bones:
							# determine the proper root
							root_bone = root_bones[0]
							for bone in root_bones:
								if bone.name == "Bip01":
									root_bone = bone
									break
							scene.objects.active = armature
							bpy.ops.object.mode_set(mode='EDIT')
							# delete the other root bones
							for bone in root_bones:
								if bone != root_bone:
									e_bone = armature.data.edit_bones[bone.name]
									armature.data.edit_bones.remove(e_bone)
									logging.warning(f"Removed {bone.name} because it is a superfluous root bone")
							bpy.ops.object.mode_set(mode='OBJECT')
						else:
							log_error(
								f"{armature.name} has more than one root bone. Remove all other root bones so that only Bip01 remains. This usually means: Bake and export your animations and then remove all control bones before you export the model.")
							return errors
					# clear pose to ensure no distorted pose is applied
					for p_bone in armature.pose.bones:
						p_bone.matrix_basis = mathutils.Matrix()
					bones_names = {name: i for i, name in enumerate(armature.data.bones.keys())}
				else:
					bones_names = {}

				# remove unneeded modifiers
				for mod in b_ob.modifiers:
					if mod.type in ('TRIANGULATE',):
						b_ob.modifiers.remove(mod)
				b_ob.modifiers.new('Triangulate', 'TRIANGULATE')

				# make a copy with all modifiers applied
				dg = bpy.context.evaluated_depsgraph_get()
				eval_obj = b_ob.evaluated_get(dg)
				eval_me = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dg)

				if len(eval_me.vertices) == 0:
					log_error(f"{b_ob.name} has no vertices. Delete the object and export again.")
					return errors

				# tangents have to be pre-calculated; this will also calculate loop normal
				try:
					eval_me.calc_tangents(uvmap=eval_me.uv_layers[0].name)
				except RuntimeError:
					raise RuntimeError(
						f"Tangent space calculation for model {b_ob.name} failed. Make sure it has valid geometry")
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
				unweighted_vertices = []
				group_map = {vg.index: bones_names.get(vg.name, -1) for vg in b_ob.vertex_groups}
				for polygon in eval_me.polygons:
					tri = []
					for loop_index in polygon.loop_indices:
						vertex_index = eval_me.loops[loop_index].vertex_index
						co = eval_me.vertices[vertex_index].co
						no = eval_me.loops[loop_index].normal

						bfb_vertex = [(co.x, co.y, co.z), (no.x, no.y, no.z), ]
						if eval_me.vertex_colors:
							col = eval_me.vertex_colors[0].data[loop_index].color
							bfb_vertex += [(int(col.b * 255), int(col.g * 255), int(col.r * 255), int(col.b * 255)), ]
						for uv_layer in eval_me.uv_layers:
							uv_coord = uv_layer.data[loop_index].uv
							bfb_vertex += [(uv_coord.x, 1.0 - uv_coord.y), ]
							if 'T3' in BFRVertex:
								try:
									weight = eval_me.vertices[vertex_index].groups[weight_group_index].weight
								except:
									weight = 0
								bfb_vertex.append(weight)
						key = tuple(bfb_vertex)
						if key not in dummy_vertices:
							dummy_vertices[key] = len(dummy_vertices)
							mesh_vertices.append(key)
							if armature:
								w = []
								for vertex_group in eval_me.vertices[vertex_index].groups:
									# dummy vertex groups without corresponding bones
									try:
										w.append((group_map[vertex_group.group], vertex_group.weight))
									except:
										pass
								w_s = sorted(w, key=lambda x: x[1], reverse=True)[0:4]
								# pad the weight list to 4 bones, ie. add empty bones if missing
								for i in range(0, 4 - len(w_s)):
									w_s.append((-1, 0))
								sw = w_s[0][1] + w_s[1][1] + w_s[2][1] + w_s[3][1]
								if sw > 0.0:
									weights_list.append((w_s[0][0], w_s[1][0], w_s[2][0], w_s[3][0],
														  w_s[0][1] / sw, w_s[1][1] / sw, w_s[2][1] / sw))
								elif vertex_index not in unweighted_vertices:
									unweighted_vertices.append(vertex_index)
						tri.append(dummy_vertices[key])
					mesh_triangles.append(tri)

				if armature:
					ob_2_weights_list[b_ob] = weights_list
				if unweighted_vertices:
					log_error(
						f'Found {len(unweighted_vertices)} unweighted vertices in {b_ob.name}! Add them to vertex groups!')
					return errors
				# does a mesh of this type already exist?
				if BFRVertex not in BFRVertex_2_meshData:
					BFRVertex_2_meshData[BFRVertex] = ([], [], [])
				BFRVertex_2_meshData[BFRVertex][0].append(b_ob)
				BFRVertex_2_meshData[BFRVertex][1].append(mesh_vertices)
				BFRVertex_2_meshData[BFRVertex][2].append(mesh_triangles)

	# 1) create a meshData block for every vertex type we have
	# 2) merge all meshes that use the same vertex type
	# 3) get the counts for creating separate mesh blocks in the next loop
	# 4) increment ID for each meshData
	for BFRVertex, (obs, vertex_lists, triangle_lists) in BFRVertex_2_meshData.items():
		mesh_data_block = bfb.create_block(obs[0].data, bfb, BlockType.MESH_DATA)
		logging.debug(f'Assigned meshID{ID} to BFRVertex{BFRVertex}')
		vertex_offset = 0
		tris_offset = 0
		for b_ob, vertex_list, triangle_list in zip(obs, vertex_lists, triangle_lists):
			num_vertices = len(vertex_list)
			num_triangles = len(triangle_list)
			eval_me = b_ob.data

			center = mathutils.Vector()
			for v in eval_me.vertices:
				center += v.co
			center /= len(eval_me.vertices)
			radius = max([(v.co - center).length for v in eval_me.vertices])

			armature = b_ob.find_armature()
			if armature:
				mesh_block = bfb.create_block(b_ob, bfb, BlockType.MESH_SKINNED)
				# store weights
				weights_list = ob_2_weights_list[b_ob]
				mesh_block.data.num_weights = len(weights_list)
				mesh_block.data.reset_field("weights")
				mesh_block.data.weights[:] = weights_list

				bones = armature.data.bones.values()
				if "!scale!" in bpy.data.actions:
					rest_scale = bpy.data.actions["!scale!"]
					# we have to apply the scale dummy action
					armature.animation_data.action = rest_scale
					scene.frame_set(0)
				else:
					log_error("Rest scale action is missing, assuming rest scale of 1.0 for all bones!")
					rest_scale = None
				# export bones
				mesh_block.data.num_bones = len(bones)
				mesh_block.data.reset_field("bones")
				for b_bone, bfb_bone in zip(bones, mesh_block.data.bones):
					bfb_bone.id = bones.index(b_bone) + 1
					if b_bone.parent:
						bfb_bone.parent_id = bones.index(b_bone.parent) + 1
					else:
						bfb_bone.parent_id = 0
					# rest scale support
					try:
						group = rest_scale.groups[b_bone.name]
						scales = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("scale")]
						scale = scales[0].keyframe_points[0].co[1]
					except:
						scale = 1.0
					# bfb_bone.group = lodgroup
					bfb_bone.name = blendername_to_bfbname(b_bone.name).lower()
					bfb_bone.matrix.set_rows((mathutils.Matrix.Scale(scale, 4) @ get_bfb_matrix(b_bone)).transposed())
			else:
				mesh_block = bfb.create_block(b_ob, bfb, BlockType.MESH)

			# create just 1 chunk
			mesh_chunk = mesh_block.data.chunks[0]
			mesh_chunk.data_id = mesh_data_block.id
			mesh_chunk.tri_index_offset = tris_offset * 3
			mesh_chunk.num_tri_indices = num_triangles * 3
			mesh_chunk.vertex_offset = vertex_offset
			mesh_chunk.vertex_count = num_vertices
			mesh_chunk.num_tris = num_triangles
			mesh_chunk.bounds_extent[:] = center
			mesh_chunk.bounds_radius = radius
			
			vertex_offset += num_vertices
			tris_offset += num_triangles

		# write the meshData block
		mesh_data_block.name = 'meshData'
		mesh_data_block.data.b_f_r_vertex = 'BFRVertex' + BFRVertex
		mesh_data_block.data.vertex_count = vertex_offset
		mesh_data_block.data.verts.set_verts(list(itertools.chain(*vertex_lists)))
		mesh_data_block.data.num_tri_indices = tris_offset * 3
		mesh_data_block.data.reset_field("tris")
		mesh_data_block.data.tris[:] = list(itertools.chain(*triangle_lists))

	bfb.tree = export_tree(b_root, bfb)

	bfb.header.author = author_name
	bfb.header.num_blocks = bfb.header.num_blocks_2 = len(bfb.blocks)
	if not os.path.exists(dirname):
		os.makedirs(dirname)
	bfb.save(filepath)
	# print(bfb)
	logging.info(f'Finished BFB Export in {time.time() - start_time:.2f} seconds')
	return errors


def export_capsule(b_ob, bfb):
	logging.debug('Found capsule collider!')
	me = b_ob.data
	start = (me.vertices[0].co + me.vertices[12].co) / 2
	end = (me.vertices[37].co + me.vertices[49].co) / 2 - start
	radius = ((me.vertices[0].co - me.vertices[12].co) / 2).length
	block = bfb.create_block(b_ob, bfb, BlockType.CAPSULE)
	block.data.start[:] = start
	block.data.end[:] = end
	block.data.radius = radius


def export_bounding_box(b_ob, bfb):
	logging.debug('Found bounding box collider!')
	me = b_ob.data
	block = bfb.create_block(b_ob, bfb, BlockType.BOUNDING_BOX)
	# todo check transpose
	block.data.matrix.set_rows(b_ob.matrix_local.transposed())
	block.data.extent[:] = me.vertices[4].co * 2


def export_sphere(b_ob, bfb):
	logging.debug('Found sphere collider!')
	me = b_ob.data
	block = bfb.create_block(b_ob, bfb, BlockType.SPHERE)
	center = (me.vertices[2].co + me.vertices[23].co) / 2
	block.data.pos[:] = b_ob.location
	block.data.radius = (me.vertices[2].co - center).length
