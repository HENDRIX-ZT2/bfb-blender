import os
import time
import bpy
import mathutils
from struct import iter_unpack, unpack_from
from .common_bfb import *
from .bfmat import bfmat
from .util.node_arrange import nodes_iterate
from .util.node_util import *

def getstring128(x): return datastream[x:x+128].rstrip(b"\x00").decode("utf-8")
def getint(x): return unpack_from('i',datastream, x)[0]
def get_matrix(x): return mathutils.Matrix(list(iter_unpack('4f',datastream[x:x+64])))

def log_error(error):
	print(error)
	global errors
	errors.append(error)

def read_linked_list(pos, parent, level):
	blockid, typeid, childstart, nextblockstart, u_cha, name = unpack_from("=4i b 64s", datastream, pos)
	name = name.rstrip(b"\x00").decode("utf-8")
	matrix = get_matrix(pos+81)
	matrix.transpose()
	#ordinary node, node with collision or lod level
	if typeid == 1:
		print("NODE:",name)
		if armature and not parent:
			ob = armature
			ob.name = name
			ob.data.name = name
			ob.matrix_local = matrix
		else:
			ob = create_empty(parent, name, matrix)
		hascollision = getint(pos+153)
		if hascollision == 1:
			id2data[getint(pos+157)].parent = ob
	#lod group
	elif typeid == 2:
		print("LOD GROUP:",name)
		ob = create_empty(parent, "lodgroup", matrix)
	#mesh linker
	elif typeid == 3:
		print("MESH LINK:",name)
		objID = getint(pos+161)
		matname = getstring128(pos+169)
		ob = id2data[objID]
		ob.name = name
		if parent:
			ob.parent = parent
		ob.matrix_local = matrix
		create_material(ob,matname)
		LOD(ob, level)
	elif typeid == 4:
		print("BILLBOARD:",name)
		global camera
		if not camera:
			camera_data = bpy.data.cameras.new("TrackingCameraData")
			camera = create_ob("TrackingCamera", camera_data)
			camera.location = (2,-2,2)
			camera.rotation_euler = (1.047,0.0,0.785)
		hasobj = getint(pos+157)
		objID = getint(pos+185)
		matname = getstring128(pos+189)
		ob = id2data[objID]
		ob.name = name
		ob.matrix_local = matrix
		ob.parent = parent
		create_material(ob,matname)
		LOD(ob, level)
		const = ob.constraints.new('COPY_ROTATION')
		const.use_x = False
		const.use_y = False
		const.use_z = True
		const.target = camera
	#capsule collider link, only in actor meshes
	elif typeid == 5:
		collisionid = getint(pos+157)
		#case-sensitive name
		bone_name = bfbname_to_blendername(datastream[pos+161:pos+161+64])
		ob = id2data[collisionid]
		ob.parent = armature
		ob.parent_bone = bone_name
		ob.parent_type = 'BONE'
		try:
			ob.location.y = -armature.data.bones[bone_name].length
		except:
			ob.parent_bone = "Bip01"
			log_error("Capsule collider "+name+" has no parent bone, set to Bip01!")
		print("CAPSULE COLLIDER:",bone_name)
	else:
		print("Unknown type ID",typeid,"in block links!")
	#if we have children, the newly created empty is their parent
	if childstart!= 0:
		pos = childstart
		read_linked_list(pos,ob,level)
	#if this is a lod level, move it to its respective layer
	if parent and parent.name.startswith("lodgroup"):
		level+= 1
	#for the next block, the old empty is the parent
	if nextblockstart!= 0:
		pos = nextblockstart
		read_linked_list(pos,parent,level)

def create_material(ob, matname):
	material = bfmat(dirname, matname+".bfmat")
	for error in material.errors:
		log_error(error)
	if not material.root: return
	fx = material.fx
	cull_mode = material.CullMode
	alpha_ref = material.AlphaRef
	fps = bpy.context.scene.render.fps
	
	#see which sub-shaders are used by this fx shader, and get the used ones in order
	shaders = ("Base", "Decal", "Detail", "Gloss", "Glow", "Reflect")
	tex_shaders = [name for i, name in sorted(zip([fx.find(s) for s in shaders], shaders)) if i > -1]
	
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
		mat.use_nodes = True
		
		tree = mat.node_tree
		# clear default nodes
		for node in tree.nodes:
			tree.nodes.remove(node)
		output = tree.nodes.new('ShaderNodeOutputMaterial')
		output.label = fx
		# principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
		shader_diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
		diffuse = None
		
		textures = []
		for i, (texture, tex_index, tex_transform, tex_anim) in enumerate( zip(material.Texture, material.TexCoordIndex, material.TextureTransform, material.TextureAnimation) ):
			if texture is not None:
				tex = load_tex(tree, material.find_recursive(texture+".dds"))
				textures.append(tex)
				tex.name = "Texture"+str(i)
				# #eg. African violets, but only in rendered view; but: glacier
				tex.extension = "CLIP" if (cull_mode == "2" and not (material.AlphaTestEnable is False and material.AlphaBlendEnable is False) ) else "REPEAT"
				# use generated UV coords for reflection maps
				if tex_shaders[i] == "Reflect":
					uv = tree.nodes.new('ShaderNodeTexCoord')
					tree.links.new(uv.outputs[6], tex.inputs[0])
				# use supplied UV maps for everything else, if present
				else:
					uv = tree.nodes.new('ShaderNodeUVMap')
					uv.name = "TexCoordIndex"+str(i)
					uv.uv_map = tex_index if tex_index else str(i)
					if tex_transform or tex_anim:
						transform = tree.nodes.new('ShaderNodeMapping')
						#todo: negate V coordinate
						if tex_transform: 
							matrix_4x4 = mathutils.Matrix(tex_transform)
							transform.scale = matrix_4x4.to_scale()
							transform.rotation = matrix_4x4.to_euler()
							transform.translation = matrix_4x4.to_translation()
							transform.name = "TextureTransform"+str(i)
						if tex_anim:
							for j, dtype in enumerate( ("offsetu", "offsetv") ):
								for key in tex_anim[dtype]:
									transform.translation[j] = key[1]
									#note that since we are dealing with UV coordinates, V has to be negated
									if j == 1: transform.translation[j] *= -1
									transform.keyframe_insert("translation", index = j, frame = int(key[0]*fps))
						tree.links.new(uv.outputs[0], transform.inputs[0])
						tree.links.new(transform.outputs[0], tex.inputs[0])
					else:
						tree.links.new(uv.outputs[0], tex.inputs[0])
				tex.update()
		#gather & premix all diffuse colors into one RGB color to plug into the shader
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
		if ob.data.vertex_colors:
			vcol = tree.nodes.new('ShaderNodeAttribute')
			vcol.attribute_name = "RGB"
			mixRGB = tree.nodes.new('ShaderNodeMixRGB')
			mixRGB.inputs[0].default_value = 1
			mixRGB.blend_type = "OVERLAY"
			if textures:
				tree.links.new(diffuse.outputs[0], mixRGB.inputs[1])
				tree.links.new(vcol.outputs[0], mixRGB.inputs[2])
				diffuse = mixRGB
			#fallback for missing texture
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
				#now add glow to diffuse shader with an add shader
				shader_add = tree.nodes.new('ShaderNodeAddShader')
				tree.links.new(shader_diffuse.outputs[0], shader_add.inputs[0])
				tree.links.new(shader_glow.outputs[0], shader_add.inputs[1])
				shader_diffuse = shader_add
		
		#transparency
		if material.AlphaTestEnable is False and material.AlphaBlendEnable is False:
			mat.blend_method = "OPAQUE"
			tree.links.new(shader_diffuse.outputs[0], output.inputs[0])
		else:
			if material.AlphaTestEnable:
				mat.blend_method = "CLIP"
				mat.alpha_threshold = 1 - float(alpha_ref) /255
			if material.AlphaBlendEnable:
				mat.blend_method = "BLEND"
			transp = tree.nodes.new('ShaderNodeBsdfTransparent')
			alpha_mixer = tree.nodes.new('ShaderNodeMixShader')
			
			if textures and ob.data.vertex_colors:
				vcol = tree.nodes.new('ShaderNodeAttribute')
				vcol.attribute_name = "AAA"
				mixAAA = tree.nodes.new('ShaderNodeMixRGB')
				mixAAA.inputs[0].default_value = 1
				mixAAA.blend_type = "MULTIPLY"
				tree.links.new(textures[0].outputs[1],	mixAAA.inputs[1])
				tree.links.new(vcol.outputs[0], 		mixAAA.inputs[2])
				tree.links.new(mixAAA.outputs[0],		alpha_mixer.inputs[0])
			elif textures:
				tree.links.new(textures[0].outputs[1],	alpha_mixer.inputs[0])
			elif ob.data.vertex_colors:
				vcol = tree.nodes.new('ShaderNodeAttribute')
				vcol.attribute_name = "AAA"
				tree.links.new(vcol.outputs[0],			alpha_mixer.inputs[0])
				
			tree.links.new(transp.outputs[0],			alpha_mixer.inputs[1])
			tree.links.new(shader_diffuse.outputs[0],	alpha_mixer.inputs[2])
			tree.links.new(alpha_mixer.outputs[0],		output.inputs[0])
			
		nodes_iterate(tree, output)
		#finally, set interpolation and extrapolation for all fcurves we have created
		if tree.animation_data:
			for fcu in tree.animation_data.action.fcurves:
				for k in fcu.keyframe_points:
					k.interpolation = 'LINEAR'
				mod = fcu.modifiers.new('CYCLES')
				mod.mode_after = 'REPEAT_OFFSET'
				mod.mode_before = 'REPEAT_OFFSET'
	else: mat = bpy.data.materials[matname]
	
	#now finally set all the textures we have in the mesh
	me = ob.data
	me.materials.append(mat)
	
def load(operator, context, filepath = "", use_custom_normals = False, mirror_mesh=False):
	starttime = time.clock()
	global errors
	errors = []
	global armature
	global camera
	global datastream
	global dirname
	global id2data
	armature = None
	camera = None
	dirname, basename = os.path.split(filepath)
	id2data = {}
	skinned_meshes = []
	#when no object exists, or when we are in edit mode when script is run
	try: bpy.ops.object.mode_set(mode='OBJECT')
	except: pass
	print("\nImporting",basename)
	with open(filepath, 'rb') as f:
		datastream = f.read()
	#used to access data from the BFB by ID
	version, u_int, author, blockcount  = unpack_from("i i 64s i", datastream, 8)
	if version != 131073: log_error("Unsupported BFB version: "+str(version))
	pos = 88
	print("BFB Version:",version)
	print("BFB Author:",author.rstrip(b"\x00").decode("utf-8"))
	print("\nReading object blocks...")
	for b in range(0, blockcount):
		blockid, typeid, blockend, name = unpack_from("i h i 64s", datastream, pos)
		try:
			name = name.rstrip(b"\x00").decode("utf-8")
		except: name = "NONE"
		if typeid == 1:
			type_name = "SphereCollider"
			x, y, z, r = unpack_from("4f", datastream, pos+78)
			id2data[blockid] = create_sphere(name, x, y, z, r)
		elif typeid == 3:
			type_name = "BoundingBox"
			matrix = get_matrix(pos+78)
			x, y, z = unpack_from("3f", datastream, pos+142)
			id2data[blockid] = create_bounding_box(name, matrix.transposed(), x, y, z)
		elif typeid == 4:
			type_name = "Capsule"
			s_x, s_y, s_z, e_x, e_y, e_z, r = unpack_from("3f 3f f", datastream, pos+78)
			id2data[blockid] = create_capsule(name, mathutils.Vector((s_x, s_y, s_z)), mathutils.Vector((e_x, e_y, e_z)), r)
		elif typeid == 6:
			type_name = "MeshData"
			BFRVertex, v_len, v_num = unpack_from("64s 2i", datastream, pos+77)
			pos += 149
			BFRVertex = BFRVertex.rstrip(b"\x00").decode("utf-8")[9:]
			#This decodes the vertex format on the fly, should work on most if not all models. Some uncertainities about the last two, rare options.
			formatstr = BFRVertex.replace("P","3f").replace("N","3f").replace("T0","2f").replace("T1","2f").replace("T2","2f").replace("T30","3f").replace("T31","3f").replace("T3D1","2f4B").replace("D","4B")
			vertlist = list(iter_unpack(formatstr, datastream[pos : pos+v_len*v_num]))
			u_cha, t_num = unpack_from("=b i", datastream, pos+v_len*v_num)
			trilist = list(iter_unpack("3h", datastream[pos+v_len*v_num+5 : pos+v_len*v_num+5+t_num*2]))
			#there are some dummies that do not work as they should but most seems to work.
			#perhaps find a solution for D that works without texture
			#4/17: changed vcol to ND to make it work without tex!
			meshtypes = (("P",("ver",)), ("N",("nor",)), ("ND",("rgba",)), ("T0",("u0",)), ("T1",("u1",)), ("T2",("u2",)), ("T30",("u0","w",)), ("T31",("u1","c",)), ("T3D1",("u3","abcd",)), )
			mesh_data = {"tri":trilist, "we":[]}
			meshformat = []
			#parse the meshtypes from the BFRVertex into dict and list for correct sorting
			for letter, typetuple in meshtypes:
				for meshtype in typetuple:
					mesh_data[meshtype] = []
					if letter in BFRVertex: meshformat.append(meshtype)
			#sort the mesh_vert into the right mesh_data lists
			for vert in vertlist:
				x = 0
				for meshtype in meshformat:
					mesh_data[meshtype].append(vert[x : x+len(meshtype)])
					x += len(meshtype)
			id2data[blockid] = mesh_data
		elif typeid in (5,8):
			type_name = "Mesh"
			dataid, u_int, t_sta, t_num, v_sta, v_num, f_num, x, y, z, s = unpack_from("7i 4f", datastream, pos+77)
			mesh_data = id2data[dataid]
			#this could be integrated in the mesh creator further down?
			mesh = {}
			for key in mesh_data:
				if key == "tri":
					mesh[key] = mesh_data[key][t_sta//3:(t_sta+t_num)//3]
				else:
					mesh[key] = mesh_data[key][v_sta:v_sta+v_num]
			if typeid == 8:
				type_name = "Mesh (skinned)"
				numbones, numweights = unpack_from("2i", datastream, pos+121)
				pos += 129
				if not armature:
					#create the armature
					armData = bpy.data.armatures.new(basename[:-4])
					armData.show_axes = True
					armData.display_type = 'STICK'
					armature = create_ob(basename[:-4], armData)
					# armature.show_x_ray = True
					bpy.ops.object.mode_set(mode = 'EDIT')
					#read the armature block
					mat_storage = {}
					scales = {}
					for x in range(0, numbones):
						boneid, parentid, bonegroup, bonename = unpack_from("3b 64s", datastream, pos+x*131)
						bonename = bfbname_to_blendername(bonename)
						bind = mathutils.Matrix(list(iter_unpack('4f',datastream[pos+67+x*131:pos+67+x*131+64])))
						#new support for bone scale
						scale = bind.to_scale()[0]
						if int(round(scale*1000)) != 1000:
							# bind = mathutils.Matrix.Scale(1/scale, 4) * bind
							scales[bonename] = scale
						#create a bone
						bone = armData.edit_bones.new(bonename)
						#parent it and get the armature space matrix
						if parentid > 0:
							#@ operator apparently does not work in-place
							bind = bind @ mat_storage[parentid]
							bone.parent = armData.edit_bones[parentid-1]
						#we store the bfb space armature matrix of each bone
						mat_storage[boneid] = bind.copy()
						#blender transposes matrices
						bind.transpose()
						#set transformation
						bind = correction_global @ correction_local @ bind @ correction_local.inverted()
						tail, roll = mat3_to_vec_roll(bind.to_3x3())
						bone.head = bind.to_translation()
						bone.tail = tail + bone.head
						bone.roll = roll
					#fix the bone length
					for edit_bone in armData.edit_bones:
						fix_bone_length(edit_bone)
					bpy.ops.object.mode_set(mode = 'OBJECT')
				pos += numbones*131
				bonenames = armature.data.bones.keys()
				for vert in [((b0, w0), (b1, w1), (b2, w2), (b3, 1-w0-w1-w2)) for b0, b1, b2, b3, w0, w1, w2 in list(iter_unpack("4b 3f", datastream[pos:pos+numweights*16]))]:
					mesh["we"].append([(bonenames[id], weight) for id, weight in vert if id > 0])
			ob, me = mesh_from_data(name, mesh["ver"], mesh["tri"], False)
			id2data[blockid] = ob
			if mesh["we"]:
				skinned_meshes.append(ob)
				for i, vert	in enumerate(mesh["we"]):
					for bonename, weight in vert:
						if bonename not in ob.vertex_groups: ob.vertex_groups.new( name = bonename )
						ob.vertex_groups[bonename].add([i], weight, 'REPLACE')
			#Do we have weights for the wind vertex shader? (UVW coordinates if you like) We store them as a vertex group so they can be easily modified.
			if mesh["w"]:
				print("Found fx_wind weights!")
				ob.vertex_groups.new( name = "fx_wind" )
				for i, vert in enumerate(mesh["w"]):
					ob.vertex_groups["fx_wind"].add([i], vert[0], 'REPLACE')

			for face in me.polygons:
				face.use_smooth = True
				face.material_index = 0
				
			if use_custom_normals:
				me.use_auto_smooth = True
				me.normals_split_custom_set_from_vertices(mesh["nor"])
			
			#UV: 1-V coordinate
			for uv_layer in ("u0","u1","u2"):
				if mesh[uv_layer]:
					me.uv_layers.new(name = uv_layer[-1])
					me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [mesh[uv_layer][l.vertex_index] for l in me.loops] for uv in (pair[0], 1-pair[1])])
			#2.8: vcol now uses RGBA colors, maintain old 2-layer setup until implementation is fully functional
			if mesh["rgba"]:
				me.vertex_colors.new(name = "RGB")
				me.vertex_colors[-1].data.foreach_set("color", [c for col in [mesh["rgba"][l.vertex_index] for l in me.loops] for c in (col[2]/255, col[1]/255, col[0]/255, 1)])
				me.vertex_colors.new(name = "AAA")
				me.vertex_colors[-1].data.foreach_set("color", [c for col in [mesh["rgba"][l.vertex_index] for l in me.loops] for c in (col[3]/255, col[3]/255, col[3]/255, 1)])
				
			bpy.ops.object.mode_set(mode = 'EDIT')
			if mirror_mesh and mesh["we"]:
				bpy.ops.mesh.bisect(plane_co=(0,0,0), plane_no=(1,0,0), clear_inner=True)
				bpy.ops.mesh.select_all(action='SELECT')
				mod = ob.modifiers.new('Mirror', 'MIRROR')
				mod.use_clip = True
				mod.use_mirror_merge = True
				mod.use_mirror_vertex_groups = True
				mod.use_x = True
				mod.merge_threshold = 0.001
			#implement a custom remove doubles algorithm
			#see which verts can be removed, find their indices and then make a new custom normals list
			if not use_custom_normals:
				bpy.ops.mesh.remove_doubles(threshold = 0.0001, use_unselected = False)
			try:
				bpy.ops.uv.seams_from_islands()
			except:
				log_error(ob.name+" has no UV coordinates!")
			bpy.ops.object.mode_set(mode = 'OBJECT')
			if mesh["we"]:
				mod = ob.modifiers.new('SkinDeform', 'ARMATURE')
				mod.object = armature
			me.calc_normals()
		else:
			type_name = "unknown ID: "+str(typeid)
				
		print('ID: %.i, Type: ' % int(blockid)+type_name+', End: %.i, Name: ' % int(blockend) + str(name))
		pos = blockend
	
	#Now comes the linked list part, it starts with the root block.
	print("\nReading object hierarchy and creating blender objects...")
	read_linked_list(pos, None, 0)
	
	#handle scale on armature and meshes
	if armature and scales:
		#set inverse scale to all bones
		for bonename, scale in scales.items():
			pbone = armature.pose.bones[bonename]
			pbone.matrix_basis = mathutils.Matrix.Scale(1/scale, 4)
		depsgraph = context.evaluated_depsgraph_get()
		#apply skin deformation 
		for ob in skinned_meshes:
			object_eval = ob.evaluated_get(depsgraph)
			ob.data = bpy.data.meshes.new_from_object(object_eval)
		#remove scales from armature
		bpy.context.view_layer.objects.active = armature
		bpy.ops.object.mode_set(mode='POSE' )
		bpy.ops.pose.armature_apply()
		bpy.ops.object.mode_set(mode='OBJECT' )
		#add scale back in as dummy action
		scale_action = create_anim(armature, "!scale!")
		for bonename, scale in scales.items():
			fcurves = [scale_action.fcurves.new(data_path = 'pose.bones["'+bonename+'"].scale', index = i, action_group = bonename) for i in range(0, 3)]
			for fcurve in fcurves: fcurve.keyframe_points.insert(0, scale)
	
	success = '\nFinished BFB Import in %.2f seconds\n' %(time.clock()-starttime)
	print(success)
	return errors