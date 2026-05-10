import logging

import bpy
import os
import mathutils
import time

from common_bfb import *
from import_bfb import assign_to_lod


def clear_scene():
	#set the visible layers for this scene
	# todo: make all collisions visible?
	# bpy.context.scene.layers = [True for i in range(0,20)]
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete(use_global=True)
	for cat in (bpy.data.objects, bpy.data.materials,):
		for thing in cat:
			thing.user_clear()
			cat.remove(thing)


def add_lods(num_lods, rate):
	root = None
	meshes = []
	lodgroup = None
	for ob in bpy.context.scene.objects:
		if ob.type in ("EMPTY", "ARMATURE"):
			if ob.name.startswith("lodgroup"):
				logging.info("BFB model already has lodgroups!")
				lodgroup = ob
			if not ob.parent:
				root = ob
	# lodgroup mustn't be the root!
	if not root:
		root = create_empty(None, "AutoRoot", mathutils.Matrix())
	# delete the existing lodgroup and low detail lods
	for coll_name in bpy.context.view_layer.layer_collection.children.keys():
		hide_collection(coll_name, False)
	if lodgroup and lodgroup.children:
		logging.debug("Found lodgroup, deleting children...")
		# parent lod0 to lodgroup's parent
		lod0 = lodgroup.children[0]
		lod0.parent = lodgroup.parent
		# remove rest of the lodgroup and its children - add them later if needed
		for ob in lodgroup.children_recursive:
			bpy.data.objects.remove(ob)
		bpy.data.objects.remove(lodgroup)
	for ob in bpy.context.scene.objects:
		# if we have more than one mesh we have to add a lod group node
		# in some cases, a model is our root (e.g. fence), then we add the lodgroup as the new root
		if ob.type == "MESH":
			if ob.name.startswith('sphere') or ob.name.startswith('orientedbox') or ob.name.startswith('capsule'):
				pass
			else:
				# special cases
				if ob.parent_type == 'BONE':
					# sometimes the main mesh is child of a bone...
					ob.matrix_local = mathutils.Matrix()
					if not ob.vertex_groups:
						logging.warning(
							f"{ob.name} was deleted as it was parented to a bone but had no vertex groups - NIF dummy object?")
						bpy.data.objects.remove(ob)
					# it shouldn't be parented to a bone, nif sometimes does this
					else:
						meshes.append(ob)
				# this has to be lodded
				else:
					meshes.append(ob)

	# only add a lodgroup if needed
	if num_lods > 1:
		lodgroup = create_empty(root, "lodgroup", mathutils.Matrix())
		# when obs are parented to empties with offset it will cause trouble!
		# decide what the parent should be
		for i in range(num_lods):
			# create lod level if needed
			if len(meshes) > 1:
				lodlevel = create_empty(lodgroup, f"LOD{i}", mathutils.Matrix())
				parent = lodlevel
			else:
				parent = lodgroup
			# copy for new lod levels, assign high detail to lodgroup
			# could also try to copy the empties here, but not much need for that
			for ob in meshes:
				if i > 0:
					lod = ob.copy()
					lod.data = ob.data.copy()
					lod.name = f"{ob.name}_LOD{i}"
					for coll in ob.users_collection:
						coll.objects.link(lod)
					assign_to_lod(lod, i)
					lod.parent = parent
					mod = lod.modifiers.new('Decimator', 'DECIMATE')
					mod.ratio = 1 / (i + rate)
				else:
					ob.parent = parent
	# maybe a final cleanup
	# if armature > clear any empties without children


def process(operator, context, files=[], filepath="", num_lods=1, rate=1):
	dir = os.path.dirname(filepath)
	starttime = time.time()

	clear_scene()
	print("Starting Batch Processing")

	for file in files:
		if file.name.endswith(".bfb"):
			bpy.ops.import_scene.bluefang_bfb(filepath=os.path.join(dir, file.name), use_custom_normals=True)
			add_lods(num_lods, rate)
			bpy.ops.export_scene.bluefang_bfb(filepath=os.path.join(dir, file.name) + "new.bfb", author_name="HENDRIX",
											  export_materials=False)
		elif file.name.endswith(".nif"):
			try:
				bpy.ops.import_scene.nif(filepath=os.path.join(dir, file.name), combine_vertices=True, axis_forward='X',
										 axis_up='Y')
				add_lods(num_lods, rate)
				bpy.ops.export_scene.bluefang_bfb(filepath=os.path.join(dir, file.name).replace(".nif", ".bfb"),
												  author_name="HENDRIX", export_materials=True)
			except:
				print("NIF import didn't work")
		else:
			continue
		clear_scene()
	success = '\nFinished Batch LOD processing in %.2f seconds\n' % (time.time() - starttime)
	print(success)
	return {'FINISHED'}
