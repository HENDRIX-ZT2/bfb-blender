import math
import bpy
import mathutils
import os


def LOD(ob, level):
	"""Adds a newly created object to a lod collection, creates one if neeed, and sets their visibility"""
	lod_name = "LOD"+str(level)
	if lod_name not in bpy.data.collections:
		coll = bpy.data.collections.new(lod_name)
		bpy.context.scene.collection.children.link(coll)
	else:
		coll = bpy.data.collections[lod_name]
	# Link active object to the new collection
	coll.objects.link(ob)
	# show lod 0, hide the others
	should_hide = level != 0
	# hide object in view layer
	hide_collection(lod_name, should_hide)
	# hide object in view layer
	ob.hide_set(should_hide, view_layer=bpy.context.view_layer)




def hide_collection(lod_name, should_hide):
	# get view layer, hide collection there
	# print(list(x for x in bpy.context.view_layer.layer_collection.children))
	bpy.context.view_layer.layer_collection.children[lod_name].hide_viewport = should_hide


def ensure_active_object():
	# ensure that we have objects in the scene
	if bpy.context.scene.objects:
		# operator needs an active object, set one if missing (eg. user had deleted the active object)
		if not bpy.context.view_layer.objects.active:
			bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
		# now enter object mode on the active object, if we aren't already in it
		bpy.ops.object.mode_set(mode="OBJECT")
	else:
		print("No objects in scene, nothing to export!")

def fix_bone_length(edit_bone):
	#don't change Bip01
	if edit_bone.parent:
		if edit_bone.children:
			childheads = mathutils.Vector()
			for child in edit_bone.children:
				childheads += child.head
			bone_length = (edit_bone.head - childheads/len(edit_bone.children)).length
			if bone_length < 0.01:
				bone_length = 0.25
		# end of a chain
		else:
			bone_length = edit_bone.parent.length
		edit_bone.length = bone_length
	
def load_config():
	d={}
	f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"config_bfb.ini"), 'rb')
	new_list = f.read().decode("utf-8").split("\n")
	f.close()
	for line in new_list:
		try:
			(key, val) = line.split("=")
			d[key] = val
		except:
			pass
	return d

def update_config(key,val):
	config=load_config()
	if key not in config.keys():
		config[key] = val
		stream=config_to_str(config)
	elif val != str(config[key]):
		config[key] = val
		stream=config_to_str(config)
	else:
		return
	f = open(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)),"config_bfb.ini")), 'wb')
	f.write(stream.encode("utf-8"))
	f.close()
	
def config_to_str(config):
	stream=""
	for key in config:
		stream+=(key+"="+config[key]+"\n")
	return stream

def create_ob(ob_name, ob_data):
	ob = bpy.data.objects.new(ob_name, ob_data)
	bpy.context.scene.collection.objects.link(ob)
	bpy.context.view_layer.objects.active = ob
	return ob
	
def create_anim(ob, anim_name):
	action = bpy.data.actions.new(name = anim_name)
	action.use_fake_user = True
	ob.animation_data_create()
	ob.animation_data.action = action
	return action
	
def mesh_from_data(name, verts, faces, wireframe = True):
	me = bpy.data.meshes.new(name)
	me.from_pydata(verts, [], faces)
	me.update()
	ob = create_ob(name, me)
	if wireframe:
		ob.display_type = 'WIRE'
	return ob, me
	
def create_sphere(name, x, y, z, r):
	verts = [(0.50,0.00,0.87),(0.87,0.00,0.50),(1.00,0.00,-0.00),(0.87,0.00,-0.50),(0.50,0.00,-0.87),(0.35,0.35,-0.87),(0.61,0.61,-0.50),(0.71,0.71,0.00),(0.61,0.61,0.50),(0.35,0.35,0.87),(0.00,0.00,1.00),(-0.00,0.50,0.87),(-0.00,0.87,0.50),(-0.00,1.00,0.00),(-0.00,0.87,-0.50),(-0.00,0.50,-0.87),(-0.35,0.35,-0.87),(-0.61,0.61,-0.50),(-0.71,0.71,0.00),(-0.61,0.61,0.50),(-0.35,0.35,0.87),(-0.50,-0.00,0.87),(-0.87,-0.00,0.50),(-1.00,-0.00,0.00),(-0.87,-0.00,-0.50),(-0.50,-0.00,-0.87),(-0.00,-0.00,-1.00),(-0.35,-0.35,-0.87),(-0.61,-0.61,-0.50),(-0.71,-0.71,0.00),(-0.61,-0.61,0.50),(-0.35,-0.35,0.87),(0.00,-0.50,0.87),(0.00,-0.87,0.50),(0.00,-1.00,0.00),(0.00,-0.87,-0.50),(0.00,-0.50,-0.87),(0.35,-0.35,-0.87),(0.61,-0.61,-0.50),(0.71,-0.71,0.00),(0.61,-0.61,0.50),(0.35,-0.35,0.87)]
	faces = [(26,5,4),(4,5,6,3),(3,6,7,2),(2,7,8,1),(9,0,1,8),(0,9,10),(9,11,10),(8,12,11,9),(7,13,12,8),(6,14,13,7),(5,15,14,6),(26,15,5),(26,16,15),(15,16,17,14),(14,17,18,13),(13,18,19,12),(12,19,20,11),(11,20,10),(20,21,10),(19,22,21,20),(18,23,22,19),(17,24,23,18),(16,25,24,17),(26,25,16),(26,27,25),(25,27,28,24),(24,28,29,23),(23,29,30,22),(22,30,31,21),(21,31,10),(31,32,10),(30,33,32,31),(29,34,33,30),(28,35,34,29),(27,36,35,28),(26,36,27),(26,37,36),(36,37,38,35),(35,38,39,34),(34,39,40,33),(33,40,41,32),(32,41,10),(41,0,10),(0,41,40,1),(39,2,1,40),(38,3,2,39),(37,4,3,38),(26,4,37)]
	ob, me = mesh_from_data(name,verts,faces)
	for v in me.vertices:
		v.co = v.co*r
	ob.location = (x,y,z)
	# ob.layers = select_layer(5)
	return ob

def create_bounding_box(name, matrix, x, y, z):
	verts = [(x/2,y/2,-z/2),(x/2,-y/2,-z/2),(-x/2,-y/2,-z/2),(-x/2,y/2,-z/2),(x/2,y/2,z/2),(x/2,-y/2,z/2),(-x/2,-y/2,z/2),(-x/2,y/2,z/2)]
	faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)]
	ob, me = mesh_from_data(name,verts,faces)
	ob.matrix_local = matrix
	# ob.layers = select_layer(5)
	return ob
	
def create_capsule(name, start, end, r):
	#print(start,end,r)
	l = end.length
	#this primitive stands up and has radius of 0.5, height 1, the caps extend outward
	verts = [(1.00*r,0.00*r,-0.00*r),(0.87*r,0.00*r,-0.50*r),(0.50*r,0.00*r,-0.87*r),(0.35*r,0.35*r,-0.87*r),(0.61*r,0.61*r,-0.50*r),(0.71*r,0.71*r,0.00*r),(-0.00*r,1.00*r,0.00*r),(-0.00*r,0.87*r,-0.50*r),(-0.00*r,0.50*r,-0.87*r),(-0.35*r,0.35*r,-0.87*r),(-0.61*r,0.61*r,-0.50*r),(-0.71*r,0.71*r,0.00*r),(-1.00*r,-0.00*r,0.00*r),(-0.87*r,-0.00*r,-0.50*r),(-0.50*r,-0.00*r,-0.87*r),(-0.00*r,-0.00*r,-1.00*r),(-0.35*r,-0.35*r,-0.87*r),(-0.61*r,-0.61*r,-0.50*r),(-0.71*r,-0.71*r,0.00*r),(0.00*r,-1.00*r,0.00*r),(0.00*r,-0.87*r,-0.50*r),(0.00*r,-0.50*r,-0.87*r),(0.35*r,-0.35*r,-0.87*r),(0.61*r,-0.61*r,-0.50*r),(0.71*r,-0.71*r,0.00*r),(0.71*r,-0.71*r,0.00*r+l),(0.61*r,-0.61*r,0.50*r+l),(0.35*r,-0.35*r,0.87*r+l),(0.00*r,-0.50*r,0.87*r+l),(0.00*r,-0.87*r,0.50*r+l),(0.00*r,-1.00*r,0.00*r+l),(-0.71*r,-0.71*r,0.00*r+l),(-0.61*r,-0.61*r,0.50*r+l),(-0.35*r,-0.35*r,0.87*r+l),(-0.00*r,-0.00*r,1.00*r+l),(-0.50*r,-0.00*r,0.87*r+l),(-0.87*r,-0.00*r,0.50*r+l),(-1.00*r,-0.00*r,0.00*r+l),(-0.71*r,0.71*r,0.00*r+l),(-0.61*r,0.61*r,0.50*r+l),(-0.35*r,0.35*r,0.87*r+l),(-0.00*r,0.50*r,0.87*r+l),(-0.00*r,0.87*r,0.50*r+l),(-0.00*r,1.00*r,0.00*r+l),(0.71*r,0.71*r,0.00*r+l),(0.61*r,0.61*r,0.50*r+l),(0.35*r,0.35*r,0.87*r+l),(0.50*r,0.00*r,0.87*r+l),(0.87*r,0.00*r,0.50*r+l),(1.00*r,0.00*r,0.00*r+l)]
	faces = [(15,3,2),(2,3,4,1),(5,0,1,4),(4,7,6,5),(3,8,7,4),(15,8,3),(15,9,8),(8,9,10,7),(7,10,11,6),(10,13,12,11),(9,14,13,10),(15,14,9),(15,16,14),(14,16,17,13),(13,17,18,12),(17,20,19,18),(16,21,20,17),(15,21,16),(15,22,21),(21,22,23,20),(20,23,24,19),(0,24,23,1),(22,2,1,23),(15,2,22),(34,47,27),(27,47,48,26),(49,25,26,48),(29,26,25,30),(28,27,26,29),(34,27,28),(34,28,33),(33,28,29,32),(32,29,30,31),(36,32,31,37),(35,33,32,36),(34,33,35),(34,35,40),(40,35,36,39),(39,36,37,38),(42,39,38,43),(41,40,39,42),(34,40,41),(34,41,46),(46,41,42,45),(45,42,43,44),(44,49,48,45),(47,46,45,48),(34,46,47),(18,19,30,31),(19,24,25,30),(0,49,25,24),(0,5,44,49),(5,6,43,44),(6,11,38,43),(11,12,37,38),(12,18,31,37)]
	ob, me = mesh_from_data(name,verts,faces)
	#we want a rotation that, when multiplied with the up vector, equals the end vector
	rot = end.to_track_quat("Z", "Y" )
	#this shows our rotation is correct	#up = mathutils.Vector((0,0,1))	#result = rot*up*l	#print(result)	#print(end)	#these are all working = identical
	for v in me.vertices:
		v.co = rot @ v.co+start
	ob.rotation_euler.z = 1.5708
	# ob.layers = select_layer(5)
	return ob

def create_empty(parent, name, matrix):
	empty = create_ob(name, None)
	if parent:
		empty.parent = parent
	empty.matrix_local = matrix
	empty.empty_display_type="ARROWS"
	return empty

correction_local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
correction_global = mathutils.Euler((math.radians(-90), math.radians(-90), 0)).to_matrix().to_4x4()

def get_bfb_matrix(bone):
	bind = correction_global.inverted() @  correction_local.inverted() @ bone.matrix_local @  correction_local
	if bone.parent:
		p_bind_restored = correction_global.inverted() @ correction_local.inverted() @ bone.parent.matrix_local @ correction_local
		bind = p_bind_restored.inverted() @ bind
		
	return bind.transposed()
	
def decompose_srt(mat):
	mat.transpose()
	b_scale = 1.0
	b_rot = mat.to_quaternion().to_matrix()
	b_trans = mat.translation
	return b_scale, b_rot, b_trans
	
def blendername_to_bfbname(s):
	if 'Bip01 ' in s:
		if '.L' in s:
			s = s[:-2].replace('Bip01 ','Bip01 L ')
		elif '.R' in s:
			s = s[:-2].replace('Bip01 ','Bip01 R ')
	return s
	
def bfbname_to_blendername(s):
	s = s.rstrip(b"\x00").decode("utf-8")
	if " l " in s:
		s+= ".L"
	elif " L " in s:
		s+= ".L"
	if " r " in s:
		s+= ".R"
	elif " R " in s:
		s+= ".R"
	return s.title().replace(" R "," ").replace(" L "," ").replace("back","Back").replace("front","Front").replace("left","Left").replace("right","Right").replace("Nonaccum","NonAccum").replace("Upperarm","UpperArm").replace("Horselink","HorseLink")
	
def get_armature():
	src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
	#do we have armatures?
	if src_armatures:
		#see if one of these is selected -> get only that one
		if len(src_armatures) > 1:
			sel_armatures = [ob for ob in src_armatures if ob.select]
			if sel_armatures:
				return sel_armatures[0]
		return src_armatures[0]
	