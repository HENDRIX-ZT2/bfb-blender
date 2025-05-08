import logging
import os
import time
import bpy
import mathutils

from bfb_gen.formats.bfb import BfbFile
from bfb_gen.formats.bfb.enums.BlockType import BlockType
from bfb_gen.formats.bfb.enums.NodeType import NodeType
from modules_import.anim import Animation
from modules_import.geometry import ob_postpro, set_auto_smooth_safe
from util.fast_mesh import FastMesh
from .common_bfb import *
from .bfmat import Bfmat
from .util import node_arrange, node_util


def log_error(error):
	logging.warning(error)
	global errors
	errors.append(error)


anim = Animation()


def get_matrix(matrix):
	matrix = mathutils.Matrix(matrix.data)
	matrix.transpose()
	return matrix

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
		for collision_id in node.data.collision_ids:
			id2data[collision_id].parent = b_ob
	elif node.type_id == NodeType.LOD_GROUP:
		b_ob = create_empty(b_parent, "lodgroup", matrix)
	elif node.type_id == NodeType.MESH_LINK:
		for object_id in node.data.object_ids:
			b_ob = id2data[object_id]
			b_ob.name = node.name
			if b_parent:
				b_ob.parent = b_parent
			b_ob.matrix_local = matrix
			for mat_name in node.data.materials:
				create_material(b_ob, mat_name, anim)
			assign_to_lod(b_ob, lod_level)
	elif node.type_id == NodeType.BILLBOARD_LINK:
		global camera
		if not camera:
			camera_data = bpy.data.cameras.new("TrackingCameraData")
			camera = create_ob("TrackingCamera", camera_data)
			camera.location = (2, -2, 2)
			camera.rotation_euler = (1.047, 0.0, 0.785)
		b_ob = id2data[node.data.object_id]
		b_ob.name = node.name
		b_ob.matrix_local = matrix
		b_ob.parent = node
		create_material(b_ob, node.data.material, anim)
		assign_to_lod(b_ob, lod_level)
		const = b_ob.constraints.new('COPY_ROTATION')
		const.use_x = False
		const.use_y = False
		const.use_z = True
		const.target = camera
	elif node.type_id == NodeType.CAPSULE_LINK:
		# only in actor meshes
		bone_name = name_import(node.data.bone_name)
		b_ob = id2data[node.data.collision_id]
		b_ob.parent = b_armature_ob
		b_ob.parent_bone = bone_name
		b_ob.parent_type = 'BONE'
		try:
			b_ob.location.y = -b_armature_ob.data.bones[bone_name].length
		except:
			b_ob.parent_bone = "Bip01"
			log_error(f"Capsule collider {node.name} has no parent bone, set to Bip01!")
	# if we have children, the newly created empty is their parent
	for child in reversed(node.children):
		import_scene_graph(b_ob, child, lod_level)
		# if this is a lod level, move next child to its respective layer
		if b_ob.name.startswith("lodgroup"):
			lod_level += 1


def create_material(b_ob, mat_name, anim):
	try:
		bfmat = Bfmat(dirname, f"{mat_name}.bfmat")
		for error in bfmat.errors:
			log_error(error)
	except Exception as error:
		log_error(str(error))
		return
	if not bfmat.root:
		return
	fx = bfmat.fx
	cull_mode = bfmat.CullMode
	alpha_ref = bfmat.AlphaRef
	fps = bpy.context.scene.render.fps

	# see which sub-shaders are used by this fx shader, and get the used ones in order
	shaders = ("Base", "Decal", "Detail", "Gloss", "Glow", "Reflect")
	tex_shaders = [name for i, name in sorted(zip([fx.find(s) for s in shaders], shaders)) if i > -1]

	logging.info(f"MATERIAL: {mat_name}")
	# only create the material if we haven't already created it, then just grab it
	if mat_name not in bpy.data.materials:
		b_mat = bpy.data.materials.new(mat_name)
		b_mat.use_nodes = True

		tree = b_mat.node_tree
		# clear default nodes
		for node in tree.nodes:
			tree.nodes.remove(node)
		output = tree.nodes.new('ShaderNodeOutputMaterial')
		output.label = fx
		# principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
		shader_diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
		diffuse = None

		textures = []
		for i, (texture, tex_index, tex_transform, tex_anim) in enumerate(
				zip(bfmat.Texture, bfmat.TexCoordIndex, bfmat.TextureTransform, bfmat.TextureAnimation)):
			if texture is not None:
				tex = node_util.load_tex_node(tree, bfmat.find_recursive(texture + ".dds"))
				textures.append(tex)
				tex.name = "Texture" + str(i)
				# e.g. African violets, but only in rendered view; but: glacier
				tex.extension = "CLIP" if (cull_mode == "2" and not (
						bfmat.AlphaTestEnable is False and bfmat.AlphaBlendEnable is False)) else "REPEAT"
				# use generated UV coords for reflection maps
				if tex_shaders[i] == "Reflect":
					uv = tree.nodes.new('ShaderNodeTexCoord')
					tree.links.new(uv.outputs[6], tex.inputs[0])
				# use supplied UV maps for everything else, if present
				else:
					uv = tree.nodes.new('ShaderNodeUVMap')
					uv.name = f"TexCoordIndex{i}"
					uv.uv_map = tex_index if tex_index else str(i)
					if tex_transform or tex_anim:
						transform = tree.nodes.new('ShaderNodeMapping')
						transform.name = f"TextureTransform{i}"
						if tex_transform:
							matrix_4x4 = mathutils.Matrix(tex_transform)
							transform.inputs["Scale"].default_value = matrix_4x4.to_scale()
							transform.inputs["Rotation"].default_value = matrix_4x4.to_euler()
							loc = matrix_4x4.to_translation()
							# negate V coordinate
							loc.y *= -1.0
							transform.inputs["Location"].default_value = loc
						if tex_anim:
							b_action = anim.create_action(tree, f"{b_mat.name}_Action")
							u = tex_anim["offsetu"]
							v = tex_anim["offsetv"]
							anim.add_keys(b_action, transform.name, (0,), None, [k[0] * fps for k in u], [k[1] for k in u], None, n_node_input=1)
							anim.add_keys(b_action, transform.name, (1,), None, [k[0] * fps for k in v], [-k[1] for k in v], None, n_node_input=1)
						tree.links.new(uv.outputs[0], transform.inputs[0])
						tree.links.new(transform.outputs[0], tex.inputs[0])
					else:
						tree.links.new(uv.outputs[0], tex.inputs[0])
				tex.update()
		# gather & premix all diffuse colors into one RGB color to plug into the shader
		if textures:
			diffuse = textures[0]
			for texture, tex_shader in zip(textures, tex_shaders):
				if tex_shader in ("Detail", "Decal", "Reflect"):
					mixRGB = tree.nodes.new('ShaderNodeMixRGB')
					if tex_shader == "Decal":
						tree.links.new(texture.outputs[1], mixRGB.inputs[0])
					elif tex_shader in ("Detail", "Reflect"):
						mixRGB.inputs[0].default_value = 1
						mixRGB.blend_type = "OVERLAY"
					tree.links.new(diffuse.outputs[0], mixRGB.inputs[1])
					tree.links.new(texture.outputs[0], mixRGB.inputs[2])
					diffuse = mixRGB
		if b_ob.data.vertex_colors:
			vcol = tree.nodes.new('ShaderNodeAttribute')
			vcol.attribute_name = "RGBA"
			mixRGB = tree.nodes.new('ShaderNodeMixRGB')
			mixRGB.inputs[0].default_value = 1
			mixRGB.blend_type = "OVERLAY"
			if textures:
				tree.links.new(diffuse.outputs[0], mixRGB.inputs[1])
				tree.links.new(vcol.outputs["Color"], mixRGB.inputs[2])
				diffuse = mixRGB
			# fallback for missing texture
			else:
				diffuse = vcol
		if diffuse:
			tree.links.new(diffuse.outputs[0], shader_diffuse.inputs[0])

		# glow / emit
		for texture, tex_shader in zip(textures, tex_shaders):
			if tex_shader == "Glow":
				# create a glow shader and link this texture to it
				shader_glow = tree.nodes.new('ShaderNodeEmission')
				tree.links.new(texture.outputs[0], shader_glow.inputs[0])
				tree.links.new(texture.outputs[1], shader_glow.inputs[1])
				# now add glow to diffuse shader with an add shader
				shader_add = tree.nodes.new('ShaderNodeAddShader')
				tree.links.new(shader_diffuse.outputs[0], shader_add.inputs[0])
				tree.links.new(shader_glow.outputs[0], shader_add.inputs[1])
				shader_diffuse = shader_add

		# transparency
		if bfmat.AlphaTestEnable is False and bfmat.AlphaBlendEnable is False:
			b_mat.blend_method = "OPAQUE"
			tree.links.new(shader_diffuse.outputs[0], output.inputs[0])
		else:
			if bfmat.AlphaTestEnable:
				b_mat.blend_method = "CLIP"
				b_mat.alpha_threshold = 1 - float(alpha_ref) / 255
			if bfmat.AlphaBlendEnable:
				b_mat.blend_method = "BLEND"
			transp = tree.nodes.new('ShaderNodeBsdfTransparent')
			alpha_mixer = tree.nodes.new('ShaderNodeMixShader')

			if textures and b_ob.data.vertex_colors:
				mix_rgba = tree.nodes.new('ShaderNodeMixRGB')
				mix_rgba.inputs[0].default_value = 1
				mix_rgba.blend_type = "MULTIPLY"
				tree.links.new(textures[0].outputs[1], mix_rgba.inputs[1])
				tree.links.new(vcol.outputs["Alpha"], mix_rgba.inputs[2])
				tree.links.new(mix_rgba.outputs[0], alpha_mixer.inputs[0])
			elif textures:
				tree.links.new(textures[0].outputs[1], alpha_mixer.inputs[0])
			elif b_ob.data.vertex_colors:
				tree.links.new(vcol.outputs["Alpha"], alpha_mixer.inputs[0])

			tree.links.new(transp.outputs[0], alpha_mixer.inputs[1])
			tree.links.new(shader_diffuse.outputs[0], alpha_mixer.inputs[2])
			tree.links.new(alpha_mixer.outputs[0], output.inputs[0])

		node_arrange.nodes_iterate(tree, output)
		# finally, set interpolation and extrapolation for all fcurves we have created
		if tree.animation_data:
			for fcu in tree.animation_data.action.fcurves:
				for k in fcu.keyframe_points:
					k.interpolation = 'LINEAR'
				mod = fcu.modifiers.new('CYCLES')
				mod.mode_after = 'REPEAT_OFFSET'
				mod.mode_before = 'REPEAT_OFFSET'
	else:
		b_mat = bpy.data.materials[mat_name]

	# now finally set all the textures we have in the mesh
	me = b_ob.data
	me.materials.append(b_mat)


def load(operator, context, filepath="", use_custom_normals=False, use_mirror_mesh=False):
	start_time = time.time()
	global errors
	errors = []
	global b_armature_ob
	global camera
	global dirname
	global id2data
	b_armature_ob = None
	camera = None
	dirname, basename = os.path.split(filepath)
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
		log_error(f"Unsupported BFB version: {bfb.header.version}")
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
			id2data[block.id] = create_capsule(block.name, mathutils.Vector(data.start),
											   mathutils.Vector(data.end), data.radius)
		elif block.type_id == BlockType.MESH_DATA:
			id2data[block.id] = data
		elif block.type_id in (BlockType.MESH, BlockType.MESH_SKINNED):
			mesh_data = id2data[data.data_id]

			if block.type_id == BlockType.MESH_SKINNED:
				if not b_armature_ob:
					import_bones(basename, data, scales)
			# build mesh
			for chunk_i, chunk in enumerate(data.chunks):
				tris = mesh_data.tris[chunk.tri_index_offset // 3: (chunk.tri_index_offset + chunk.num_tri_indices) // 3]
				verts = mesh_data.verts.verts_data[chunk.vertex_offset: chunk.vertex_offset + chunk.vertex_count]

				vertices = verts["pos"].copy()
				verts_unique, unique_indices, unique_inverse = np.unique(vertices, return_index=True, return_inverse=True, axis=0)
				sorted_indices = np.sort(unique_indices)
				verts_unique = vertices[sorted_indices]
				transsort = np.argsort(unique_indices)
				i_rev = transsort.copy()
				i_rev[transsort] = np.arange(len(i_rev))
				unique_inverse = i_rev[unique_inverse]
				tris_sorted = np.take(unique_inverse, tris)
				mesh_tris_flat = tris.flatten()

				b_me = FastMesh.new(block.name)
				b_me.from_pydata(verts_unique, [], tris_sorted)
				ob = create_ob(block.name, b_me)
				id2data[block.id] = ob
				# Do we have weights for the wind vertex shader? (UVW coordinates if you like)
				# We store them as a vertex group so they can be easily modified.
				if "w" in verts.dtype.fields:
					logging.debug("Found fx_wind weights!")
					ob.vertex_groups.new(name="fx_wind")
					for i, vert in enumerate(verts["w"][sorted_indices]):
						ob.vertex_groups["fx_wind"].add([i], vert[0], 'REPLACE')

				b_me.polygons.foreach_set('use_smooth', [True] * len(b_me.polygons))
				for face in b_me.polygons:
					face.material_index = 0

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
								if bone_name not in ob.vertex_groups:
									ob.vertex_groups.new(name=bone_name)
								ob.vertex_groups[bone_name].add([i], weight, 'REPLACE')
					skinned_meshes.append(ob)
					mod = ob.modifiers.new('SkinDeform', 'ARMATURE')
					mod.object = b_armature_ob

			ob_postpro(use_mirror_mesh)
		logging.debug(f'ID: {block.id} ({block.type_id}) End: {block.end}, Name: {block.name}')

	logging.info("Reading object hierarchy")
	import_scene_graph(None, bfb.tree, 0)

	apply_rest_scale_correction(b_armature_ob, context, scales, skinned_meshes)

	logging.info(f'Finished BFB Import in {time.time() - start_time:.2f} seconds')
	return errors


def apply_rest_scale_correction(b_armature_ob, context, scales, skinned_meshes):
	# handle scale on armature and meshes
	if b_armature_ob and scales:
		# set inverse scale to all bones
		for bone_name, scale in scales.items():
			p_bone = b_armature_ob.pose.bones[bone_name]
			p_bone.matrix_basis = mathutils.Matrix.Scale(1 / scale, 4)
		depsgraph = context.evaluated_depsgraph_get()
		# apply skin deformation
		for ob in skinned_meshes:
			object_eval = ob.evaluated_get(depsgraph)
			ob.data = bpy.data.meshes.new_from_object(object_eval)
		# remove scales from armature
		bpy.context.view_layer.objects.active = b_armature_ob
		bpy.ops.object.mode_set(mode='POSE')
		bpy.ops.pose.armature_apply()
		bpy.ops.object.mode_set(mode='OBJECT')
		# add scale back in as dummy action
		scale_action = create_anim(b_armature_ob, "!scale!")
		for bone_name, scale in scales.items():
			fcurves = [scale_action.fcurves.new(data_path=f'pose.bones["{bone_name}"].scale', index=i,
												action_group=bone_name) for i in range(3)]
			for fcurve in fcurves:
				fcurve.keyframe_points.insert(0, scale)


def import_bones(basename, data, scales):
	global b_armature_ob
	# create the b_armature_ob
	b_armature_data = bpy.data.armatures.new(basename[:-4])
	b_armature_data.show_axes = True
	b_armature_data.display_type = 'STICK'
	b_armature_ob = create_ob(basename[:-4], b_armature_data)
	b_armature_ob.show_in_front = True
	bpy.ops.object.mode_set(mode='EDIT')
	mat_storage = {}
	for bfb_bone in data.bones:
		bone_name = name_import(bfb_bone.name)
		bind = get_matrix(bfb_bone.matrix)
		# support for bone scale
		scale = bind.to_scale()[0]
		if int(round(scale * 1000)) != 1000:
			scales[bone_name] = scale
		# create a bone
		b_edit_bone = b_armature_data.edit_bones.new(bone_name)
		# parent it and get the armature space matrix
		if bfb_bone.parent_id > 0:
			# calculate bfb armature space matrix
			bind = mat_storage[bfb_bone.parent_id] @ bind
			b_edit_bone.parent = b_armature_data.edit_bones[bfb_bone.parent_id - 1]
		# we store the bfb space armature matrix of each bone
		mat_storage[bfb_bone.id] = bind.copy()
		# set transformation
		bind = correction_global @ correction_local @ bind @ correction_local.inverted()
		tail, roll = bpy.types.Bone.AxisRollFromMatrix(bind.to_3x3())
		b_edit_bone.head = bind.to_translation()
		b_edit_bone.tail = tail + b_edit_bone.head
		b_edit_bone.roll = roll
	# fix the bone length
	for edit_bone in b_armature_data.edit_bones:
		fix_bone_length(edit_bone)
	bpy.ops.object.mode_set(mode='OBJECT')
	# group
	for bfb_bone in data.bones:
		bone_name = name_import(bfb_bone.name)
		p_bone = b_armature_ob.pose.bones[bone_name]
		p_bone["group"] = bfb_bone.group
