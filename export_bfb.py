import os
import time
import bpy
import mathutils
import xml.etree.ElementTree as ET
from struct import pack
from .common_bfb import *

def flatten(mat):
	return [v for row in mat for v in row]
	
def log_error(error):
	print(error)
	global errors
	errors.append(error)

def indent(elem, level=0):
	i = "\n" + level*"	"
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "	"
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
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
	except: pass

			
def write_bfmat(ob, mat):
	matoptions=[("AlphaApplyMode","dword","4"),
				("AlphaBlendEnable","bool","false"),
				("AlphaFunc","dword","5"),
				("AlphaRef","dword","127"),
				("AlphaTestEnable","bool","true"),
				("AmbientMaterialSource","dword","1"),
				("ColorApplyMode","dword","4"),
				("CullMode","dword","1"),
				("DiffuseMaterialSource","dword","1"),
				("EmissiveMaterialSource","dword","0"),
				("MaterialAmbient","vector4","1, 1, 1, 1"),
				("MaterialDiffuse","vector4","1, 1, 1, 1"),
				("MaterialEmissive","vector4","0, 0, 0, 1"),
				("MaterialPower","float","1"),
				("ShadeMode","dword","2"),
				("SpecularEnable","bool","false")]
				
	print("Exporting BFMAT file for",mat.name)
	matpath=os.path.join(dirname,"Materials")
	if not os.path.exists(matpath):
		os.makedirs(matpath)
	material = ET.Element('material')
	index=0
	fps=bpy.context.scene.render.fps
	for i, texture_slot in enumerate(mat.texture_slots):
		if texture_slot:
			if texture_slot.texture.type == "IMAGE":
				
				u = find_fcurve(mat, "texture_slots["+str(i)+"].offset", 0)
				v = find_fcurve(mat, "texture_slots["+str(i)+"].offset", 1)
				
				if u:
					animate = ET.SubElement(material, "animate",{"name":"TextureTransform"+str(index),"type":"UVTransform", "loop":"wrap", "length":str(max(u.range()[1],v.range()[1])/fps)})
					offsetu =  ET.SubElement(animate, "offsetu")
					for k in u.keyframe_points:
						ET.SubElement(offsetu, "key",{"time":str(k.co[0]/fps),"value":str(k.co[1])})
					offsetv =  ET.SubElement(animate, "offsetv")
					for k in v.keyframe_points:
						ET.SubElement(offsetv, "key",{"time":str(k.co[0]/fps),"value":str(k.co[1])})
					#not exactly sure what these are for? - not supported atm
					tileu =  ET.SubElement(animate, "tileu")
					ET.SubElement(tileu, "key",{"time":"0.0","value":"1.0"})
					tilev =  ET.SubElement(animate, "tilev")
					ET.SubElement(tilev, "key",{"time":"0.0","value":"1.0"})
					rotw =  ET.SubElement(animate, "rotw")
					ET.SubElement(rotw, "key",{"time":"0.0","value":"0.0"})
					
				#matoptions.append(("AddressU"+str(index), "dword", "1"))
				#matoptions.append(("AddressV"+str(index), "dword", "1"))
				if texture_slot.texture.image:
					image = texture_slot.texture.image.filepath
					if not image: image = texture_slot.texture.image.name
					matoptions.append(("Texture"+str(index), "texture", os.path.basename(image)[:-4]))
					try:
						texcoord = str(int(texture_slot.uv_layer))
					except:
						error = texture_slot.name+" does not follow the UV layer naming convention (numbers only), TexCoordIndex set to 0"
						print(error)
						texcoord = list(mat.texture_slots).index(texture_slot)
					matoptions.append(("TexCoordIndex"+str(index),"dword",texcoord))
					index+=1
				else:
					log_error('Texture '+texture_slot.texture.name+' in material '+mat.name+' contains no image!')
					
	
	fx="Base"
	if index==1:
		matoptions.append(("LightingEnable","bool","true"))
	if index==2:
		fx+="Decal"
	if index==3:
		fx+="DecalDetail"
	if ob in ob_2_fx_wind:
		fx+=ob_2_fx_wind[ob]
	material.set("fx",fx)
	#dots don't work in ZT2
	material.set("name",mat.name.replace(".",""))
	
	for option in sorted(matoptions, key=lambda x:x[0]):
		param=ET.SubElement(material, "param",{"name":option[0],"type":option[1]})
		param.text=str(option[2])
		
	materialtree=ET.ElementTree()
	materialtree._setroot(material)
	indent(material)
	materialtree.write(os.path.join(matpath, mat.name.replace(".","") + ".bfmat"))

def has_collider(ob):
	#does this empty contain a collider object?
	if ob.children and (ob.children[0].name.startswith('sphere') or ob.children[0].name.startswith('orientedbox')):
		return True
	return False
	
def write_linked_list(ob, start):
	data = b''
	matrix = flatten(ob.matrix_local.transposed())
	print('Gathering block data for',ob.name)
	if type(ob.data) in (type(None), bpy.types.Armature):
		# LOD group
		if ob.name.startswith('lodgroup'):
			type_id = 2
			data = pack('<B 64s 16f 3i 64s', 2, ob.name.encode('utf-8'), *matrix, 0, 2, 0, b'lodgroup')
		else:
			type_id = 1
			# Root Block
			if not ob.parent:
				data = pack('<B 64s 16f 3i', 0, ob.name.encode('utf-8'), *matrix, 0, 5, 0)
			# node, with collision attached
			elif has_collider(ob):
				data = pack('<B 64s 16f 4i', 1, ob.name.encode('utf-8'), *matrix, 1, 1, 1, ob_2_id[ob.children[0]])
			# standard node
			else:
				obname = "end_post" if "end_post" in ob.name else ob.name
				data = pack('<B 64s 16f 3i', 1, obname.encode('utf-8'), *matrix, 1, 1, 0)
	elif type(ob.data) == bpy.types.Mesh:
		if ob.name.startswith('sphere') or ob.name.startswith('orientedbox'): pass
		elif ob.name.startswith('capsule'):
			if ob.parent_type != "BONE" or not ob.parent_bone:
				log_error("Capsule collider "+ob.name+" is not parented to a bone.")
			bone = blendername_to_bfbname(ob.parent_bone)
			type_id = 5
			data = pack('<B 64s 16f 4i 64s', 0, bone.lower().encode('utf-8'), *matrix, 1, 1, 1, ob_2_id[ob], bone.encode('utf-8'))
		else:
			matname = 'none'
			if len(ob.data.materials) > 0:
				#sometimes the will be empty slots before a material
				for material in ob.data.materials:
					if material:
						if write_materials:
							write_bfmat(ob, material)
						matname = material.name.replace(".","")
						break
			else:
				log_error('Mesh '+ob.name+' has no Material, no BFMAT was exported!')
			if ob.constraints:
				#i assume 1, 0, -1 are the tracking axes?
				type_id = 4
				data = pack('<B 64s 16f 6i 3f 2i 128s', 4, ob.name.encode('utf-8'), *matrix, 0, 0, 0, 1, 0, 0, 1, 0, -1, 0, ob_2_id[ob], matname.encode('utf-8'))
			else:
				type_id = 3
				data = pack('<B 64s 16f 6i 128s', 4, ob.name.encode('utf-8'), *matrix, 1, 1, 0, 1, ob_2_id[ob], 1, matname.encode('utf-8'))
	if data:
		#does this node have children? colliders don't count!
		has_children = False
		if ob.children and not has_collider(ob):
			has_children = True
		next_child = start + len(data) + 16 if has_children else 0
		
		childrenstart = next_child
		for child in ob.children:
			childstr = write_linked_list(child, childrenstart)
			childrenstart += len(childstr)
			data += childstr
		#are there any more siblings of this node left to add? siblings follow after all children of this node
		has_sibling = False
		if ob.parent:
			for sibling in ob.parent.children[ob.parent.children.index(ob)+1:]:
				if type(sibling.data) in (type(None), bpy.types.Armature, bpy.types.Mesh):
					has_sibling = True
					break
		next_sibling = start + len(data) + 16 if has_sibling else 0
		return pack('<4i', ob_2_id[ob], type_id, next_child, next_sibling)+data
	return data
	
def save(operator, context, filepath = '', author_name = "HENDRIX", export_materials = True, create_lods = False, fix_root_bones=False, numlods = 1, rate = 1):
	
	if create_lods:
		print('Adding LODs...')
		from . import batch_bfb
		batch_bfb.add_lods(numlods, rate)
		
	print('Exporting',filepath,'...')
	global errors
	errors = []
	#just in case - probably not needed
	#make sure there is an active object - is it needed?
	try: bpy.ops.object.mode_set(mode="OBJECT")
	except:
		bpy.context.scene.objects.active = bpy.context.scene.objects[0]
		bpy.ops.object.mode_set(mode="OBJECT")
	
	global write_materials
	write_materials = export_materials
	global dirname
	dirname = os.path.dirname(filepath)
	armature_bytes = b""
	
	#if one model uses an armature, all have to. If they don't, they can't be exported.
	has_armature = False
	
	global ob_2_block
	ob_2_block = {}
	global ob_2_weight_bytes
	ob_2_weight_bytes = {}
	global ob_2_fx_wind
	ob_2_fx_wind = {}
	global ob_2_id
	ob_2_id = {}
	ob_2_meshOffset={}
	BFRVertex_2_meshData={}
	
	global stream
	stream = b''
	starttime = time.clock()
	print('Generating block IDs for objects in scene...')
	#keep track of objects without a parent, if >1 add an Auto Root
	roots=[]
	for ob in bpy.context.scene.objects:
		if type(ob.data) in (type(None), bpy.types.Armature, bpy.types.Mesh):
			if ob.parent==None:
				roots.append(ob)
	if len(roots)==1:
		root=roots[0]
		if root.name.startswith("lodgroup"):
			print('Warning! Lodgroup must not be root! Created an Auto Root empty!')
			root = create_empty(None, 'Auto Root', mathutils.Matrix())
			roots[0].parent = root
	else:
		print('Warning! Found more than one root object! Created an Auto Root empty!')
		root = create_empty(None, 'Auto Root', mathutils.Matrix())
		for ob in roots:
			ob.parent = root
	
	identity = mathutils.Matrix()
	blockcount = 0
	ID=1
	for ob in bpy.context.scene.objects:
		ob_2_id[ob]=ID
		ID+=1
		if type(ob.data) == bpy.types.Mesh:
			#note that this is not the final blockcount, as every mesh data also gets counted
			blockcount+=1
			#fix meshes parented to a bone by adding vgroups
			if ob.parent_type == "BONE" and not ob.name.startswith('capsule'):
				log_error(ob.name+" was parented to a bone, which is not supported by BFBs. This has been fixed for you.")
				bonename = ob.parent_bone
				ob.vertex_groups.new(bonename)
				try: ob.data.transform( ob.parent.data.bones[bonename].matrix_local )
				except: pass
				ob.vertex_groups[bonename].add( range(len(ob.data.vertices)), 1.0, 'REPLACE' )
				ob.parent_type = "OBJECT"
				bpy.context.scene.update()
			if ob.find_armature():
				#the world space transform of every rigged mesh must be neutral
				#local space transforms of the mesh and its parents may be different as long as the mesh origin ends up on the scene origin
				if ob.matrix_world != identity:
					ob.data.transform(ob.matrix_world)
					ob.matrix_world = identity
					log_error(ob.name+" has had its transform applied to avoid ingame distortion!")
				has_armature = True
	rest_scale = None
	print('Gathering mesh data...')
	#get all objects, meshData, meshes + skeletons and collisions
	for ob in bpy.context.scene.objects:
		if type(ob.data) == bpy.types.Mesh:
			if ob.name.startswith('capsule'):
				stream+=export_capsule(ob, 88+len(stream))
			elif ob.name.startswith('sphere'):
				stream+=export_sphere(ob, 88+len(stream))
			elif ob.name.startswith('orientedbox'):
				stream+=export_bounding_box(ob, 88+len(stream))
			else:
				#export the armature if not already done for a previous mesh
				armature = ob.find_armature()
				#we have an armature on one mesh, means we can't export meshes without armature
				if has_armature and not armature:
					log_error(ob.name+" is not exported because it does not use an armature while other models do.")
					continue
				if has_armature and not armature_bytes:
					for pbone in armature.pose.bones:
						pbone.matrix_basis = mathutils.Matrix()
					bones = armature.data.bones.values()
					#todo: calculate this value properly, refer values from other objects
					lodgroup = -1
					root_bones = [bone for bone in bones if not bone.parent]
					#fatal
					if len(root_bones) > 1:
						if fix_root_bones:
							#determine the proper root
							root_bone = root_bones[0]
							for bone in root_bones:
								if bone.name == "Bip01":
									root_bone = bone
									break
							bpy.context.scene.objects.active = armature
							bpy.ops.object.mode_set(mode = 'EDIT')
							#delete the other root bones
							for bone in root_bones:
								if bone != root_bone:
									e_bone = armature.data.edit_bones[bone.name]
									armature.data.edit_bones.remove(e_bone)
									print("Removed",bone.name,"because it is a superfluous root bone")
							bpy.ops.object.mode_set(mode = 'OBJECT')
							#update the bones list
							bones = armature.data.bones.values()
						else:
							log_error(armature.name+" has more than one root bone. Remove all other root bones so that only Bip01 remains. This usually means: Bake and export your animations and then remove all control bones before you export the model.")
							return errors
					
					rest_scale = bpy.data.actions["!scale!"]
					for bone in bones:
						boneid = bones.index(bone)+1
						if bone.parent:
							parentid = bones.index(bone.parent)+1
						else:
							parentid = 0
						#new scale support
						try:
							group = rest_scale.groups[bone.name]
							scales = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("scale")]
							scale = scales[0].keyframe_points[0].co[1]
						except:
							scale = 1.0
						mat = mathutils.Matrix.Scale(scale, 4) * get_bfb_matrix(bone)
						armature_bytes += pack('<bbb 64s 16f', boneid, parentid, lodgroup, blendername_to_bfbname(bone.name).lower().encode('utf-8'), *flatten(mat) )
				
				# we have to apply the scale dummy action
				if rest_scale:
					armature.animation_data.action = rest_scale
					bpy.context.scene.frame_set(0)
				#remove unneeded modifiers
				for mod in ob.modifiers:
					if mod.type in ('TRIANGULATE',):
						ob.modifiers.remove(mod)
				ob.modifiers.new('Triangulate', 'TRIANGULATE')
				
				#make a copy with all modifiers applied - I think there was another way to do it too
				me = ob.to_mesh(bpy.context.scene, True, "PREVIEW", calc_tessface=False)
				
				if len(me.vertices) == 0:
					log_error(ob.name+" has no vertices. Delete the object and export again.")
					return errors
				#need this?
				me.calc_normals_split()
				
				mesh_vertices = []
				mesh_triangles = []
				#used to ignore the normals for checking equality
				dummy_vertices = []
				
				weights_bytes = b''
				bfb_col=b''
				if 'fx_wind' in ob.vertex_groups:
					weight_group_index = ob.vertex_groups['fx_wind'].index
					ob_2_fx_wind[ob] = "_wind"
					#this is for some shaders to make sure the decal set uses the UV1
					if len(me.uv_layers) > 1:
						ob_2_fx_wind[ob]+="_uv11"
				#use this to look up the index of the uv layer
				#this is a little faster than
				BFRVertex='PN'
				if me.vertex_colors:
					if len(me.vertex_colors) == 1:
						log_error('Mesh '+me.name+' has 1 vertex color layer, must be either 0 or 2 (RGB and AAA)')
						return errors
					BFRVertex+='D'
				for i in range(0,len(me.uv_layers)):
					if 'fx_wind' in ob.vertex_groups: BFRVertex+='T3'+str(i)
					else: BFRVertex+='T'+str(i)
				#select all verts without weights
				unweighted_vertices = []
				for polygon in me.polygons:
					tri=[]
					for loop_index in polygon.loop_indices:
						vertex_index = me.loops[loop_index].vertex_index
						co = me.vertices[vertex_index].co
						no = me.loops[loop_index].normal
						
						bfb_vertex = pack('<3f',co.x, co.y, co.z)
						bfb_normal = pack('<3f',no.x, no.y, no.z)
						if me.vertex_colors:
							bfb_col = pack('<4B',int(me.vertex_colors[0].data[loop_index].color.b*255),
												int(me.vertex_colors[0].data[loop_index].color.g*255),
												int(me.vertex_colors[0].data[loop_index].color.r*255),
												int(me.vertex_colors[1].data[loop_index].color.b*255))
						bfb_uv = b''
						if 'T3' in BFRVertex:
							try: weight = me.vertices[vertex_index].groups[weight_group_index].weight
							except: weight = 0
						for uv_layer in me.uv_layers:
							if 'T3' in BFRVertex:
								bfb_uv+= pack('<3f',uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y, weight)
							else:
								bfb_uv+= pack('<2f',uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y)
						#we have to add new verts also if the UV is different!
						if bfb_vertex+bfb_uv not in dummy_vertices:
							dummy_vertices.append(bfb_vertex+bfb_uv)
							mesh_vertices.append(bfb_vertex+bfb_normal+bfb_col+bfb_uv)
							if armature_bytes:
								w = []
								bones = armature.data.bones.keys()
								for vertex_group in me.vertices[vertex_index].groups:
									#dummy vertex groups without corresponding bones
									try: w.append((bones.index(ob.vertex_groups[vertex_group.group].name), vertex_group.weight))
									except: pass
								w_s = sorted(w, key = lambda x:x[1], reverse = True)[0:4]
								#pad the weight list to 4 bones, ie. add empty bones if missing
								for i in range(0, 4-len(w_s)): w_s.append((-1,0))
								sw = w_s[0][1]+w_s[1][1]+w_s[2][1]+w_s[3][1]
								if sw > 0.0: weights_bytes+= pack('<4b 3f', w_s[0][0], w_s[1][0], w_s[2][0], w_s[3][0], w_s[0][1]/sw, w_s[1][1]/sw, w_s[2][1]/sw)
								elif vertex_index not in unweighted_vertices: unweighted_vertices.append(vertex_index)
						tri.append( dummy_vertices.index(bfb_vertex+bfb_uv) )
					mesh_triangles.append( pack('<3h',*tri) )
				
				if armature_bytes:
					ob_2_weight_bytes[ob] = weights_bytes
				if unweighted_vertices:
					log_error('Found '+str(len(unweighted_vertices))+' unweighted vertices in '+ob.name+'! Add them to vertex groups!')
					return errors
				#does a mesh of this type already exist?
				if BFRVertex not in BFRVertex_2_meshData: BFRVertex_2_meshData[BFRVertex] = ([],[],[])
				BFRVertex_2_meshData[BFRVertex][0].append(ob)
				BFRVertex_2_meshData[BFRVertex][1].append(mesh_vertices)
				BFRVertex_2_meshData[BFRVertex][2].append(mesh_triangles)
					
	#1) create a meshData block for every vertex type we have
	#2) merge all meshes that use the same vertex type
	#3) get the counts for creating separate mesh blocks in the next loop
	#4) increment blockcount + ID for each meshData
	for BFRVertex, (obs, vertex_lists, triangle_lists) in BFRVertex_2_meshData.items():
		ID+=1
		blockcount+=1
		print('Assigned meshID',ID,'to BFRVertex'+BFRVertex)
		num_all_vertices = 0
		num_all_triangles = 0
		bytes_vertices = b''
		bytes_triangles = b''
		for ob, vertex_list, triangle_list in zip(obs, vertex_lists, triangle_lists):
			num_vertices  = len(vertex_list)
			num_triangles = len(triangle_list)
			bytes_vertices += b''.join(vertex_list)
			bytes_triangles += b''.join(triangle_list)
			ob_2_meshOffset[ob] = (ID, num_all_vertices, num_vertices, num_all_triangles, num_triangles)
			num_all_vertices += num_vertices
			num_all_triangles += num_triangles
		len_vert = len(vertex_list[0])
		#write the meshData block
		stream += pack('<i 2h i 64s B 64s 2i', ID, 6, -32768, len(stream)+242+num_all_vertices*len_vert+num_all_triangles*6, b'meshData', 8, 
		('BFRVertex'+BFRVertex).encode('utf-8'), len_vert, num_all_vertices) + bytes_vertices + pack('<B i', 2, num_all_triangles*3) + bytes_triangles
		
	#write the mesh blocks
	for ob in ob_2_meshOffset:
		meshDataID, start_vertices, num_vertices, start_triangles, num_triangles = ob_2_meshOffset[ob]
		me = ob.data
		
		center = mathutils.Vector()
		for v in me.vertices:
			center += v.co
		center /= len(me.vertices)
		radius = max( [(v.co-center).length for v in me.vertices] )
		
		if ob in ob_2_weight_bytes:
			weights_bytes = ob_2_weight_bytes[ob]
			typeid = 8
			len_weights=len(armature_bytes)+len(weights_bytes)+8
		else:
			typeid = 5
			len_weights = 0
		stream += pack('<i 2h i 64s B 7i 4f', ob_2_id[ob], typeid, -32768, len(stream)+209+len_weights, b'mesh', 0, meshDataID, 1, start_triangles*3, num_triangles*3, start_vertices, num_vertices, num_triangles, *center, radius)
		
		if ob in ob_2_weight_bytes:
			stream += pack('<2i', len(armature_bytes)//131, len(weights_bytes)//16) + armature_bytes + weights_bytes
	
	stream = pack('<8s l l 64s i i', b'BFB!*000', 131073, 1, author_name.encode('utf-8'), blockcount, blockcount) + stream
	stream+= write_linked_list(root, len(stream))

	if not os.path.exists(dirname):
		os.makedirs(dirname)
	f = open(filepath, 'wb')
	f.write(stream)
	f.close()

	print('Finished BFB Export in %.2f seconds' %(time.clock()-starttime))
	return errors

def export_capsule(ob, blockstart):
	print('Found capsule collider!')
	me = ob.data
	start = (me.vertices[0].co+me.vertices[12].co) / 2
	end = (me.vertices[37].co+me.vertices[49].co) / 2 - start
	radius = ((me.vertices[0].co-me.vertices[12].co) / 2).length
	return pack('<i 2h i 64s h 3f 3f f', ob_2_id[ob], 4, -32768, blockstart+106, ob.name.encode('utf-8'), 1, start.x, start.y, start.z, end.x, end.y, end.z, radius)

def export_bounding_box(ob, blockstart):
	print('Found bounding box collider!')
	me = ob.data
	x, y, z = me.vertices[4].co*2
	return pack('<i 2h i 64s h 16f 3f', ob_2_id[ob], 3, -32768, blockstart+154, ob.name.encode('utf-8'), 1, *flatten(ob.matrix_local.transposed()), x, y, z)

def export_sphere(ob, blockstart):
	print('Found sphere collider!')
	me = ob.data
	center = (me.vertices[2].co + me.vertices[23].co) / 2
	r = (me.vertices[2].co - center).length
	return pack('<i 2h i 64s h 4f', ob_2_id[ob], 1, -32768, blockstart+94, ob.name.encode('utf-8'), 1, *ob.location, r)
