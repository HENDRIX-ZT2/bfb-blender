import os
import time
import bpy
#import bmesh
import mathutils
import xml.etree.ElementTree as ET
from struct import pack
from .common_bfb import *

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
	fps=25
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

def write_linked_list(ob, start):
	data = ""
	matrix = export_matrix(ob.matrix_local.transposed())
	print('Gathering block data for',ob.name)
	if type(ob.data) in (type(None), bpy.types.Armature):
		#Root Block
		if not ob.parent:
			type_id, data = (1, pack('=B 64s 64s 3i', 0, ob.name.encode('utf-8'), matrix, 0, 5, 0))
		# LOD group
		elif ob.name.startswith('lodgroup'):
			type_id, data = (2, pack('=B 64s 64s 3i 64s', 2, ob.name.encode('utf-8'), matrix, 0, 2, 0, b'lodgroup'))
		else:
			# node, with collision attached
			if ob.children and ob.children[0] and (ob.children[0].name.startswith('sphere') or ob.children[0].name.startswith('orientedbox')):
				type_id, data = (1, pack('=B 64s 64s 4i', 1, ob.name.encode('utf-8'), matrix, 1, 1, 1, ob_2_id[ob.children[0]]))
			# empty node
			else:
				obname = ob.name
				if "end_post" in ob.name:
					obname = "end_post"
				type_id, data = (1, pack('=B 64s 64s 3i', 1, obname.encode('utf-8'), matrix, 1, 1, 0))
	elif type(ob.data) == bpy.types.Mesh:
		if ob.name.startswith('sphere') or ob.name.startswith('orientedbox'): pass
		elif ob.name.startswith('capsule'):
			if ob.parent_type != "BONE":
				log_error("Capsule collider "+ob.name+" is not parented to a bone.")
#				return errors
			elif ob.parent_bone == "":
				log_error("Capsule collider "+ob.name+" is not parented to a bone.")
#				return errors
			bone = blendername_to_bfbname(ob.parent_bone)
			type_id, data = (5, pack('=B 64s 64s 4i 64s', 0, bone.lower().encode('utf-8'), matrix, 1, 1, 1, ob_2_id[ob], bone.encode('utf-8')))
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
				type_id, data = (4, pack('=B 64s 64s 6i 3f 2i 128s', 4, ob.name.encode('utf-8'), matrix, 0, 0, 0, 1, 0, 0, 1, 0, -1, 0, ob_2_id[ob], matname.encode('utf-8')))
			else:
				type_id, data = (3, pack('=B 64s 64s 6i 128s', 4, ob.name.encode('utf-8'), matrix, 1, 1, 0, 1, ob_2_id[ob], 1, matname.encode('utf-8')))
	
	oblist.append(ob)
	if data:
		if ob.children:
			#print(ob,'has children')
			childrenstart = start + len(data) + 16
			blockend = childrenstart
			for child in ob.children:
				childstr = write_linked_list(child,childrenstart)
				if childstr:
					childrenstart += len(childstr)
					data += childstr
			#collision nodes
			#the node has only one child and it's a mesh and it's a collider
			if len(ob.children) == 1:
				if ob.children[0].name.startswith('sphere') or ob.children[0].name.startswith('orientedbox'):
					blockend = 0
		else:
			#print(ob,'has no children!')
			blockend = 0
		nextblockstart = start + len(data) + 16

		#if no more sibling left, nextblockstart is 0
		has_no_sibling = True
		if ob.parent:
			for sibling in ob.parent.children:
				if type(sibling.data) in (type(None), bpy.types.Armature, bpy.types.Mesh):
					if sibling not in oblist:
						has_no_sibling = False
						break
		if has_no_sibling:
			#print('No more siblings left, move back up')
			nextblockstart = 0
		#print(ob,blockend,nextblockstart)
		return pack('= 4i', ob_2_id[ob], type_id, blockend, nextblockstart)+data
	
def save(operator, context, filepath = '', author_name = "HENDRIX", export_materials = True, create_lods = False, numlods = 1, rate = 1):
	
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
	#make global to check for weights and grant access to all meshes
	# not needed?
	global armature_bytes
	armature_bytes = b""
	global ob_2_block
	ob_2_block = {}
	global ob_2_weight_bytes
	ob_2_weight_bytes = {}
	global ob_2_fx_wind
	ob_2_fx_wind = {}
	global ob_2_id
	ob_2_id = {}
	#ID of meshdata, vert_readstart,readcount,tris readstart, readcount
	ob_2_meshOffset={}
	#BFRVertex=[meshData,meshData,....]
	#meshData=(vertices,trilist)
	#and get the ID later on
	BFRVertex_2_meshData={}
	
	global stream
	stream = b''
	#used to check for siblings when writing the linked list, ie. if one obejct has already been processed
	global oblist
	oblist = []
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
	
	
	#note that this is not the final blockcount, as every mesh data also gets counted
	ID=1
	blockcount=0
	for ob in bpy.context.scene.objects:
		while ID in list(ob_2_id.values()):
			ID+=1
		ob_2_id[ob]=ID
		if type(ob.data) == bpy.types.Mesh:
			blockcount+=1

	print('Gathering mesh data...')
	#get all objects, meshData, meshes + skeletons and collisions
	for ob in bpy.context.scene.objects:
		if type(ob.data) == bpy.types.Mesh:
			if ob.name.startswith('sphere'):
				stream+=export_sphere(ob, 88+len(stream))
			elif ob.name.startswith('orientedbox'):
				stream+=export_bounding_box(ob, 88+len(stream))
			elif ob.name.startswith('capsule'):
				stream+=export_capsule(ob, 88+len(stream))
			else:
				armature = ob.find_armature()
				#export the armature if not already done for a previous mesh
				if armature and not armature_bytes:
					bones = armature.data.bones.values()
					#todo: calculate this value properly, refer values from other objects
					lodgroup = -1
					roots = []
					for bone in bones:
						boneid = bones.index(bone)+1
						if bone.parent:
							parentid = bones.index(bone.parent)+1
						else:
							parentid = 0
							roots.append(bone)
						armature_bytes += pack('= bbb 64s', boneid, parentid, lodgroup, blendername_to_bfbname(bone.name).lower().encode('utf-8')) + export_matrix(get_bfb_matrix(bone))
					#fatal
					if len(roots) > 1:
						log_error(armature.name+" has more than one root bone. Remove all other root bones so that only Bip01 remains. This usually means: Bake and export your animations and then remove all control bones before you export the model.")
						return errors
				#remove unneeded modifiers
				for mod in ob.modifiers:
					if mod.type in ('ARMATURE','TRIANGULATE'):
						ob.modifiers.remove(mod)
				ob.modifiers.new('Triangulate', 'TRIANGULATE')
				#make a copy with all modifiers applied - I think there was another way to do it too
				me = ob.to_mesh(bpy.context.scene, True, "PREVIEW", calc_tessface=True, calc_undeformed=False)
				
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
					ob_2_fx_wind[ob] = "_wind"
					weight_group_index = ob.vertex_groups['fx_wind'].index
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
						#if me.has_custom_normals:
						no = me.loops[loop_index].normal
						#else: no = me.vertices[vertex_index].normal
						
						bfb_vertex = pack('= 3f',co.x, co.y, co.z)
						bfb_normal = pack('= 3f',no.x, no.y, no.z)
						if me.vertex_colors:
							#access via index for NIF intercompatibility
							bfb_col = pack('4B',int(me.vertex_colors[0].data[loop_index].color.b*255),
												int(me.vertex_colors[0].data[loop_index].color.g*255),
												int(me.vertex_colors[0].data[loop_index].color.r*255),
												int(me.vertex_colors[1].data[loop_index].color.b*255))
						bfb_uv = b''
						if 'T3' in BFRVertex:
							weight = 0
							#sometimes there might be zero weights missing from the group, which have to be restored
							#use get api instead??
							for vertex_group in me.vertices[vertex_index].groups:
								if vertex_group.group == weight_group_index:
									weight = vertex_group.weight
									break
						for uv_layer in me.uv_layers:
							if 'T3' in BFRVertex:
								bfb_uv+= pack('3f',uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y, weight)
							else:
								bfb_uv+= pack('2f',uv_layer.data[loop_index].uv.x, 1-uv_layer.data[loop_index].uv.y)
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
								sum = w_s[0][1]+w_s[1][1]+w_s[2][1]+w_s[3][1]
								if sum > 0.0: weights_bytes+= pack('4b 3f', w_s[0][0], w_s[1][0], w_s[2][0], w_s[3][0], w_s[0][1]/sum, w_s[1][1]/sum, w_s[2][1]/sum)
								elif vertex_index not in unweighted_vertices: unweighted_vertices.append(vertex_index)
						bfb_vert_index = dummy_vertices.index(bfb_vertex+bfb_uv)
						tri.append(bfb_vert_index)
					mesh_triangles.append(pack('= 3h',*tri))
				
				if armature_bytes:
					ob_2_weight_bytes[ob] = weights_bytes
					mod = ob.modifiers.new('SkinDeform', 'ARMATURE')
					mod.object = armature
					if unweighted_vertices:
						log_error('Found '+str(len(unweighted_vertices))+' unweighted vertices in '+ob.name+'! Add them to vertex groups!')
						return errors
				#does a mesh of this type already exist?
				if BFRVertex not in BFRVertex_2_meshData:
					blockcount+=1
					id=1
					while id in list(ob_2_id.values()): id+=1
					ob_2_id[id]=id
					print('Assigned meshID',id,'to BFRVertex'+BFRVertex)
					BFRVertex_2_meshData[BFRVertex]=(id,[],[],[])
				BFRVertex_2_meshData[BFRVertex][1].append(ob)
				BFRVertex_2_meshData[BFRVertex][2].append(mesh_vertices)
				BFRVertex_2_meshData[BFRVertex][3].append(mesh_triangles)
					
	#we create a meshData block for every vertex type we have
	#we merge all meshes that use the same vertex type
	#then we get the counts for creating separate mesh blocks in the next loop
	for BFRVertex in BFRVertex_2_meshData:		
		#so here we have a tuple with lists of all the blocks and the same index
		meshDataID, obs, vertex_lists, triangle_lists = BFRVertex_2_meshData[BFRVertex]
		num_all_vertices = 0
		num_all_triangles = 0
		bytes_vertices = b''
		bytes_triangles = b''
		for i in range(0,len(vertex_lists)):
			num_all_vertices += len(vertex_lists[i])
			num_all_triangles += len(triangle_lists[i])
			for vert in vertex_lists[i]:
				bytes_vertices += vert
			for tri in triangle_lists[i]:
				bytes_triangles += tri
			#these are the offsets for every mesh block
			start_vertices  = num_all_vertices - len(vertex_lists[i])
			start_triangles = num_all_triangles - len(triangle_lists[i])
			num_vertices  = len(vertex_lists[i])
			num_triangles = len(triangle_lists[i])
			ob_2_meshOffset[obs[i]]=(meshDataID, start_vertices, num_vertices, start_triangles, num_triangles)
		
		#write the meshData block
		stream += pack('= 3i 64s B 64s 2i',meshDataID, -2147483642, len(stream)+242+num_all_vertices*len(vert)+num_all_triangles*6, b'meshData', 8, 
		('BFRVertex'+BFRVertex).encode('utf-8'), len(vert), num_all_vertices) + bytes_vertices + pack('= B i', 2, num_all_triangles*3) + bytes_triangles
		
	#write the mesh blocks
	for ob in ob_2_meshOffset:
		meshDataID, start_vertices, num_vertices, start_triangles, num_triangles = ob_2_meshOffset[ob]
		me = ob.data
		
		center = mathutils.Vector()
		for v in me.vertices:
			center += v.co
		center = center/len(me.vertices)
		radius = 0
		for v in me.vertices:
			radius = max(radius,(v.co-center).length)
		
		id = 1
		while id in list(ob_2_id.values()):
			id += 1
		ob_2_id[ob] = id
		if ob in ob_2_weight_bytes:
			weights_bytes = ob_2_weight_bytes[ob]
			typeid = -2147483640
			len_weights=len(armature_bytes)+len(weights_bytes)+8
		else:
			typeid = -2147483643
			len_weights = 0
		stream += pack('= 3i 64s B 7i 4f', id, typeid, len(stream)+209+len_weights, b'mesh', 0, meshDataID, 1, start_triangles*3, num_triangles*3, start_vertices, num_vertices, num_triangles, center.x, center.y, center.z, radius)
		
		if ob in ob_2_weight_bytes:
			stream += pack('= 2i', int(len(armature_bytes)/131), int(len(weights_bytes)/16))
			stream += armature_bytes + weights_bytes
	
	header = pack('= 8s l l 64s i i', b'BFB!*000', 131073, 1, author_name.encode('utf-8'), blockcount, blockcount)
	stream = header + stream
	
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
	return pack('= 3i 64s h 3f 3f f', ob_2_id[ob], -2147483644, blockstart+106, ob.name.encode('utf-8'), 1, start.x, start.y, start.z, end.x, end.y, end.z, radius)

def export_bounding_box(ob, blockstart):
	print('Found bounding box collider!')
	me = ob.data
	x, y, z = me.vertices[4].co*2
	return pack('= 3i 64s h', ob_2_id[ob], -2147483645, blockstart+154, ob.name.encode('utf-8'), 1) + export_matrix(ob.matrix_local.transposed()) + pack('= 3f', x, y, z)

def export_sphere(ob, blockstart):
	print('Found sphere collider!')
	me = ob.data
	center = (me.vertices[2].co + me.vertices[23].co) / 2
	r = (me.vertices[2].co - center).length
	x, y, z = ob.location
	return pack('= 3i 64s h 4f', ob_2_id[ob], -2147483647, blockstart+94, ob.name.encode('utf-8'), 1, x, y, z, r)
	
def export_matrix(mat):
	bytes = b''
	for row in mat: bytes += pack('=4f',*row)
	return bytes
