import os
import time
import bpy
import mathutils
import xml.etree.ElementTree as ET
from struct import iter_unpack, unpack_from
from .common_bfb import *

def getstring128(x): return datastream[x:x+128].rstrip(b"\x00").decode("utf-8")
def getint(x): return unpack_from('i',datastream, x)[0]
def get_matrix(x): return mathutils.Matrix(list(iter_unpack('4f',datastream[x:x+64])))

def select_layer(layer_nr): return tuple(i == layer_nr for i in range(0, 20))

def log_error(error):
	print(error)
	global errors
	errors.append(error)
	
def read_linked_list(pos,parent,level):
	try:
		blockid, typeid, childstart, nextblockstart, u_cha, name = unpack_from("=4i b 64s", datastream, pos)
		name = name.rstrip(b"\x00").decode("utf-8")
		matrix = get_matrix(pos+81)
		matrix.transpose()
		#ordinary node, node with collision or lod level
		if typeid == 1:
			print("NODE:",name)
			if parent:
				ob = create_empty(parent,name,matrix)
				#if this is a lod level, move it to its respective layer
				if parent.name.startswith("lodgroup"):
					ob.layers = select_layer(level)
				#a dock node, a collision node, but nothing with a model, so move it to layer 6
				else:
					ob.layers = parent.layers
			else:
				if armature:
					ob = armature
					ob.name = name
					ob.data.name = name
					ob.matrix_local = matrix
				else:
					ob = create_empty(parent,name,matrix)
				ob.layers = select_layer(5)
			hascollision = getint(pos+153)
			if hascollision == 1:
				id2data[getint(pos+157)].parent = ob
				if name.startswith("paint_"):
					ob.layers = select_layer(5)
		#lod group
		elif typeid == 2:
			print("LOD GROUP:",name)
			ob = create_empty(parent,"lodgroup",matrix)
			ob.layers = select_layer(5)
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
			ob.layers = select_layer(level)
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
			ob.layers = select_layer(level)
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
			level = read_linked_list(pos,ob,level)
		if parent:
			#if this is a lod level, move it to its respective layer
			if parent.name.startswith("lodgroup"):
				level+= 1
		#for the next block, the old empty is the parent
		if nextblockstart!= 0:
			pos = nextblockstart
			level = read_linked_list(pos,parent,level)
			
	except:
		if parent: name = parent.name
		else: name = "EMPTY"
		log_error("Read error at position "+str(pos)+" in "+name+"'s children.")
		
	return level
		
def create_material(ob,matname):
	
	recursiveDepth = 5
	
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
		mat_dir = dirname
		for dirLevel in range(0,recursiveDepth):
			mat_file = os.path.join(mat_dir, "Materials", matname+".bfmat")
			if os.path.exists(mat_file): break
			mat_file = os.path.join(mat_dir, "shared", "Materials", matname+".bfmat")
			if os.path.exists(mat_file): break
			mat_dir = os.path.dirname(mat_dir)

		if os.path.exists(mat_file):
			try:
				tree = ET.parse(mat_file)
			except:
				log_error("Materials/"+matname+".BFMAT cannot be parsed, likely due to an XML syntax error!")
				return
		else:
			log_error("Could not find Materials/"+matname+".BFMAT!")
			return
		
		#mat.diffuse_shader = 'LAMBERT' 
		#mat.diffuse_intensity = 1.0 
		#mat.specular_color = specular
		#mat.specular_shader = 'COOKTORR'
		mat.specular_intensity = 0.0
		mat.ambient = 1
		mat.use_transparency = True
		
		material = tree.getroot()
		fx = material.attrib["fx"]
		print("FX SHADER:",fx)
		for param in material:
			name = param.attrib["name"]
			if "type" in param.attrib:
				if param.attrib["type"] == "vector4":
					text = param.text.split(", ")
				else:
					text = param.text
			#set stuff on the material
			if name == "MaterialAmbient":
				mat.diffuse_color=float(text[0]),float(text[1]),float(text[2])#
				#always put to 0
				mat.alpha=0
			if name == "MaterialPower":
				mat.diffuse_intensity=float(text)
			
			#new and experimental
			if param.tag == "animate":
				fps = 25
				for i in range(0,2):
					if name == "TextureTransform"+str(i):
						for key in param.find("./offsetu"):
							mat.texture_slots[i].offset[0] = float(key.attrib["value"])
							mat.texture_slots[i].keyframe_insert("offset", index = 0, frame = int(float(key.attrib["time"])*fps))
						for key in param.find("./offsetv"):
							mat.texture_slots[i].offset[1] = float(key.attrib["value"])
							mat.texture_slots[i].keyframe_insert("offset", index = 1, frame = int(float(key.attrib["time"])*fps))
			#multi-textures
			for i in range(0,2):
				if name == "Texture"+str(i):
					#only import the image and texture if we haven't already imported it!
					#we may use the same texture in different materials!
					try:
						if text not in bpy.data.textures:
							tex = bpy.data.textures.new(text, type = 'IMAGE')
							tex_dir = dirname
							for dirLevel in range(0,recursiveDepth):
								tex_file = os.path.join(tex_dir,text+".dds")
								if os.path.exists(tex_file): break
								tex_file = os.path.join(tex_dir,"shared",text+".dds")
								if os.path.exists(tex_file): break
								tex_dir = os.path.dirname(tex_dir)
							try:
								img = bpy.data.images.load(tex_file)
							except:
								print("Could not find image "+text+".dds, generating blank image!")
								img = bpy.data.images.new(text+".dds",1,1)
							tex.image = img
						else: tex = bpy.data.textures[text]
						#now create the slot in the material for the texture
						mtex = mat.texture_slots.add()
						mtex.texture = tex
						mtex.texture_coords = 'UV'
						mtex.use_map_color_diffuse = True 
						mtex.use_map_color_emission = True 
						mtex.emission_color_factor = 0.5
						mtex.use_map_density = True 
						mtex.mapping = 'FLAT'
						#mtex.use_stencil = True
						#RR reflection effect
						if (fx == "BaseReflectRR" and i == 1) or (fx == "BaseDecalReflectRR" and i == 2):
							mtex.blend_type = 'OVERLAY'
							mtex.texture_coords = 'REFLECTION'
						if (fx == "BaseDetail" and i == 1):
							mtex.blend_type = 'OVERLAY'
						#TO DO: cull mode -> african violets
						
						#see if there is an alternative UV index specified. If so, set it as the UV layer. If not, use i.
						mtex.uv_layer = str(i)
						for param in material:
							if param.attrib["name"] == "TexCoordIndex"+str(i):
								mtex.uv_layer = param.text
								break
						
						#for the icon renderer
						tex.use_mipmap = False
						tex.use_interpolation = False
						tex.filter_type = "BOX"
						tex.filter_size = 0.1
						# we only want to render default tex for icons
						if i > 0: mat.use_textures[i] = False
					except:
						log_error(name+" in Materials/"+matname+".BFMAT has no image reference! Add the image name in the .BFMAT to fix!")
	else: mat = bpy.data.materials[matname]
	
	#now finally set all the textures we have in the mesh
	me = ob.data
	me.materials.append(mat)
	#reversed so the last is shown
	for mtex in reversed(mat.texture_slots):
		if mtex:
			try:
				uv_i = int(mtex.uv_layer)
				for texface in me.uv_textures[uv_i].data:
					texface.image = mtex.texture.image
			except:
				print("No matching UV layer for Texture!")
	#and for rendering, make sure each poly is assigned to the material
	for f in me.polygons:
		f.material_index = 0
	
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
		#try:
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
			#parse the meshtypes from the BFVertex into dict and list for correct sorting
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
					armData.draw_type = 'STICK'
					armature = create_ob(basename[:-4], armData)
					armature.show_x_ray = True
					bpy.ops.object.mode_set(mode = 'EDIT')
					#read the armature block
					mat_storage = {}
					for x in range(0, numbones):
						boneid, parentid, bonegroup, bonename = unpack_from("3b 64s", datastream, pos+x*131)
						bonename = bfbname_to_blendername(bonename)
						bind = mathutils.Matrix(list(iter_unpack('4f',datastream[pos+67+x*131:pos+67+x*131+64])))#.transposed()
						#create a bone
						bone = armData.edit_bones.new(bonename)
						#parent it and get the armature space matrix
						if parentid > 0:
							bind *= mat_storage[parentid]
							bone.parent = armData.edit_bones[parentid-1]
						#we store the bfb space armature matrix of each bone
						mat_storage[boneid] = bind.copy()
						#blender transposes matrices
						bind.transpose()
						#set transformation
						bind = correction_global * correction_local * bind * correction_local.inverted()
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
				for i, vert	in enumerate(mesh["we"]):
					for bonename, weight in vert:
						if bonename not in ob.vertex_groups: ob.vertex_groups.new(bonename)
						ob.vertex_groups[bonename].add([i], weight, 'REPLACE')
			#Do we have weights for the wind vertex shader? (UVW coordinates if you like) We store them as a vertex group so they can be easily modified.
			if mesh["w"]:
				print("Found fx_wind weights!")
				ob.vertex_groups.new("fx_wind")
				for i, vert in enumerate(mesh["w"]):
					ob.vertex_groups["fx_wind"].add([i], vert[0], 'REPLACE')
			#build a correctly sorted normals array, sorted by the order of faces - loops does not work!!
			no_array = []
			for face in me.polygons:
				for vertex_index in face.vertices:
					no_array.append(mesh["nor"][vertex_index])	
				face.use_smooth = True
			if use_custom_normals:
				me.use_auto_smooth = True
				#is there any way without the operator??
				bpy.ops.mesh.customdata_custom_splitnormals_add()
				me.normals_split_custom_set(no_array)
			
			#UV: 1-V coordinate
			for uv_layer in ("u0","u1","u2"):
				if mesh[uv_layer]:
					me.uv_textures.new(uv_layer[-1])
					me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [mesh[uv_layer][l.vertex_index] for l in me.loops] for uv in (pair[0], 1-pair[1])])
			if mesh["rgba"]:
				me.vertex_colors.new("RGB")
				me.vertex_colors[-1].data.foreach_set("color", [c for col in [mesh["rgba"][l.vertex_index] for l in me.loops] for c in (col[2]/255, col[1]/255, col[0]/255)])
				me.vertex_colors.new("AAA")
				me.vertex_colors[-1].data.foreach_set("color", [c for col in [mesh["rgba"][l.vertex_index] for l in me.loops] for c in (col[3]/255, col[3]/255, col[3]/255)])
				
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
		#except:
		#	log_error("Could not read block at position "+str(pos)+". Name: "+name+", Type: "+str(type_name))
		pos = blockend
	
	#Now comes the linked list part, it starts with the root block.
	print("\nReading object hierarchy and creating blender objects...")
	maxlod = read_linked_list(pos, None, 0)
	
	#set the visible layers for this scene
	bools = []
	for i in range(20):  
		if i < maxlod or i == 5 or i == 0: bools.append(True)
		else: bools.append(False)
	bpy.context.scene.layers = bools
	
	success = '\nFinished BFB Import in %.2f seconds\n' %(time.clock()-starttime)
	print(success)
	return errors