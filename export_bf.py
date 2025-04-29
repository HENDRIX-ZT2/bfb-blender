import logging
import os
import time
import bpy
import mathutils

from bfb_gen.formats.bf import BfFile
from bfb_gen.formats.bf.enums.KeyType import KeyType
from .common_bfb import get_bfb_matrix, decompose_srt, blendername_to_bfbname, get_armature
import math


def write_nodes(dir_path, action, nodes, bones_data):
	file_path = os.path.join(dir_path, f"{action.name}.bf")
	bf = BfFile()
	fps = bpy.context.scene.render.fps
	duration = action.frame_range[1] / fps
	bf.header.version = bf.context.version = 2
	bf.header.duration = duration
	bf.header.num_nodes = len(nodes)
	bf.reset_field("nodes")
	for bf_node, (name, storage) in zip(bf.nodes, nodes):
		bf_node.name = blendername_to_bfbname(name)
		bf_node.num_mod_types = len(storage)
		bf_node.reset_field("modifiers")
		rest_scale, rest_rot, rest_trans, rest_quat = bones_data[name]
		for modifier, dt in zip(bf_node.modifiers, storage):
			fcurves = storage[dt]
			modifier.num_keys = len(fcurves[0].keyframe_points)

			if dt == "rotation_quaternion":
				modifier.key_type = KeyType.QUATERNION_LINEAR
				modifier.reset_field("keys")
				for bf_key, (frame, key) in zip(modifier.keys, keys_iter(fcurves)):
					quat = export_keymat(rest_rot, mathutils.Quaternion(key).to_matrix().to_4x4()).to_quaternion()
					set_quat(bf_key, fps, frame, quat, rest_quat)
			if dt == "rotation_euler":
				modifier.key_type = KeyType.QUATERNION_LINEAR
				modifier.reset_field("keys")
				for bf_key, (frame, key) in zip(modifier.keys, keys_iter(fcurves)):
					# todo: use to_euler( ) with compatible euler to fix distortions
					quat = export_keymat(rest_rot, mathutils.Euler(key).to_matrix().to_4x4()).to_quaternion()
					set_quat(bf_key, fps, frame, quat, rest_quat)

			if dt == "location":
				modifier.key_type = KeyType.LOC_LINEAR
				modifier.reset_field("keys")
				for bf_key, (frame, key) in zip(modifier.keys, keys_iter(fcurves)):
					trans = export_keymat(rest_rot, mathutils.Matrix.Translation(key)).to_translation() + rest_trans
					bf_key.time = frame / fps
					bf_key.x = trans.x
					bf_key.y = trans.y
					bf_key.z = trans.z

			if dt == "scale":
				modifier.key_type = KeyType.SCALE_LINEAR
				modifier.reset_field("keys")
				for bf_key, (frame, key) in zip(modifier.keys, keys_iter(fcurves)):
					bf_key.time = frame / fps
					bf_key.scale = key[0]
	bf.footer.start_time = 0.0
	bf.footer.end_time = duration
	bf.save(file_path)


def set_quat(bf_key, fps, frame, quat, rest_quat):
	bf_key.time = frame / fps
	# some quats need to be negated to match the rest_quat; otherwise the bf breaks bones when applied to nif models
	quat.make_compatible(rest_quat)
	bf_key.x = quat.x
	bf_key.y = quat.y
	bf_key.z = quat.z
	bf_key.w = quat.w


correction_local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
correction_local_inv = correction_local.inverted()


def export_keymat(rest_rot, key_matrix):
	key_matrix = correction_local_inv @ key_matrix @ correction_local
	return rest_rot @ key_matrix


def keys_iter(fcurves):
	num_keys = len(fcurves[0].keyframe_points)
	for i in range(0, num_keys):
		frame = fcurves[0].keyframe_points[i].co[0]
		yield frame, [fcurve.keyframe_points[i].co[1] for fcurve in fcurves]


def save(operator, context, filepath='', bake_actions=False, error=0.25, exp_power=2):
	start_time = time.time()
	errors = []
	if bake_actions:
		from . import bake_clean_actions
		errors.extend(bake_clean_actions.bake_and_clean(error, exp_power))

	dir_path = os.path.dirname(filepath)

	logging.info(f'Exporting BF animations into {dir_path}')

	bones_data = {}
	armature = get_armature()
	if armature:
		if armature.matrix_world.to_scale().length < 1:
			errors.append(
				"Your armature (or one of its parents) is scaled down in object mode! Apply scale to armature, objects and animations and try again.")
		for bone in armature.data.bones:
			rest_scale, rest_rot, rest_trans = decompose_srt(get_bfb_matrix(bone))
			bones_data[bone.name] = (rest_scale, rest_rot.to_4x4(), rest_trans, rest_rot.to_quaternion())
	else:
		logging.info("There's no armature, but are there animations at all (docking)?")
		for b_ob in bpy.data.objects:
			rest_scale, rest_rot, rest_trans = decompose_srt(mathutils.Matrix().to_4x4())
			bones_data[b_ob.name] = (rest_scale, rest_rot.to_4x4(), rest_trans, rest_rot.to_quaternion())

	for action in bpy.data.actions:
		# make sure it starts precisely at frame 0
		anim_start = action.frame_range[0]
		if anim_start != 0:
			errors.append(
				f"Action {action.name} did not start at frame 0! This has been automatically fixed!")
			for fcurve in action.fcurves:
				for kp in fcurve.keyframe_points:
					kp.co[0] -= anim_start

		# skip IKed / unbaked versions
		if action.name.startswith("*"):
			continue
		logging.info(f"Exporting {action.name}")

		constrained_name = f"*{action.name}"
		# does an unbaked version exist, then store it
		if constrained_name in bpy.data.actions and "secondary_" in action.name.lower():
			errors.append(
				f"Action {action.name} uses only bones keyframed in the original to avoid slithering.")
			# remember which bones were keyframed in the IK version for the secondary anim treatment
			raw_action_groups = [group.name for group in bpy.data.actions[constrained_name].groups]
		else:
			raw_action_groups = None
		nodes = []
		# these so-called action groups are the bones, ie one group contains all fcurves of one bone
		for group in action.groups:
			if group.name in bones_data:
				# do not export scale library
				if "!scale!" in action.name:
					continue
				# do not export helper bones for constraints
				if "*" in group.name:
					continue
				# if it is a secondary anim, limit the baked channels to what was keyframed initially
				if raw_action_groups and group.name not in raw_action_groups:
					continue

				# collect the fcurves here already
				dtypes = {"rotation_quaternion": 4, "rotation_euler": 3, "location": 3, "scale": 3}
				storage = {dt: [fcurve for fcurve in group.channels if fcurve.data_path.endswith(dt)] for dt in dtypes}

				# force export of scale for Bip01
				if not storage["scale"] and group.name == "Bip01":
					logging.debug(f"Adding scale curves for Bip01 in {group.name}")
					storage["scale"] = [
						action.fcurves.new(data_path='pose.bones["Bip01"].scale', index=i, action_group="Bip01")
						for i in range(3)]
					for fcurve in storage["scale"]:
						fcurve.keyframe_points.insert(0, 1)

				# sample sparse keying sets
				for dt, fcurves in storage.items():
					if not fcurves:
						continue
					same_amount_of_keys = all(
						len(fcu.keyframe_points) == len(fcurves[0].keyframe_points) for fcu in fcurves)
					if not same_amount_of_keys:
						logging.debug(f"{group.name} has differing keyframe numbers for {dt}")
						times = []
						# get all times
						for fcu in fcurves:
							for key in fcu.keyframe_points:
								key_time = key.co[0]
								if key_time not in times: times.append(key_time)
						times.sort()
						# sample and recreate all fcurves according to the full times
						for fcu in fcurves:
							samples = [fcu.evaluate(key_time) for key_time in times]
							fcu_dp, fcu_i = fcu.data_path, fcu.array_index
							action.fcurves.remove(fcu)
							fcu = action.fcurves.new(fcu_dp, index=fcu_i, action_group=group.name)
							fcu.keyframe_points.add(count=len(times))
							fcu.keyframe_points.foreach_set("co", [x for co in zip(times, samples) for x in co])
							fcu.update()
						# get the new curves because we deleted the original ones
						storage[dt] = [fcurve for fcurve in group.channels if fcurve.data_path.endswith(dt)]

				for dt, channel_count in dtypes.items():
					fcurves = storage[dt]
					if len(fcurves) == channel_count:
						continue
					if fcurves:
						errors.append(
							f"Incomplete {dt} key set in bone {group.name} for action {action.name}")
					storage.pop(dt)

				nodes.append((group.name, storage))
		write_nodes(dir_path, action, nodes, bones_data)
	logging.info(f"Finished BF Export in {time.time() - start_time:.2f} seconds")
	return errors
