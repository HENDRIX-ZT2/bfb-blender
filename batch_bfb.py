import bpy
import os
import mathutils
import time

from .common_bfb import *
from .import_bfb import LOD

def clear_scene():
	#set the visible layers for this scene
	# todo: make all collisions visible?
	# bpy.context.scene.layers = [True for i in range(0,20)]
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete(use_global=True)
	for cat in (bpy.data.objects, bpy.data.materials, ):
		for thing in cat:
			thing.user_clear()
			cat.remove(thing)
	
def get_children(childlist):
	global oblist
	for child in childlist:
		oblist.append(child)
		get_children(child.children)


def add_lods(numlods, rate):
	ensure_active_object()
	root = None
	meshes = []
	lodgroup = None
	for ob in bpy.context.scene.objects:
		ob.select_set(False)
		if type(ob.data) in (type(None), bpy.types.Armature):
			if ob.name.startswith("lodgroup"):
				print("BFB model already has lodgroups!")
				ob.select_set(True)
				lodgroup = ob
			if not ob.parent:
				root = ob
	# lodgroup mustn't be the root!
	if not root:
		root = create_empty(None,"AutoRoot",mathutils.Matrix())
	# delete the existing lodgroup and low detail lods
	for coll_name in bpy.context.view_layer.layer_collection.children.keys():
		hide_collection(coll_name, False)
	bpy.ops.object.select_all(action='DESELECT')
	if lodgroup:
		print("Found lodgroup, deleting children...")
		try:
			# parent lod0 to lodgroup's parent
			lod0 = lodgroup.children[0]
			lod0.parent = lodgroup.parent
			global oblist
			oblist = []
			get_children(lodgroup.children)
			for ob in oblist:
				print("deleting",ob)
				# first show, then select!
				ob.hide_set(False, view_layer=bpy.context.view_layer)
				ob.select_set(True)
		except:
			print("Deleted lonely lodgroup with no LOD levels!")
		bpy.ops.object.delete(use_global=True)
	for ob in bpy.context.scene.objects:
		# if we have more than one mesh we have to add a lod group node
		# in some cases, a model is our root (eg. fence), then we add the lodgroup as the new root
		if type(ob.data) == bpy.types.Mesh:
			if ob.name.startswith('sphere') or ob.name.startswith('orientedbox') or ob.name.startswith('capsule'): pass
			else:
				# special cases
				if ob.parent_type == 'BONE':
					# sometimes the main mesh is child of a bone...
					ob.matrix_local = mathutils.Matrix()
					# it has to be some NIF dummy object, so delete it!
					if not ob.vertex_groups:
						ob.select_set(True)
					# it shouldn't be parented to a bone, nif sometimes does this
					else:
						meshes.append(ob)
				# this has to be lodded
				else:
					meshes.append(ob)
	bpy.ops.object.delete(use_global=True)
	
	# only add a lodgroup if needed
	if numlods > 1:
		lodgroup = create_empty(root,"lodgroup",mathutils.Matrix())
		# when obs are parented to empties with offset it will cause trouble!
		# decide what the parent should be
		for i in range(numlods):
			# create lod level if needed
			if len(meshes) > 1:
				lodlevel = create_empty(lodgroup,"LOD"+str(i),mathutils.Matrix())
				parent = lodlevel
			else:
				parent = lodgroup
			# copy for new lod levels, assign high detail to lodgroup
			# could also try to copy the empties here, but not much need for that
			for ob in meshes:
				if i > 0:
					lod = ob.copy()
					lod.data = ob.data.copy()
					lod.name = ob.name + "_LOD"+str(i)
					bpy.context.scene.collection.objects.link(lod)
					LOD(lod, i)
					lod.parent = parent
					mod = lod.modifiers.new('Decimator', 'DECIMATE')
					mod.ratio = 1/(i+rate)
				else: 
					ob.parent = parent
	# maybe a final cleanup
	# if armature > clear any empties without children
				
def process(operator, context, files = [], filepath = "", numlods = 1, rate = 1):
	dir = os.path.dirname(filepath)
	starttime = time.time()

	clear_scene()
	print("Starting Batch Processing")

	for file in files:
		if file.name.endswith(".bfb"):
			bpy.ops.import_scene.bluefang_bfb(filepath = os.path.join(dir, file.name), use_custom_normals = True)
			add_lods(numlods, rate)
			bpy.ops.export_scene.bluefang_bfb(filepath = os.path.join(dir, file.name)+"new.bfb", author_name="HENDRIX", export_materials = False)
		elif file.name.endswith(".nif"):
			try:
				bpy.ops.import_scene.nif(filepath = os.path.join(dir, file.name), combine_vertices = True, axis_forward='X', axis_up='Y')
				add_lods(numlods, rate)
				bpy.ops.export_scene.bluefang_bfb(filepath = os.path.join(dir, file.name).replace(".nif",".bfb"), author_name="HENDRIX", export_materials = True, fix_root_bones = True)
			except: print("NIF import didn't work")
		else: continue
		clear_scene()
	success = '\nFinished Batch LOD processing in %.2f seconds\n' %(time.time()-starttime)
	print(success)
	return {'FINISHED'}