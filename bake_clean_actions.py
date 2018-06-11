import bpy
import math
import time

#########################################
#### Ramer-Douglas-Peucker algorithm ####
#########################################
# get altitude of vert
def altitude(point1, point2, pointn):
	"""Returns the altitude"""
	edge1 = point2 - point1
	edge2 = pointn - point1
	if edge2.length == 0:
		return 0
	elif edge1.length == 0:
		return edge2.length
	else:
		return math.sin(edge1.angle(edge2)) * edge2.length


#### get SplineVertIndices to keep
def simplify_RDP(splineVerts, local_error):
	# set first and last vert
	new_vert_indices = [0, len(splineVerts)-1]

	# iterate through the points
	#continue until it doesn't yield any more new_verts points
	#maybe simplify with new_vert as the while loop condition
	new_verts = 1
	while new_verts:
		new_verts = []
		for newIndex in range(len(new_vert_indices)-1):
			new_vert = 0
			alti_store = 0
			for i, point in enumerate(splineVerts[new_vert_indices[newIndex]+1:new_vert_indices[newIndex+1]]):
				alti = altitude(splineVerts[new_vert_indices[newIndex]], splineVerts[new_vert_indices[newIndex+1]], point)
				if alti > alti_store:
					alti_store = alti
					if alti_store >= local_error:
						new_vert = i+1+new_vert_indices[newIndex]
						new_verts.append(new_vert)
		if new_verts:
			new_vert_indices += new_verts
			new_vert_indices.sort()
	return new_vert_indices

		
def clean_group(group, type_id):
	#get all desired fcurves from group
	fcurves = [fcurve for fcurve in group.channels if fcurve.data_path.endswith(type_id)]
		
	#these are the vert indices that we are going to keep
	vert_indices = []
	for fcurve in fcurves:		
		fcurve_verts = [vcVert.co.to_3d() for vcVert in fcurve.keyframe_points.values()]
		
		#get the simplified keys for this fcurve
		#if we want to keep a key for one curve, we have to keep it for the whole set
		#so add the additional indices so we get nice tuples for export
		
		#use local error according to number of bone children
		for i in simplify_RDP(fcurve_verts, errors[group.name]):
			if i not in vert_indices:
				vert_indices.append(i)
				
	#now clean every curve, ie. remove all keys we don't need
	for fcurve in fcurves:
		#go over all keys, remove those we don't want and make the others linear
		for i in range(len(fcurve.keyframe_points)-1,0,-1):
			if i in vert_indices:
				fcurve.keyframe_points[i].interpolation = "LINEAR"
			else:
				fcurve.keyframe_points.remove(fcurve.keyframe_points[i])
	
def pose_frame_info(obj):
	matrices = {}
	for name, pbone in obj.pose.bones.items():
		matrices[name] = obj.convert_space(pbone, pbone.matrix, 'POSE', 'LOCAL')
	return matrices

def find_in_group(group, t, i):
	for fcurve in group.channels:
		if fcurve.data_path == t and fcurve.array_index == i:
			return fcurve
			
def loop_fcurve_tangents():
	print("starting loop_fcurve_tangents")
	before = {}
	after = {}
	for action in bpy.data.actions:
		#eventually also check for transitions, make sure they match up and interpolate tangents between anims
		#print(action.name)
		if "_" in action.name:
			if "_2" not in action.name:
				main = action.name.split("_")[0]+"_"
				for act in bpy.data.actions:
					if any(x in act.name and main in act.name for x in ("Idle", "Ahead")):
						#print("before+after",act.name)
						before[action] = act
						after[action] = act
						break
			if "_2" in action.name:
				b, a = action.name.split("_2")
				b += "_"
				a += "_"
				for act in bpy.data.actions:
					if any(x in act.name and b in act.name for x in ("Idle", "Ahead")):
						#print("before",act.name)
						before[action] = act
						break
				for act in bpy.data.actions:
					if any(x in act.name and a in act.name for x in ("Idle", "Ahead")):
						#print("after",act.name)
						after[action] = act
						break
		# might not want to do this
		#else:
		#	before[action] = action
		#	after[action] = action
	for action in bpy.data.actions:
		#eventually also check for transitions, make sure they match up and interpolate tangents between anims

		print("Looping",action.name)
		#frame_range = range(int(action.frame_range[0]), int(action.frame_range[1]))
		w = 0
		e=0
		#if they were not added in the first place, skip now
		try:
			bef = before[action]
			aft = after[action]
		except:
			continue
		for group in action.groups:
			#set or create the other groups
			try:
				bgroup = bef.groups[group.name]
				w+=1
			except:
				bgroup = group
				e+=1
			try: agroup = aft.groups[group.name]
			except: agroup = group
			
			#go through all fcurves of that bone
			for fcurve in group.channels:
				#print(fcurve.data_path)
				
				#equivalent curves from before and after anims
				try: bcurve = find_in_group(bgroup, fcurve.data_path, fcurve.array_index)
				except: bcurve = fcurve
				try: acurve = find_in_group(agroup, fcurve.data_path, fcurve.array_index)
				except: acurve = fcurve
				
				#the keys
				try:
					bkeys = bcurve.keyframe_points
					fkeys = fcurve.keyframe_points
					akeys = acurve.keyframe_points
				except:
					print("An fcurve is missing")
					break
					
				#current action
				#get both tangents
				if len(fkeys) > 1:
					#handle = (fkeys[1].co - fkeys[0].co - fkeys[-2].co + fkeys[-1].co)/5
					lfhandle = fkeys[1].co - fkeys[0].co
					rfhandle = fkeys[-1].co - fkeys[-2].co
					
					#the action before this action
					#get the last tangent
					if len(bkeys) > 1:
						bhandle = bkeys[-1].co - bkeys[-2].co
					#then cycle
					else:
						bhandle = rfhandle
					#the action after this action
					#get the first tangent
					if len(akeys) > 1:
						ahandle = akeys[1].co - akeys[0].co
					#then cycle
					else:
						ahandle = lfhandle
					
					#set the handle
					fkeys[0].handle_right_type = "FREE"
					fkeys[-1].handle_left_type = "FREE"
					#interpolate with the main anim or with its own ends
					if "_2" in action.name:
						fkeys[0].handle_right = fkeys[0].co + (lfhandle + bhandle)/5
						fkeys[-1].handle_left = fkeys[-1].co - (rfhandle + ahandle)/5
					#only use the foreign handles for loops
					else:
						fkeys[0].handle_right = fkeys[0].co + (ahandle + bhandle)/5
						fkeys[-1].handle_left = fkeys[-1].co - (ahandle + bhandle)/5

def is_constrained_armature(ob):
	#finds an armature either via name (first) or if it has constraints (slower fallback)
	if type(ob.data) == bpy.types.Armature:
		if ob.name.startswith("*"):
				return True
		for name, pbone in ob.pose.bones.items():
			if pbone.constraints:
				ob.name = "*"+ob.name
				return True
	return False
						
def bake_and_clean(error = 0.25, exp_power = 2):
	print("\nStarted baking and cleaning process with max error",error)
	starttime = time.clock()
	frame_back = bpy.context.scene.frame_current
	
	#first fix the tangents on all actions
	loop_fcurve_tangents()
	
	reported_errors = []
	
	#initialize the error lookup used for adaptive error
	global errors
	errors = {}
	
	if bpy.data.actions:
		src_armatures = [ob for ob in bpy.data.objects if is_constrained_armature(ob)]
		if src_armatures:
			armature = src_armatures[0]
			if armature.pose is None: return
			print("Found armature "+armature.name+" with constraints!")
			
			#exp_power = 2 seems reasonable
			for bone in armature.data.bones.values():
				#a bone may have zero children, so add 1!
				errors[bone.name] = error/(len(bone.children_recursive)+1)**exp_power
			print("Errors for each bone:")
			print(errors)
			if armature.name[1:] in bpy.data.objects:
				armature_copy = bpy.data.objects[armature.name[1:]]
				armature_copy.data = armature.data.copy()
				armature_copy.data.name = armature.data.name[1:]
				print("Armature "+armature_copy.name+" without constraints exists!")
			else:
				armature_copy = armature.copy()
				armature_copy.data = armature.data.copy()
				armature_copy.name = armature.name[1:]
				armature_copy.data.name = armature.data.name[1:]
				bpy.context.scene.objects.link(armature_copy)
				print("Created armature "+armature_copy.name+" without constraints!")
			#drivers
			for name in armature_copy.pose.bones.keys():
				armature_copy.driver_remove('pose.bones["'+name+'"].rotation_quaternion')
				
			src_actions = [action for action in bpy.data.actions if action.name.startswith("*")]
			#if it did not find any - but it is already clear from the armature that we have constraints - the user forgot to name them, so we name them and all is fine
			if not src_actions:
				reported_errors.append("Could not find any actions marked for baking - marking all existing actions with *!")
				for action in bpy.data.actions:
					action.name = "*" + action.name
				src_actions = bpy.data.actions
				
			for action in src_actions:
				print("Baking",action.name)
				pose_info = []
				#thylacine demands +1
				frame_range = range(int(action.frame_range[0]), int(action.frame_range[1])+1)

				armature.animation_data.action = action
				# Collect transformations
				for f in frame_range:
					bpy.context.scene.frame_set(f)
					# for drivers, we need two updates!
					bpy.context.scene.update()
					bpy.context.scene.update()
					pose_info.append(pose_frame_info(armature))

				# in case animation data hasn't been created
				atd = armature_copy.animation_data_create()
				# Create or clear action
				if action.name[1:] in bpy.data.actions:
					copy_action = bpy.data.actions[action.name[1:]]
					for fcurve in copy_action.fcurves:
						copy_action.fcurves.remove(fcurve)
				else:
					copy_action = bpy.data.actions.new(action.name[1:])
				copy_action.use_fake_user = True
				atd.action = copy_action

				# Apply transformations to action
				for name, pbone in armature_copy.pose.bones.items():
					while pbone.constraints:
						pbone.constraints.remove(pbone.constraints[0])
					# create compatible eulers
					euler_prev = None

					for (f, matrix) in zip(frame_range, pose_info):
						pbone.matrix_basis = matrix[name].copy()

						pbone.keyframe_insert("location", -1, f, name)

						rotation_mode = pbone.rotation_mode
						if rotation_mode == 'QUATERNION':
							pbone.keyframe_insert("rotation_quaternion", -1, f, name)
						elif rotation_mode == 'AXIS_ANGLE':
							pbone.keyframe_insert("rotation_axis_angle", -1, f, name)
						else:  # euler, XYZ, ZXY etc
							if euler_prev is not None:
								euler = pbone.rotation_euler.copy()
								euler.make_compatible(euler_prev)
								pbone.rotation_euler = euler
								euler_prev = euler
								del euler
							else:
								euler_prev = pbone.rotation_euler.copy()
							pbone.keyframe_insert("rotation_euler", -1, f, name)

						pbone.keyframe_insert("scale", -1, f, name)
				print("Cleaning",copy_action.name)
				for group in copy_action.groups:
					clean_group(group, "quaternion")
					clean_group(group, "location")
					clean_group(group, "scale")
				if not "2" in copy_action.name:
					for fcurve in copy_action.fcurves:
						mod = fcurve.modifiers.new('CYCLES')
						mod.mode_after = 'REPEAT_OFFSET'
						mod.mode_before = 'REPEAT_OFFSET'
			success = '\nFinished action baking and fcurve cleaning in %.2f seconds\n' %(time.clock()-starttime)
			bpy.context.scene.frame_set(frame_back)
			bpy.context.scene.update()
			worked = True
			print(success)
		else:
			reported_errors.append("Could not find an armature with constraints for baking!")
	else:
		reported_errors.append("There are no actions - are you really trying to export animations?")

	return reported_errors