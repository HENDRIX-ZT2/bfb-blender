import time
import mathutils
import numpy as np

from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType
from modules_import.anim import Animation
from modules_import.armature import import_bones, get_matrix, apply_rest_scale_correction
from modules_import.geometry import ob_postpro, set_auto_smooth_safe
from modules_import.collision import attach_capsule, create_capsule, create_sphere, create_bounding_box
from modules_import.materials import create_material
from util.fast_mesh import FastMesh
from common_bfb import *


anim = Animation()


def import_scene_graph(b_parent, node, lod_level):
	b_ob = None
	matrix = get_matrix(node.matrix)
	logging.info(f"{node.type_id}: {node.name}")
	# ordinary node, node with collision or lod level
	if node.type_id == NodeType.NODE:
		if b_armature_ob and not b_parent:
			b_ob = b_armature_ob
			b_ob.name = node.name
			b_ob.data.name = node.name
			b_ob.matrix_local = matrix
		else:
			b_ob = create_empty(b_parent, node.name, matrix)
		if len(node.collision_ids):
			logging.info(f"collisions: {node.collision_ids}")
			for collision_id in node.collision_ids:
				id2data[collision_id].parent = b_ob
	elif node.type_id == NodeType.LOD_GROUP:
		b_ob = create_empty(b_parent, "lodgroup", matrix)
	elif node.type_id in (NodeType.MESH_LINK, NodeType.BILLBOARD_LINK):
		logging.info(f"geometries: {node.geometry.object_ids}")
		for object_id in node.geometry.object_ids:
			b_ob = id2data[object_id]
			b_ob.name = node.name
			if b_parent:
				b_ob.parent = b_parent
			b_ob.matrix_local = matrix
			for mat_name in node.geometry.materials:
				create_material(b_ob, dir_path, mat_name, anim)
			assign_to_lod(b_ob, lod_level)
			if node.type_id == NodeType.BILLBOARD_LINK:
				global camera
				if not camera:
					camera_data = bpy.data.cameras.new("TrackingCameraData")
					camera = create_ob(bpy.context.scene, "TrackingCamera", camera_data)
					camera.location = (2, -2, 2)
					camera.rotation_euler = (1.047, 0.0, 0.785)
				const = b_ob.constraints.new('COPY_ROTATION')
				const.use_x = False
				const.use_y = False
				const.use_z = True
				const.target = camera
	elif node.type_id == NodeType.CAPSULE_LINK:
		# only in actor meshes
		bone_name = name_import(node.bone_name)
		for collision_id in node.collision_ids:
			b_ob = id2data[collision_id]
			attach_capsule(b_armature_ob, b_ob, bone_name)
	# if we have children, the newly created empty is their parent
	for child in node.children:
		import_scene_graph(b_ob, child, lod_level)
		# if this is a lod level, move next child to its respective layer
		if b_ob.name.startswith("lodgroup"):
			lod_level += 1


def load(reporter, filepath="", use_custom_normals=False, use_mirror_mesh=False, cleanup_geometry=True):
	start_time = time.time()
	global b_armature_ob
	global camera
	global dir_path
	global id2data
	b_armature_ob = None
	camera = None
	dir_path, basename = os.path.split(filepath)
	# used to access data from the BFB by ID
	id2data = {}
	scales = {}
	skinned_meshes = []
	# when no object exists, or when we are in edit mode when script is run
	try:
		bpy.ops.object.mode_set(mode='OBJECT')
	except:
		pass
	logging.info(f"Importing {basename}")
	bfb = BfbFile()
	bfb.load(filepath)
	# print(bfb)
	if bfb.header.version != 4295098369:
		reporter.show_warning(f"Unsupported BFB version: {bfb.header.version}")
	logging.debug(f"BFB Version: {bfb.header.version}")
	logging.debug(f"BFB Author: {bfb.header.author}")
	logging.info("Reading object blocks...")
	for block in bfb.blocks:
		data = block.data
		if block.type_id == BlockType.SPHERE:
			id2data[block.id] = create_sphere(block.name, data.pos.x, data.pos.y, data.pos.z, data.radius)
		elif block.type_id == BlockType.BOUNDING_BOX:
			id2data[block.id] = create_bounding_box(block.name, get_matrix(data.matrix),
													data.extent.x, data.extent.y, data.extent.z)
		elif block.type_id == BlockType.CAPSULE:
			id2data[block.id] = create_capsule(block.name, mathutils.Vector(data.start), mathutils.Vector(data.end), data.radius)
		elif block.type_id == BlockType.MESH_DATA:
			id2data[block.id] = data
		elif block.type_id in (BlockType.MESH, BlockType.MESH_SKINNED):
			mesh_data = id2data[data.data_id]

			if block.type_id == BlockType.MESH_SKINNED:
				if not b_armature_ob:
					b_armature_ob = import_bones(basename, data, scales)
			num_tris = sum(chunk.num_tri_indices // 3 for chunk in data.chunks)
			num_verts = sum(chunk.vertex_count for chunk in data.chunks)
			material_indices = np.empty(shape=num_tris, dtype=int)
			tris = np.empty(shape=(num_tris, 3), dtype=mesh_data.tris.dtype)
			verts = np.empty(shape=num_verts, dtype=mesh_data.verts.verts_data.dtype)
			verts_offset = 0
			tris_offset = 0
			# build mesh from chunks
			for chunk_i, chunk in enumerate(data.chunks):
				num_chunk_tris = chunk.num_tri_indices // 3
				tris[tris_offset: tris_offset + num_chunk_tris] = mesh_data.tris[chunk.tri_index_offset // 3: (chunk.tri_index_offset + chunk.num_tri_indices) // 3]
				tris[tris_offset: tris_offset + num_chunk_tris] += verts_offset
				material_indices[tris_offset: tris_offset + num_chunk_tris] = chunk_i
				verts[verts_offset: verts_offset + chunk.vertex_count] = mesh_data.verts.verts_data[chunk.vertex_offset: chunk.vertex_offset + chunk.vertex_count]
				verts_offset += chunk.vertex_count
				tris_offset += num_chunk_tris

			vertices = verts["pos"].copy()
			material_indices_sorted, sorted_indices, tris_sorted, verts_unique = cleanup_mesh_data(
				material_indices, tris, vertices, cleanup_geometry)

			mesh_tris_flat = tris.flatten()
			b_me = FastMesh.new(block.name)
			b_me.from_pydata(verts_unique, [], tris_sorted)
			b_ob = create_ob(bpy.context.scene, block.name, b_me)
			id2data[block.id] = b_ob
			# Do we have weights for the wind vertex shader? (UVW coordinates if you like)
			# We store them as a vertex group so they can be easily modified.
			if "w" in verts.dtype.fields:
				logging.debug("Found fx_wind weights!")
				b_ob.vertex_groups.new(name="fx_wind")
				for i, vert in enumerate(verts["w"][sorted_indices]):
					b_ob.vertex_groups["fx_wind"].add([i], vert[0], 'REPLACE')

			b_me.polygons.foreach_set('use_smooth', [True] * len(b_me.polygons))
			b_me.polygons.foreach_set('material_index', material_indices_sorted)

			if use_custom_normals:
				set_auto_smooth_safe(b_me)
				b_me.normals_split_custom_set(per_loop(mesh_tris_flat, verts["normal"]))

			for uv_layer in ("u0", "u1", "u2"):
				if uv_layer in verts.dtype.fields:
					b_me.uv_layers.new(name=uv_layer[-1])
					uvs = verts[uv_layer].copy()
					uvs[:, 1] = 1.0 - uvs[:, 1]
					b_me.uv_layers[-1].data.foreach_set("uv", per_loop(mesh_tris_flat, uvs).flatten())
			if "rgba" in verts.dtype.fields:
				rgba = verts["rgba"].astype(float) / 255.0
				cols = b_me.attributes.new(f"RGBA", "BYTE_COLOR", "CORNER")
				cols.data.foreach_set("color", per_loop(mesh_tris_flat, rgba[:, (2, 1, 0, 3)]).flatten())

			if block.type_id == BlockType.MESH_SKINNED:
				bone_names = b_armature_ob.data.bones.keys()
				for i, vert in enumerate([(
						(w.b_0, w.w_0),
						(w.b_1, w.w_1),
						(w.b_2, w.w_2),
						(w.b_3, 1.0 - w.w_0 - w.w_1 - w.w_2)) for w in data.weights[sorted_indices]]):
					for bone_id, weight in vert:
						if bone_id < 255 and weight > 0.0:
							bone_name = bone_names[bone_id]
							if bone_name not in b_ob.vertex_groups:
								b_ob.vertex_groups.new(name=bone_name)
							b_ob.vertex_groups[bone_name].add([i], weight, 'REPLACE')
				skinned_meshes.append(b_ob)
				mod = b_ob.modifiers.new('SkinDeform', 'ARMATURE')
				mod.object = b_armature_ob

			ob_postpro(b_me, use_mirror_mesh)
		logging.debug(f'ID: {block.id} ({block.type_id}) End: {block.end}, Name: {block.name}')

	logging.info("Reading object hierarchy")
	import_scene_graph(None, bfb.tree, 0)

	apply_rest_scale_correction(b_armature_ob, scales, anim, skinned_meshes)

	logging.info(f'Finished BFB Import in {time.time() - start_time:.2f} seconds')


def cleanup_mesh_data(material_indices, tris, vertices, cleanup_geometry):
	if cleanup_geometry:
		verts_unique, unique_indices, unique_inverse = np.unique(vertices, return_index=True, return_inverse=True, axis=0)
		sorted_indices = np.sort(unique_indices)
		verts_unique = vertices[sorted_indices]
		transsort = np.argsort(unique_indices)
		i_rev = transsort.copy()
		i_rev[transsort] = np.arange(len(i_rev))
		unique_inverse = i_rev[unique_inverse]
		tris_sorted = np.take(unique_inverse, tris)
		material_indices_sorted = np.take(unique_inverse, material_indices)
	else:
		sorted_indices = np.arange(len(vertices))
		verts_unique = vertices
		tris_sorted = tris
		material_indices_sorted = material_indices
	return material_indices_sorted, sorted_indices, tris_sorted, verts_unique

