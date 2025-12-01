import os
import time
import bpy
import mathutils
import logging

import numpy as np

from bfb_gen.formats.bf import BfFile
from modules_import.anim import Animation
from util.transforms import Corrector
from common_bfb import create_empty, get_armature, name_import


anim_sys = Animation()
info = {
	1: ("QUAD", "location", 3),
	2: ("LINEAR", "location", 3),
	6: ("QUAD", "rotation_euler", 1),
	7: ("QUAD", "rotation_euler", 1),
	8: ("QUAD", "rotation_euler", 1),
	12: ("QUAD", "rotation_quaternion", 4),
	14: ("LINEAR", "rotation_quaternion", 4),
	16: ("QUAD", "scale", 3),
	17: ("LINEAR", "scale", 3)}


def load(reporter, files=(), filepath="", set_fps=False):
	start_time = time.time()
	dir_path = os.path.dirname(filepath)
	if set_fps:
		bpy.context.scene.render.fps = 30
		logging.info("Adjusted scene FPS!")
	fps = bpy.context.scene.render.fps

	bones_data = {}
	armature = get_armature()
	if armature:
		for bone in armature.data.bones:
			bones_data[bone.name] = Corrector.get_bfb_matrix(bone).inverted()
	else:
		logging.info(
			"The scene doesn't contain any armature! If you want to do skeletal anims, import a BFB file and try again!")
	for bf_name in files:
		read_bf(dir_path, bf_name, armature, bones_data, fps)
	logging.info(f'Finished BF Import in {time.time() - start_time:.2f} seconds')
	return {'FINISHED'}


def read_bf(dir_path, bf_name, b_armature, bones_data, fps):
	logging.info(f"Reading {bf_name}")
	src_path = os.path.join(dir_path, bf_name)
	bf = BfFile()
	bf.load(src_path)
	# we only want to get the anim set and anim e.g. Stand_Idle so cull the stuff before, if there is any
	action_name = "_".join(bf_name[:-3].split("_")[-2:])
	if bones_data:
		b_action = anim_sys.create_action(b_armature, action_name)
	# now go through all blocks of the BF file and extract the data
	for node in bf.nodes:
		b_bone_name = name_import(node.name)
		dict_eulers = {}
		dict_times = {}
		# print(node.name, [int(m.key_type) for m in node.modifiers])
		if bones_data:
			if b_bone_name in bones_data:
				rest_inv = bones_data[b_bone_name]
				b_target = b_armature.pose.bones[b_bone_name]
			else:
				logging.warning(f"Bone '{b_bone_name}' is not found in armature, skipping")
				continue
		else:
			rest_inv = mathutils.Matrix(Corrector.local_inv)
			if b_bone_name in bpy.data.objects:
				b_ob = bpy.data.objects[b_bone_name]
			else:
				b_ob = create_empty(None, b_bone_name, mathutils.Matrix())
			b_action = anim_sys.create_action(b_ob, f"{action_name}_{b_bone_name}")
			b_bone_name = None
			b_target = b_ob
		# now look at the mod identifiers and go over all blocks we know
		for modifier in node.modifiers:
			interp, data_type, k_size = info[modifier.key_type]
			if data_type == "rotation_euler":
				b_target.rotation_mode = "XYZ"
			elif data_type == "rotation_quaternion":
				b_target.rotation_mode = "QUATERNION"

			times = np.empty(len(modifier.keys), float)
			keys = np.empty((len(modifier.keys), k_size), float)
			for i, k in enumerate(modifier.keys):
				times[i] = round(k.time * fps)
				# all the others can be imported on the fly
				if data_type == "scale":
					keys[i] = [k.scale, k.scale, k.scale]
				elif data_type == "location":
					keys[i] = Corrector.import_keymat(rest_inv, mathutils.Matrix.Translation(mathutils.Vector(
						[k.x, k.y, k.z]))).to_translation()
				elif data_type == "rotation_quaternion":
					keys[i] = Corrector.import_keymat(rest_inv, mathutils.Quaternion(
						[k.w, k.x, k.y, k.z]).to_matrix().to_4x4()).to_quaternion()
				elif data_type == "rotation_euler":
					keys[i] = k.value

			if data_type == "rotation_euler":
				dict_times[modifier.key_type] = times
				dict_eulers[modifier.key_type] = keys

			# do not create fcurves yet
			if modifier.key_type in (6, 7):
				continue
			# Have we just read the Euler Z curve data?
			elif modifier.key_type == 8:
				# get all times and resample the keys
				all_times = set()
				for v in dict_times.values():
					all_times.update(v)
				times = sorted(all_times)
				# handle missing key_types
				keys = np.empty((len(times), 3), float)
				keys[:] = rest_inv.inverted().to_euler()
				for i, x in enumerate(range(6, 9)):
					if x in dict_times:
						keys[:, i] = np.interp(times, dict_times[x], dict_eulers[x].flat)
				for i, key in enumerate(keys):
					keys[i] = Corrector.import_keymat(rest_inv,
										mathutils.Euler(key).to_matrix().to_4x4()).to_euler()
			# unsure how the extra data for quad is to be interpreted
			# if interp == "QUAD":
			# 	logging.info(f"{b_bone_name} {data_type} {interp}")
			# 	print(modifier)
			# create fcurves and keys
			key_range = tuple(range(keys.shape[1]))
			anim_sys.add_keys(b_action, data_type, key_range, None, times, keys, interp, n_bone=b_bone_name)

	if not "_2" in action_name:
		for fcurve in b_action.fcurves:
			mod = fcurve.modifiers.new('CYCLES')
			mod.mode_after = 'REPEAT_OFFSET'
			mod.mode_before = 'REPEAT_OFFSET'

	for txtkey in bf.footer.txtkeys:
		name = txtkey.string.strip()
		if name not in ("start", "end"):
			marker = b_action.pose_markers.new(name)
			marker.frame = round(txtkey.time * fps)