import os
import time
import bpy
import mathutils
from struct import iter_unpack, calcsize, unpack_from

from .common_bfb import get_bfb_matrix, decompose_srt, bfbname_to_blendername, create_empty

def load(operator, context, files = [], filepath = ""):
	starttime = time.clock()
	scene = bpy.context.scene
	fpms = scene.render.fps / 1000
	bones_data = {}
	info = {1  : ("=H9h", "QUAD", "location", (1,2,3), 1000),
			2  : ("=H3h", "LINEAR", "location", (1,2,3), 1000),
			6  : ("=H3h", "QUAD", "rotation_euler", (1,), 1000),
			7  : ("=H3h", "QUAD", "rotation_euler", (1,), 1000),
			8  : ("=H3h", "QUAD", "rotation_euler", (1,), 1000),
			12 : ("=H7h", "QUAD", "rotation_quaternion", (4,1,2,3), 10000),
			14 : ("=H4h", "LINEAR", "rotation_quaternion", (4,1,2,3), 10000),
			16 : ("=HB2h", "QUAD", "scale", (1,1,1), 50),
			17 : ("=HB", "LINEAR", "scale", (1,1,1), 50)}
	src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
	if src_armatures:
		armature = src_armatures[0]
		for bone in armature.data.bones:
			rest_scale, rest_rot, rest_trans = decompose_srt(get_bfb_matrix(bone))
			rest_rot_inv = rest_rot.inverted()
			rest_quat_inv = rest_rot_inv.to_quaternion()
			bones_data[bone.name] = (rest_scale, rest_rot_inv, rest_quat_inv, rest_trans)
		for anim in files:
			read_bf(os.path.dirname(filepath), anim.name, armature, bones_data, info, fpms)
		success = '\nFinished BF Import in %.2f seconds\n' %(time.clock()-starttime)
		print(success)
		return {'FINISHED'}
	else:
		print("The scene doesn't contain any armature! If you want to do skeletal anims, import a BFB file and try again!")
		for anim in files:
			read_bf_empties(os.path.dirname(filepath), anim.name, info, fpms)
	return {'FINISHED'}
	
def read_bf_empties(dir, anim, info, fpms):
	print("Reading",anim)
	with open(os.path.join(dir, anim), 'rb') as f:
		datastream = f.read()
		
		#we only want to get the anim set and anim eg. Stand_Idle so cull the stuff before, if there is any
		filename ="_".join(anim[:-3].split("_")[-2:])
		
		num_bones = unpack_from('= h', datastream, 8)[0]
		pos = 12
		#now go through all blocks of the BF file and extract the data
		for bone in range(0,num_bones):
			bone_name = bfbname_to_blendername(datastream[pos:pos+32])
			#figure out how many datablocks there are and which type
			#num_blocks = getshort(pos+32)
			next_bone = unpack_from('= h', datastream, pos+36)[0] + pos
			
			try: ob = bpy.data.objects[bone_name]
			except: ob = create_empty(None,bone_name,mathutils.Matrix())
			
			action = bpy.data.actions.new(name = filename+bone_name)
			action.use_fake_user = True
			
			ob.animation_data_create()
			ob.animation_data.action = action
			
			pos += 44
			while pos < next_bone:
				mod_identifier, num_keys, num_bytes = unpack_from('= 3h', datastream, pos)
				try:
					fmt, interp, data_type, key_i, scale_fac = info[mod_identifier]
					i_curves = range(0, len(key_i))
					#eulers: only create once
					if data_type == "rotation_euler":
						ob.rotation_mode = "XYZ"
						if mod_identifier == 6:
							i_curves = (0,)
						elif mod_identifier == 7:
							i_curves = (1,)
						elif mod_identifier == 8:
							i_curves = (2,)
					elif data_type == "rotation_quaternion":
						ob.rotation_mode = "QUATERNION"
					#initialize the fcurves
					fcurves = [action.fcurves.new(data_path = data_type, index = i, action_group = "LocRotScale") for i in i_curves]

					#read the data and process it
					for element in iter_unpack(fmt, datastream[8+pos : 8+pos+calcsize(fmt)*num_keys]):
						#add the keys
						for fcurve, key in zip(fcurves, [element[x]/scale_fac for x in key_i]):
							fcurve.keyframe_points.insert(element[0]*fpms, key).interpolation = interp
					pos += num_bytes
				except:
					print("Unknown modifier identifier! Please report type",mod_identifier,"to HENDRIX.")
					continue
			pos = next_bone
			
def read_bf(dir, anim, armature, bones_data, info, fpms):
	print("Reading",anim)
	with open(os.path.join(dir, anim), 'rb') as f:
		datastream = f.read()
		
		#we only want to get the anim set and anim eg. Stand_Idle so cull the stuff before, if there is any
		filename = "_".join(anim[:-3].split("_")[-2:])
		
		armature.animation_data_create()
		action = bpy.data.actions.new(name = filename)
		action.use_fake_user = True
		armature.animation_data.action = action
			
		num_bones = unpack_from('= h', datastream, 8)[0]
		pos = 12
		#now go through all blocks of the BF file and extract the data
		for bone in range(0,num_bones):
			name = bfbname_to_blendername(datastream[pos:pos+32])
			#figure out how many datablocks there are and which type
			#num_blocks = getshort(pos+32)
			next_bone = unpack_from('= h', datastream, pos+36)[0] + pos
			if name in bones_data:
				rest_scale, rest_rot_inv, rest_quat_inv, rest_trans = bones_data[name]
				#now look at the mod identifiers and go over all blocks we know
				pos += 44
				while pos < next_bone:
					mod_identifier, num_keys, num_bytes = unpack_from('= 3h', datastream, pos)
					try:
						fmt, interp, data_type, key_i, scale_fac = info[mod_identifier]
					except:
						pos += num_bytes
						print("Unknown modifier identifier! Please report type",mod_identifier,"to HENDRIX.")
						continue
						
					i_curves = range(0, len(key_i))
					
					#eulers: only create once
					if data_type == "rotation_euler":
						armature.pose.bones[name].rotation_mode = "XYZ"
						rest_euler = rest_rot_inv.to_euler()
						if mod_identifier == 6:
							i_curves = (0,)
						elif mod_identifier == 7:
							i_curves = (1,)
						elif mod_identifier == 8:
							i_curves = (2,)
						
					#initialize the fcurves
					fcurves = [action.fcurves.new(data_path = 'pose.bones["'+name+'"].'+data_type, index = i, action_group = name) for i in i_curves]
					
					#read the data and process it
					for element in iter_unpack(fmt, datastream[8+pos : 8+pos+calcsize(fmt)*num_keys]):
						if data_type == "scale":
							a = [element[x]/scale_fac for x in key_i]
						elif data_type == "location":
							a = (mathutils.Vector([element[x]/scale_fac for x in key_i]) - rest_trans) * rest_rot_inv
							a = (a[1], -a[0], a[2])
						elif data_type == "rotation_quaternion":
							a = rest_quat_inv.cross(mathutils.Quaternion([element[x]/scale_fac for x in key_i]))
							a = (a[0], -a[2], a[1], a[3])
						elif data_type == "rotation_euler":
							#this is NOT correct - see stegosaurus plates
							#it only works on sloth mouth by chance
							a = (-element[1]/scale_fac + rest_euler[i_curves[0]],)
							#the keys should probably be corrected in a second pass from blender
						#add the keys
						for fcurve, key in zip(fcurves, a):
							fcurve.keyframe_points.insert(element[0]*fpms, key).interpolation = interp
					pos += num_bytes
			pos = next_bone
		
		if not "_2" in filename:
			for fcurve in action.fcurves:
				mod = fcurve.modifiers.new('CYCLES')
				mod.mode_after = 'REPEAT_OFFSET'
				mod.mode_before = 'REPEAT_OFFSET'
