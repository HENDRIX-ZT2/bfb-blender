import os
import time
import bpy
import mathutils
from struct import pack, calcsize
from .common_bfb import get_bfb_matrix, decompose_srt, blendername_to_bfbname, get_armature
import math

def write_nodes(dirname, action, nodes, fps):
	stream = b''.join([pack('=I f I', 2, action.frame_range[1]/fps, len(nodes)), b"".join(nodes), pack('=f H 6s f H 12s', 0.0, 6, b"start", action.frame_range[1]/fps, 5, b"end ")])
	with open(os.path.join(dirname, action.name+".bf"), 'wb') as f:
		f.write(stream)
	
#round a float to an integer
def rint(f): return int(round(f))

correction_local = mathutils.Euler((math.radians(90), 0, math.radians(90))).to_matrix().to_4x4()
correction_local_inv = correction_local.inverted()
def export_keymat(rest_rot, key_matrix):
	key_matrix = correction_local_inv * key_matrix * correction_local
	return rest_rot * key_matrix

def save(operator, context, filepath='', bake_actions = False, error = 0.25, exp_power = 2):
	
	starttime = time.clock()
	errors = []
	if bake_actions:
		from . import bake_clean_actions
		errors.extend(bake_clean_actions.bake_and_clean(error, exp_power))
	
	dirname = os.path.dirname(filepath)
	
	print('Exporting BF animations into',dirname,'...')
	
	fps = bpy.context.scene.render.fps
	fpms = fps / 1000
	
	armature = get_armature()
	if armature:
		bones_data = {}
		for bone in armature.data.bones:
			bonerestmat = get_bfb_matrix(bone)
			rest_scale, rest_rot, rest_trans = decompose_srt(bonerestmat)
			bones_data[bone.name] = (rest_scale, rest_rot.to_4x4(), rest_trans)

		for action in bpy.data.actions:
			print("Exporting",action.name)
			
			#make sure it starts precisely at frame 0
			anim_start = action.frame_range[0]
			if anim_start != 0:
				errors.append("Action "+action.name+" did not start at frame 0! This has been automatically fixed!")
				for fcurve in action.fcurves:
					for i in range(0, len(fcurve.keyframe_points)):
						fcurve.keyframe_points[i].co[0] -= anim_start
			
			#skip IKed / unbaked versions
			if "*" in action.name: continue
			
			#does an unbaked version exist, then store it
			if "*"+action.name in bpy.data.actions and "secondary_" in action.name.lower():
				errors.append("Action "+action.name+" uses only bones keyframed in the original to avoid slithering.")
				#remember which bones were keyframed in the IK version for the secondary anim treatment
				raw_action_groups = [group.name for group in bpy.data.actions["*"+action.name].groups]
			
			nodes = []
			#these so called action groups are the bones, ie one group contains all fcurves of one bone
			for group in action.groups:
				if group.name in bones_data:
					#do not export constrained animations prior to baking
					if "*" in group.name: continue
					#if it is a secondary anim, limit the baked channels to what was keyframed initially
					if "*"+action.name in bpy.data.actions and "secondary_" in action.name.lower():
						if group.name not in raw_action_groups: continue
					
					rest_scale, rest_rot, rest_trans = bones_data[group.name]
					key_bytes = []
					num_mod_types = 0
					
					#collect the fcurves here already
					rotations = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("quaternion")]
					translations = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("location")]
					eulers = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("euler")]
					scales = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("scale")]
					
					#force export of scale for Bip01
					if not scales and group.name == "Bip01":
						print("Adding scale curves for Bip01 in "+group.name)
						scales = [action.fcurves.new(data_path = 'pose.bones["Bip01"].scale', index = i, action_group = "Bip01") for i in range(3)]
						for fcurve in scales:
							fcurve.keyframe_points.insert(0, 1)
					
					#sample sparse keying sets - treat rot and trans independently
					for fcurves in (rotations, translations, eulers):
						same_amount_of_keys = all(len(fcu.keyframe_points) == len(fcurves[0].keyframe_points) for fcu in fcurves)
						if not same_amount_of_keys:
							print(group.name+" has differing keyframe numbers for each fcurve")
							times = []
							#get all times
							for fcu in fcurves:
								for key in fcu.keyframe_points:
									key_time = key.co[0]
									if key_time not in times: times.append(key_time)
							times.sort()
							#sample and recreate all fcurves according to the full times
							for fcu in fcurves:
								samples = [fcu.evaluate(key_time) for key_time in times]
								fcu_dp, fcu_i = fcu.data_path, fcu.array_index
								action.fcurves.remove(fcu)
								fcu = action.fcurves.new(fcu_dp, index=fcu_i, action_group=group.name)
								fcu.keyframe_points.add(count=len(times))
								fcu.keyframe_points.foreach_set("co", [x for co in zip(times, samples) for x in co])
								fcu.update()
							#get the new curves because we deleted the original ones
							rotations = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("quaternion")]
							translations = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("location")]
							eulers = [fcurve for fcurve in group.channels if fcurve.data_path.endswith("euler")]
					
					#report differing key lengths and missing channels
					if rotations:
						if len(rotations) != 4:
							errors.append("Incomplete ROT key set in bone "+group.name+" for action "+action.name)
						else:
							num_keys = len(rotations[0].keyframe_points)
							num_mod_types += 1
							key_bytes.append(pack('=4H', 14, num_keys, 8+num_keys*10, 0))
							for i in range(0, num_keys):
								frame = rotations[0].keyframe_points[i].co[0]
								quat = export_keymat(rest_rot, mathutils.Quaternion([fcurve.keyframe_points[i].co[1] for fcurve in rotations]).to_matrix().to_4x4()).to_quaternion()
								key_bytes.append(pack('=H4h', rint(frame/fpms), rint(quat.x*10000), rint(quat.y*10000), rint(quat.z*10000), rint(quat.w*10000)))
																
					if translations:
						if len(translations) != 3:
							errors.append("Incomplete LOC key set in bone "+group.name+" for action "+action.name)
						else:
							num_keys = len(translations[0].keyframe_points)
							num_mod_types += 1
							key_bytes.append(pack('=4H', 2, num_keys, 8+num_keys*8, 0))
							for i in range(0, num_keys):
								frame = translations[0].keyframe_points[i].co[0]
								trans = export_keymat(rest_rot, mathutils.Matrix.Translation( [fcurve.keyframe_points[i].co[1] for fcurve in translations] ) ).to_translation() + rest_trans
								key_bytes.append(pack('=H3h', rint(frame/fpms), rint(trans.x * 1000), rint(trans.y * 1000), rint(trans.z * 1000)))
					
					#report differing key lengths and missing channels
					if eulers:
						if len(eulers) != 3:
							errors.append("Incomplete EULER key set in bone "+group.name+" for action "+action.name)
						else:
							num_keys = len(eulers[0].keyframe_points)
							num_mod_types += 1
							key_bytes.append(pack('=4H', 14, num_keys, 8+num_keys*10, 0))
							for i in range(0, num_keys):
								frame = eulers[0].keyframe_points[i].co[0]
								quat = export_keymat(rest_rot, mathutils.Euler([fcurve.keyframe_points[i].co[1] for fcurve in eulers]).to_matrix().to_4x4() ).to_quaternion()
								key_bytes.append(pack('=H4h', rint(frame/fpms), rint(quat.x*10000), rint(quat.y*10000), rint(quat.z*10000), rint(quat.w*10000)))
																
					if scales:
						num_keys = min([len(channel.keyframe_points) for channel in scales])
						#if num_keys > 2:
						num_mod_types += 1
						key_bytes.append(pack('=4H', 17, num_keys, 8+num_keys*3, 0))
						for i in range(0, num_keys):
							frame = scales[0].keyframe_points[i].co[0]
							scale = max(0, min(255, rint(scales[0].keyframe_points[i].co[1] * 50)))
							key_bytes.append(pack('=HB', rint(frame/fpms), scale))
				
					
					key_bytes = b"".join(key_bytes)
					nodes.append(pack('=32s H 2B H I 2B', blendername_to_bfbname(group.name).encode('utf-8'), num_mod_types, 204, 204, 44+len(key_bytes), 0, 204, 204) + key_bytes)
			write_nodes(dirname, action, nodes, fps)
	else:
		print("There's no armature, but are there animations at all (docking)?")
		for action in bpy.data.actions:
			print("Exporting",action.name)
			nodes = []
			#these so called action groups are the bones, ie one group contains all fcurves of one bone
			for group in action.groups:
			
				key_bytes = []
				num_mod_types = 0
				#we need two dicts to map all the info
				info = {"location"  : ("=H3h", (2,), 1000),
						"rotation_euler"  : ("=H3h", (6,7,8), 1000),
						"rotation_quaternion" : ("=H4h", (14,), 10000),
						"scale" : ("=HB", (17,), 50)}
				info2 = {2 : (0,1,2),
						6 : (0,),
						7 : (1,),
						8 : (2,),
						14 : (1,2,3,0),
						17 : (0,)}
						
				for data_type in ("rotation_euler", "rotation_quaternion", "location", "scale"):
					fcurves = [fcurve for fcurve in group.channels if fcurve.data_path.endswith(data_type)]
					if fcurves:
						fmt, mod_ids, scale_fac = info[data_type]
						for mod_id in mod_ids:
							key_i = info2[mod_id]
							num_keys = min([len(channel.keyframe_points) for channel in fcurves])
							num_mod_types += 1
							key_bytes.append(pack("=4H", mod_id, num_keys, 8+num_keys*calcsize(fmt), 0))
							for i in range(0, num_keys):
								key = [rint(fcurves[x].keyframe_points[i].co[1] * scale_fac) for x in key_i]
								#we are using quadratic keys here and thus we need to fake the tangents or whatever
								if data_type == "rotation_euler": key.extend((0,0))
								key_bytes.append(pack(fmt, rint((fcurves[0].keyframe_points[i].co[0])/fpms), *key))
				key_bytes = b"".join(key_bytes)
				nodes.append(pack('=32s H 2B H I 2B', blendername_to_bfbname(action.name).encode('utf-8'), num_mod_types, 204, 204, 44+len(key_bytes), 0, 204, 204) + key_bytes)
			write_nodes(dirname, action, nodes, fps)
	success = '\nFinished BF Export in %.2f seconds\n' %(time.clock()-starttime)
	print(success)
	return errors