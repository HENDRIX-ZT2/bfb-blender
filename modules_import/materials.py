import logging

import bpy
import mathutils

from bfmat import Bfmat
from util import node_util, node_arrange


def create_material(b_ob, dir_path, mat_name, anim):
	logging.info(f"MATERIAL: {mat_name}")
	# only create the material if we haven't already created it, then just grab it
	if mat_name not in bpy.data.materials:
		b_mat = bpy.data.materials.new(mat_name)
		b_mat.use_nodes = True
		try:
			bfmat = Bfmat(dir_path, f"{mat_name}.bfmat")
			for error in bfmat.errors:
				logging.warning(error)
			if not bfmat.root:
				return
			fx = bfmat.fx
			cull_mode = bfmat.CullMode
			alpha_ref = bfmat.AlphaRef
			fps = bpy.context.scene.render.fps

			# see which sub-shaders are used by this fx shader, and get the used ones in order
			shaders = ("Base", "Dark", "Decal", "Detail", "Gloss", "Glow", "Reflect")
			tex_shaders = [name for i, name in sorted(zip([fx.find(s) for s in shaders], shaders)) if i > -1]


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
		except Exception as error:
			logging.exception(f"material failed")
	else:
		b_mat = bpy.data.materials[mat_name]
	me = b_ob.data
	me.materials.append(b_mat)
