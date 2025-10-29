import itertools
import logging
import os
import time
import bpy
import mathutils

import numpy as np

import batch_bfb
from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType
from common_bfb import create_empty, ensure_active_object, name_export
from modules_export.armature import clear_pose, get_valid_bones, export_bones
from modules_export.collision import export_bounding_box, export_sphere, export_capsule
from modules_export.material import get_mat_names
from util.colors import color_indices, lin_to_srgb


def flatten(mat):
	return [v for row in mat for v in row]


def attach_collision(bfb_node, new_collider_id):
	bfb_node.num_colliders += 1
	colliders = list(bfb_node.collision_ids)
	colliders.append(new_collider_id)
	bfb_node.reset_field("collision_ids")
	bfb_node.collision_ids[:] = colliders


def export_tree(reporter, b_ob, bfb, reuse_vertices, export_materials, export_dir, bfb_parent=None, lod_level=None):
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
			if lod_level in (0, 1):
				bfb_node.unk_0 = 4
				bfb_node.unk_1 = 0
			else:
				bfb_node.unk_0 = 0
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
				reporter.show_warning(f"Capsule collider {b_ob.name} is not parented to a bone.")
			bone_name = name_export(b_ob.parent_bone)
			bfb_node = bfb.create_node(b_ob, bfb, NodeType.CAPSULE_LINK, bfb_parent)
			bfb_node.name = bone_name.lower()
			bfb_node.bone_name = bone_name
			attach_collision(bfb_node, export_capsule(b_ob, bfb))
		else:
			mesh_id = export_mesh(b_ob, bfb, reuse_vertices, lod_level)
			assert mesh_id is not None
			if b_ob.constraints:
				bfb_node = bfb.create_node(b_ob, bfb, NodeType.BILLBOARD_LINK, bfb_parent)
				data = bfb_node.geometry
				data.axis[:] = mathutils.Vector((1.0, 0.0, -1.0))
			else:
				bfb_node = bfb.create_node(b_ob, bfb, NodeType.MESH_LINK, bfb_parent)
				# or 0, 2, or rarely 0, 0
				if lod_level in (0, 1):
					bfb_node.unk_0 = 4
					bfb_node.unk_1 = 0
				else:
					bfb_node.unk_0 = 0
					bfb_node.unk_1 = 0
				bfb_node.name = "editable mesh" if "editable mesh" in b_ob.name else b_ob.name.replace(".", "")
				data = bfb_node.geometry
			data.object_ids[0] = mesh_id
			mat_names = list(get_mat_names(reporter, b_ob, export_dir, export_materials))
			data.num_materials = len(mat_names)
			data.reset_field("materials")
			data.materials[:] = mat_names
	else:
		# lamps etc, just ignore them
		return None
	for i, b_child in enumerate(b_ob.children):
		if b_ob.name.startswith('lodgroup'):
			lod_level = i
		bfb_child = export_tree(reporter, b_child, bfb, reuse_vertices, export_materials, export_dir, bfb_node, lod_level=lod_level)
		if bfb_child:
			bfb_node.children.append(bfb_child)
	return bfb_node


def apply_transform(reporter, ob, ):
	identity = mathutils.Matrix()
	# the world space transform of every rigged mesh must be neutral
	# local space transforms of the mesh and its parents may be different as long as the mesh origin ends up on the b_scene origin
	if ob.matrix_world != identity:
		ob.data.transform(ob.matrix_world)
		ob.matrix_world = identity
		reporter.show_warning(f"{ob.name} has had its transform applied to avoid ingame distortion!")


def export_mesh(b_ob, bfb, reuse_vertices, lod_level):
	b_armature = b_ob.find_armature()
	# we have an armature on one mesh, means we can't export meshes without armature
	if has_armature and not b_armature:
		raise AttributeError(f"{b_ob.name} does not use an armature while other models do")
	if b_armature:
		bones_names = {b_bone.name: i for i, b_bone in enumerate(get_valid_bones(b_armature))}
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
	mesh_chunks = {}
	# used to ignore the normals for checking equality
	dummy_vertices = {}

	weights_list = []

	weight_group_index = b_ob.vertex_groups['fx_wind'].index if 'fx_wind' in b_ob.vertex_groups else None
	# get from property or guess if missing
	BFRVertex = b_ob.data.get("BFRVertex")
	if not BFRVertex:
		BFRVertex = guess_bfr(b_ob, eval_me)
	if eval_me.color_attributes:
		colors = np.empty(len(eval_me.loops) * 4, np.float32)
		eval_me.color_attributes[0].data.foreach_get('color', colors)
		colors = colors.reshape((len(eval_me.loops), 4))
		# legacy vertex_colors api converted the color to srgb float
		# attributes api must manually use lin_to_srgb
		lin_to_srgb(colors)
		colors = np.round(colors[:, color_indices] * 255)
	# select all verts without weights
	unweighted_vertices = set()
	group_map = {vg.index: bones_names.get(vg.name, -1) for vg in b_ob.vertex_groups}
	for polygon in eval_me.polygons:
		# split by material index
		if polygon.material_index not in mesh_chunks:
			mesh_chunks[polygon.material_index] = []
		chunk_triangles = mesh_chunks[polygon.material_index]
		tri = []
		for loop_index in polygon.loop_indices:
			vertex_index = eval_me.loops[loop_index].vertex_index
			vertex = eval_me.vertices[vertex_index]
			co = vertex.co
			no = eval_me.loops[loop_index].normal

			bfb_vertex = [(co.x, co.y, co.z), (no.x, no.y, no.z), ]
			if eval_me.color_attributes:
				bfb_vertex.append(tuple(colors[loop_index]))
			for uv_layer in eval_me.uv_layers:
				uv_coord = uv_layer.data[loop_index].uv
				bfb_vertex.append((uv_coord.x, 1.0 - uv_coord.y))
				if weight_group_index is not None:
					try:
						weight = vertex.groups[weight_group_index].weight
					except:
						weight = 0.0
					bfb_vertex.append(weight)
			# unedited vertex normal
			if 'T3D' in BFRVertex:
				no2 = vertex.normal
				bfb_vertex.append((no2.x, no2.y, no2.z))

			key = tuple(bfb_vertex)
			if not reuse_vertices or key not in dummy_vertices:
				dummy_vertices[key] = len(mesh_vertices)
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
		chunk_triangles.append(tri)

	if unweighted_vertices:
		raise AttributeError(
			f'Found {len(unweighted_vertices)} unweighted vertices in {b_ob.name}! Add them to vertex groups!')
	
	is_lod0 = lod_level == 0
	vertex_key_tuple = (BFRVertex, is_lod0)
	if vertex_key_tuple not in BFRVertex_2_meshData:
		mesh_data_block = bfb.create_block(b_ob.data, bfb, BlockType.MESH_DATA)
		mesh_data_block.name = "meshData"
		mesh_data_block.data.b_f_r_vertex = f"BFRVertex{BFRVertex}"
		mesh_data_block.data.flag = 10 if is_lod0 else 8
		mesh_data_block.users = []
		mesh_data_block.vertex_lists = []
		mesh_data_block.chunks_lists = []
		BFRVertex_2_meshData[vertex_key_tuple] = mesh_data_block
	else:
		mesh_data_block = BFRVertex_2_meshData[vertex_key_tuple]

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
	mesh_block.data.flag = 2 if is_lod0 else 0
	mesh_block.name = "mesh"
	mesh_data_block.users.append(mesh_block)
	mesh_data_block.vertex_lists.append(mesh_vertices)
	mesh_data_block.chunks_lists.append([mesh_chunks[i] for i in sorted(mesh_chunks.keys())])
	return mesh_block.id


def guess_bfr(b_ob, eval_me):
	BFRVertex = 'PN'
	if eval_me.color_attributes:
		BFRVertex += 'D'
	for i in range(len(eval_me.uv_layers)):
		if 'fx_wind' in b_ob.vertex_groups:
			BFRVertex += f'T3{i}'
		else:
			BFRVertex += f'T{i}'
	logging.warning(f"Guessing BFRVertex for {b_ob.name} as {BFRVertex}")
	return BFRVertex


def save(reporter, filepath='', author_name="HENDRIX", reuse_vertices=True, export_materials=True, create_lods=False,
		 num_lods=1, rate=1):
	if create_lods:
		logging.info('Adding LODs')
		batch_bfb.add_lods(num_lods, rate)

	logging.info(f'Exporting {filepath}')
	ensure_active_object()

	export_dir = os.path.dirname(filepath)
	if not os.path.exists(export_dir):
		os.makedirs(export_dir)
	bfb = BfbFile()
	bfb.header.version[:] = (1, 2, 1, 0)

	# if one model uses an armature, all have to. If they don't, they can't be exported.
	global has_armature
	has_armature = False
	global b_scale_action
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
			b_armature_ob = b_ob.find_armature()
			if b_armature_ob:
				apply_transform(reporter, b_ob)
				has_armature = True
				clear_pose(b_armature_ob)
				# apply the scale dummy action
				if "!scale!" in bpy.data.actions:
					b_scale_action = bpy.data.actions["!scale!"]
					b_armature_ob.animation_data.action = b_scale_action
					b_scene.frame_set(0)
				else:
					logging.warning("Rest scale action is missing, assuming rest scale of 1.0 for all bones!")
					b_scale_action = None
			# fix meshes parented to a bone by adding vgroups
			if b_ob.parent_type == "BONE" and not b_ob.name.startswith('capsule'):
				reporter.show_warning(
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
				apply_transform(reporter, b_ob)

	bfb.tree = export_tree(reporter, b_root, bfb, reuse_vertices, export_materials, export_dir)

	for (BFRVertex, is_lod0), mesh_data_block in BFRVertex_2_meshData.items():
		logging.debug(f'Filling in BFRVertex{BFRVertex} (is_lod0={is_lod0})')

		# fill in the meshData block
		verts = join_lists(mesh_data_block.vertex_lists)
		chunks = [join_lists(chunk) for chunk in mesh_data_block.chunks_lists]
		mesh_data_block.data.verts.set_verts(verts)
		mesh_data_block.data.vertex_count = len(verts)
		mesh_data_block.data.num_tri_indices = sum(len(tris) for tris in chunks) * 3
		mesh_data_block.data.reset_field("tris")
		mesh_data_block.data.tris[:] =  list(itertools.chain(*chunks))
		# index into mesh_data_block
		vertex_offset = 0
		tris_offset = 0
		for mesh_block, vertex_list, chunks_list in zip(mesh_data_block.users, mesh_data_block.vertex_lists, mesh_data_block.chunks_lists):
			# create just 1 chunk
			mesh_block.data.num_chunks = len(chunks_list)
			mesh_block.data.reset_field("chunks")
			for chunk, triangle_list in zip(mesh_block.data.chunks, chunks_list):
				chunk.vertex_offset = vertex_offset
				chunk.vertex_count = len(vertex_list)
				chunk.num_tris = len(triangle_list)
				chunk.tri_index_offset = tris_offset * 3
				chunk.num_tri_indices = chunk.num_tris * 3
				chunk_verts = mesh_data_block.data.verts.verts_data[chunk.vertex_offset: chunk.vertex_offset + chunk.vertex_count]["pos"]
				cog = np.mean(chunk_verts, axis=0)
				chunk.bounds_cog[:] = cog
				chunk.bounds_radius = np.max(np.linalg.norm(chunk_verts-cog, axis=1))

				tris_offset += chunk.num_tris
			vertex_offset += chunk.vertex_count

	bfb.header.author = author_name
	bfb.header.num_blocks = len(bfb.blocks)
	bfb.header.num_nodes = len(bfb.tree.get_children([])) + 1
	bfb.blocks.sort(key=lambda block: sort_id(block))
	bfb.save(filepath)
	# print(bfb)
	logging.info(f'Finished BFB Export in {time.time() - start_time:.2f} seconds')

def sort_id(block):
	# mesh data first, rest in descending order of type_id
	type_id = block.type_id
	if type_id == 6:
		type_id = -99
	else:
		type_id = -type_id
	# sorting for flag is not consistent in original
	flag = block.data.flag if hasattr(block.data, 'flag') else 0
	return type_id, flag

def join_lists(lists):
	return list(itertools.chain(*lists))


