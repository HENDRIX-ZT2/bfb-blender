import logging

import bpy
import math
import time

from common_bfb import create_ob

# references
# https://technology.riotgames.com/news/compressing-skeletal-animation-data
# https://takinginitiative.net/2020/03/07/an-idiots-guide-to-animation-compression/
# https://animcoding.com/post/animation-tech-intro-part-2-compression/


def find_in_group(group, t, i):
	for fcurve in group.channels:
		if fcurve.data_path == t and fcurve.array_index == i:
			return fcurve


def loop_fcurve_tangents():
	logging.info("starting loop_fcurve_tangents")
	before = {}
	after = {}
	for action in bpy.data.actions:
		for subtype in ("Idle", "Ahead"):
			# this anim follows the naming convention
			if "_" in action.name:
				# this is not a transition anim
				if "_2" not in action.name:
					main = action.name.split("_")[0]
					act_name = f"{main}_{subtype}"
					if act_name in bpy.data.actions:
						before[action] = bpy.data.actions[act_name]
						after[action] = bpy.data.actions[act_name]
				if "_2" in action.name:
					main_before, main_after = action.name.split("_2")
					name_before = f"{main_before}_{subtype}"
					if name_before in bpy.data.actions:
						before[action] = bpy.data.actions[name_before]
					name_after = f"{main_after}_{subtype}"
					if name_after in bpy.data.actions:
						before[action] = bpy.data.actions[name_after]
			else:
				logging.warning(
					f"{action.name} does not follow the naming convention 'ANIMGROUP_ANIM' or for transitions 'ANIMGROUP_2ANIMGROUP'")

	# eventually also check for transitions, make sure they match up and interpolate tangents between anims
	for action in bpy.data.actions:

		matches = True
		logging.info(f"Looping {action.name}")

		# if they were not added in the first place, skip now
		try:
			bef = before[action]
			aft = after[action]
		except:
			continue
		for group in action.groups:
			# set or create the other groups
			try:
				bgroup = bef.groups[group.name]
			except:
				bgroup = group
			try:
				agroup = aft.groups[group.name]
			except:
				agroup = group

			# go through all fcurves of that bone
			for fcurve in group.channels:

				# equivalent curves from before and after anims
				try:
					bcurve = find_in_group(bgroup, fcurve.data_path, fcurve.array_index)
				except:
					bcurve = fcurve
				try:
					acurve = find_in_group(agroup, fcurve.data_path, fcurve.array_index)
				except:
					acurve = fcurve

				# the keys
				try:
					keys_before = bcurve.keyframe_points
					keys_this = fcurve.keyframe_points
					keys_after = acurve.keyframe_points
				except:
					logging.warning("An fcurve is missing")
					break

				# get both tangents
				if len(keys_this) > 1:
					lfhandle = keys_this[1].co - keys_this[0].co
					rfhandle = keys_this[-1].co - keys_this[-2].co

					# get the last tangent of the preceding anim
					if len(keys_before) > 1:
						bhandle = keys_before[-1].co - keys_before[-2].co
					# then cycle
					else:
						bhandle = rfhandle
					# get the first tangent of the following anim
					if len(keys_after) > 1:
						ahandle = keys_after[1].co - keys_after[0].co
					# then cycle
					else:
						ahandle = lfhandle

					# set the handle
					keys_this[0].handle_right_type = "FREE"
					keys_this[-1].handle_left_type = "FREE"
					fac_r = keys_this[1].co[0] - keys_this[0].co[0]
					fac_l = keys_this[-1].co[0] - keys_this[-2].co[0]

					# TODO: is this the right way to do this?
					# interpolate with the main anim or with its own ends
					if "_2" in action.name:
						right_h = lfhandle + bhandle
						left_h = rfhandle + ahandle
					# only use the foreign handles for loops
					else:
						right_h = ahandle + bhandle
						left_h = ahandle + bhandle
					keys_this[0].handle_right = keys_this[0].co + right_h.normalized() * fac_r / 2
					keys_this[-1].handle_left = keys_this[-1].co - left_h.normalized() * fac_l / 2
				if group.name not in ("Bip01",) and "*" not in group.name:
					for a, b in ((keys_before[-1].co[1], keys_this[0].co[1]),
								 (keys_this[-1].co[1], keys_after[0].co[1])):
						close = math.isclose(a, b, rel_tol=0.0000000002, abs_tol=0.000000000001)
						if not close:
							matches = False
		if not matches:
			logging.warning(f"transition does not line up for {action.name}")


def is_constrained_armature(ob):
	#finds an armature either via name (first) or if it has constraints (slower fallback)
	if ob.type == "ARMATURE":
		if ob.name.startswith("*"):
			return True
		for name, p_bone in ob.pose.bones.items():
			if p_bone.constraints:
				ob.name = f"*{ob.name}"
				return True
	return False

