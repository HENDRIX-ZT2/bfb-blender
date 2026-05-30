import logging
import os
import time
import xml.etree.ElementTree as ET

import bpy
import mathutils
import numpy as np

from bfb_gen.formats.bf import BfFile
from bfb_gen.formats.bf.compounds.TxtKey import TxtKey
from bfb_gen.formats.bf.enums.KeyType import KeyType
from modules_export.armature import clear_pose
from modules_import.anim import Animation
from util import rdp
from util.transforms import Corrector
from common_bfb import name_export, get_armature
import bake_clean_actions


LOC = "location"
ROT = "rotation_quaternion"
EUL = "rotation_euler"
EUL_X = f"{EUL}.X"
EUL_Y = f"{EUL}.Y"
EUL_Z = f"{EUL}.Z"
SCL = "scale"
FLO = "float"

key_map = {
	ROT: KeyType.QUATERNION_LINEAR,
	LOC: KeyType.LOC_LINEAR,
	SCL: KeyType.SCALE_LINEAR,
	EUL_X: KeyType.EULER_X_QUADRATIC,
	EUL_Y: KeyType.EULER_Y_QUADRATIC,
	EUL_Z: KeyType.EULER_Z_QUADRATIC,
}

def handle_legacy_name(b_struct):
	# do not export helper bones for constraints
	if b_struct.name.startswith("*"):
		logging.warning(f"Removing * from legacy name for {b_struct.name}")
		b_struct.name = b_struct.name[1:]


def fill_in_rest_data(m_name, mat_local_to_parent, rest_data):
	pos, quat, sca = mat_local_to_parent.decompose()
	rest_data[m_name] = {}
	rest_data[m_name][ROT] = [quat.x, quat.y, quat.z, quat.w]
	rest_data[m_name][LOC] = pos
	rest_data[m_name][SCL] = sca
	eul = quat.to_euler()
	rest_data[m_name][EUL] = eul
	rest_data[m_name][EUL_X], rest_data[m_name][EUL_Y], rest_data[m_name][EUL_Z] = eul


def reasonably_close(a, b):
	return np.allclose(a, b, rtol=1e-04, atol=1e-06, equal_nan=False)


def needs_keyframes(keys):
	"""Checks an array of keys and yields the indices that have temporal changes"""
	if len(keys):
		# get the first key
		key0 = keys[0]
		# go over the channels
		for ch_i, ch_v in enumerate(key0):
			# do keys differ from first key?
			if not reasonably_close(keys[:, ch_i], ch_v):
				yield ch_i


def sample_action(b_ob, b_action, bones_data, rest_data):
	first_frame, last_frame = b_action.frame_range
	first_frame = int(first_frame)
	last_frame = int(last_frame) + 1
	frame_count = last_frame - first_frame
	# create arrays for loc, rot, scale keys
	channel_storage = {b_bone_name: {
		ROT: np.zeros((frame_count, 4), float),
		EUL_X: np.zeros((frame_count, 1), float),
		EUL_Y: np.zeros((frame_count, 1), float),
		EUL_Z: np.zeros((frame_count, 1), float),
		LOC: np.zeros((frame_count, 3), float),
		SCL: np.zeros((frame_count, 3), float),
	} for b_bone_name in bones_data}
	# store pose data for b_action
	b_ob.animation_data.action = b_action
	for trg_frame, src_frame in enumerate(range(first_frame, last_frame)):
		store_pose_frame_info(b_ob, src_frame, trg_frame, bones_data, channel_storage, rest_data)

	# decide which channels to keyframe by determining if the keys are static
	for bone_name, channels in tuple(channel_storage.items()):
		if b_ob.type == "ARMATURE":
			b_target = b_ob.pose.bones[bone_name]
		elif bone_name == b_ob.name:
			b_target = b_ob
		else:
			logging.warning(f"Unknown target {bone_name}, skipping")
			channel_storage.pop(bone_name)
			continue
		# decide on rotation mode
		if b_target.rotation_mode == "QUATERNION":
			channels.pop(EUL_X)
			channels.pop(EUL_Y)
			channels.pop(EUL_Z)
		else:
			channels.pop(ROT)
		if "secondary" in b_action.name.lower() and bone_name not in b_action.groups:
			logging.debug(f"Discarding {bone_name} completely because it is not keyframes in {b_action.name}")
			# discard any bones that are not keyframed
			channel_storage.pop(bone_name)
			continue
		if bone_name == "Bip01" and not "secondary" in b_action.name.lower():
			# keep all channels
			continue
		# do not export helper bones for constraints
		elif bone_name.startswith("*"):
			channel_storage.pop(bone_name)
			continue
		for channel_id, keys in tuple(channels.items()):
			needed_axes = list(needs_keyframes(keys))
			# decimate channels that are static and identical to rest pose
			if not needed_axes and reasonably_close(keys[0], rest_data[bone_name][channel_id]):
				# no need to keyframe this bone, discard it
				logging.debug(f"Discarding {bone_name}.{channel_id}")
				channels.pop(channel_id)
		if not channels:
			channel_storage.pop(bone_name)
			logging.debug(f"Discarding {bone_name} completely")
	return channel_storage


def store_pose_frame_info(b_ob, src_frame, trg_frame, bones_data, channel_storage, rest_data):
	bpy.context.scene.frame_set(src_frame)
	bpy.context.view_layer.update()
	if b_ob.type == "ARMATURE":
		for b_name, p_bone in b_ob.pose.bones.items():
			# Get the final transform of the bone in its own local space...
			# then make it relative to the parent bone
			# transform is stored relative to the parent rest
			# whereas blender stores translation relative to the bone itself, not the parent
			matrix = bones_data[b_name] @ b_ob.convert_space(
				pose_bone=p_bone, matrix=p_bone.matrix, from_space='POSE', to_space='LOCAL')
			store_transform_data(channel_storage, rest_data, matrix, b_name, trg_frame)
	else:
		matrix = bones_data[b_ob.name] @ b_ob.matrix_local
		store_transform_data(channel_storage, rest_data, matrix, b_ob.name, trg_frame)

def store_transform_data(channel_storage, rest_data, matrix, name, frame):
	matrix = Corrector.export_keymat2(matrix)
	bone_storage = channel_storage[name]
	bone_storage[LOC][frame] = matrix.to_translation()
	key = matrix.to_quaternion()
	# some quats need to be negated to match the rest_quat; otherwise the bf breaks bones when applied to nif models
	key.make_compatible(rest_data[name][ROT])
	bone_storage[ROT][frame] = key.x, key.y, key.z, key.w
	bone_storage[SCL][frame] = matrix.to_scale()[0]
	euler = key.to_euler()
	euler.make_compatible(rest_data[name][EUL])
	bone_storage[EUL_X][frame], bone_storage[EUL_Y][frame], bone_storage[EUL_Z][frame] = euler

def write_nodes(reporter, dir_path, b_action, channel_storage, error_margins, write_txtkeys_files):
	file_path = os.path.join(dir_path, f"{b_action.name}.bf")
	bf = BfFile()
	fps = bpy.context.scene.render.fps
	first_frame, last_frame = b_action.frame_range
	frame_count = last_frame - first_frame
	duration = frame_count / fps
	# warn for locomotion sets if length is not a 'clean' fraction of a second
	locomotion_sets = ["Walk", "Run", "Gallop", "Trot", "Swim", "Crawl"]
	locomotion_list = [f"{s}_" for s in locomotion_sets] + [f"{s}Object_" for s in locomotion_sets]
	if any(s in b_action.name for s in locomotion_list):
		# todo - does it actually depend on the frame count or the length?
		if (frame_count * 10) % fps:
			reporter.show_warning(f"Change duration of {b_action.name} to enable wandering")
	bf.header.version = bf.context.version = 2
	bf.header.duration = duration
	bf.header.num_nodes = len(channel_storage)
	bf.reset_field("nodes")
	for bf_node, (name, storage) in zip(bf.nodes, channel_storage.items()):
		bf_node.name = name_export(name)
		bf_node.num_mod_types = len(storage)
		bf_node.reset_field("modifiers")
		for modifier, (dt, arr) in zip(bf_node.modifiers, storage.items()):

			times = np.arange(len(arr), dtype=float) / fps
			# use RDP to simplify the curve
			mask = rdp.get_mask(arr, error_margins[name])
			times = times[mask]
			arr = arr[mask]
			modifier.num_keys = len(arr)
			kt = key_map[dt]
			modifier.key_type = kt
			modifier.reset_field("keys")
			if dt == ROT:
				for bf_key, t, key in zip(modifier.keys, times, arr):
					bf_key.time = t
					bf_key.x, bf_key.y, bf_key.z, bf_key.w = key
			elif dt.startswith(EUL):
				for bf_key, t, key in zip(modifier.keys, times, arr):
					bf_key.time = t
					bf_key.value = key[0]
			elif dt == LOC:
				for bf_key, t, key in zip(modifier.keys, times, arr):
					bf_key.time = t
					bf_key.x, bf_key.y, bf_key.z = key
			elif dt == SCL:
				for bf_key, t, key in zip(modifier.keys, times, arr):
					bf_key.time = t
					bf_key.scale = key[0]
	create_txtkey(bf, 0.0, "start")
	if write_txtkeys_files:
		if b_action.pose_markers:
			root = ET.Element('TEXTKEY')
			for marker in b_action.pose_markers:
				ET.SubElement(root, "key", {"frame": str(marker.frame), "text": marker.name})
			ET.indent(root, space='\t', level=0)
			tree = ET.ElementTree(root)
			tree.write(os.path.join(dir_path, f"{b_action.name}.txtkeys"))
	else:
		# export any custom txtkeys
		for marker in b_action.pose_markers:
			create_txtkey(bf, marker.frame / fps, marker.name)
	create_txtkey(bf, duration, "end")
	bf.save(file_path)


def create_txtkey(bf, key_time, name):
	txtkey = TxtKey(bf.context)
	txtkey.time = key_time
	txtkey.string = name
	bf.footer.txtkeys.append(txtkey)


def save(reporter, filepath='', fix_tangents=False, error=0.25, exp_power=2, write_txtkeys_files=True):
	start_time = time.time()
	if fix_tangents:
		bake_clean_actions.loop_fcurve_tangents()

	dir_path = os.path.dirname(filepath)

	logging.info(f'Exporting BF animations into {dir_path}')

	bones_data = {}
	rest_data = {}
	error_margins = {}
	b_armature_ob = get_armature()

	if b_armature_ob:
		handle_legacy_name(b_armature_ob)
		handle_legacy_name(b_armature_ob.data)
		if not reasonably_close(b_armature_ob.matrix_world.to_scale(), (1.0, 1.0, 1.0)):
			reporter.show_warning(
				"Your armature (or one of its parents) is scaled in object mode! Apply scale to armature, objects and animations and try again.")
		for bone in b_armature_ob.data.bones:
			b_rest = Corrector.get_b_matrix(bone)
			bones_data[bone.name] = b_rest
			fill_in_rest_data(bone.name, Corrector.export_keymat2(b_rest), rest_data)
			# create error margins based on the amount of children
			# exp_power = 2 seems reasonable
			# a bone may have zero children, so add 1!
			error_margins[bone.name] = error / (len(bone.children_recursive) + 1) ** exp_power
		logging.debug(f"Error margins for each bone: {error_margins}")
	else:
		logging.info("There's no armature, but are there animations at all (docking)?")
		for b_ob in bpy.data.objects:
			b_rest = mathutils.Matrix(Corrector.local)
			bones_data[b_ob.name] = b_rest
			fill_in_rest_data(b_ob.name, Corrector.export_keymat2(b_rest), rest_data)
			error_margins[b_ob.name] = error ** exp_power

	if b_armature_ob:
		for b_action in list(bpy.data.actions):
			# do not export scale library
			if "!scale!" in b_action.name:
				continue
			handle_legacy_name(b_action)
			clear_pose(b_armature_ob)
			channel_storage = sample_action(b_armature_ob, b_action, bones_data, rest_data)
			logging.info(f"Exporting {b_action.name}")

			write_nodes(reporter, dir_path, b_action, channel_storage, error_margins, write_txtkeys_files)
	else:
		for b_ob in bpy.data.objects:
			if b_ob.animation_data and b_ob.animation_data.action:
				b_action = b_ob.animation_data.action
				channel_storage = sample_action(b_ob, b_action, bones_data, rest_data)
				logging.info(f"Exporting {b_action.name}")
				write_nodes(reporter, dir_path, b_action, channel_storage, error_margins, write_txtkeys_files)
	logging.info(f"Finished BF Export in {time.time() - start_time:.2f} seconds")
