import bpy
import mathutils
from .common_bfb import *
from .bake_clean_actions import *

def uniquify(seq):
   seen = {}
   result = []
   for item in seq:
       if item in seen: continue
       seen[item] = 1
       result.append(item)
   return result
   
def toggle_link_ik_controllers(operator, context, layers=(), root_name="Bip01", ik_names = "*IKH.L,*IKH.R,*IKF.L,*IKF.R"):
	print("starting toggle_link_ik_controllers")
	n_root = root_name
	n_limbs = ik_names.split(",")
	#when no object exists, or when we are in edit mode when script is run
	for ob in bpy.context.scene.objects:
		if type(ob.data) ==  bpy.types.Armature:
			arm = ob
			bpy.context.scene.objects.active = ob
			bpy.ops.object.mode_set(mode='EDIT')
			root = ob.data.edit_bones[n_root]
			root_m_inv = root.matrix.inverted()
			e_limbs = [ob.data.edit_bones[x] for x in n_limbs if x in ob.data.edit_bones]
			for limb in e_limbs:
				if limb.parent:
					limb.parent = None
					free_to_linked = False
				else:
					limb.parent = root
					free_to_linked = True
			bpy.ops.object.mode_set(mode='POSE')
	
	p_root = arm.pose.bones[n_root]
	p_limbs = [arm.pose.bones[x] for x in n_limbs if x in arm.pose.bones]
	
	for action in bpy.data.actions:
		arm.animation_data.action = action
		for group in action.groups:
			for p_bone in p_limbs:
				if group.name == p_bone.name:
					frames = uniquify([v.co[0] for fcurve in group.channels for v in fcurve.keyframe_points])
					frames_matrix= {}
					for f in frames:
						bpy.context.scene.frame_set(f)
						bpy.context.scene.update()
						
						#inverted to change from free to linked
						#update 6/18: use pose matrix and the inverse rest to get the root movement in armature space
						if free_to_linked:
							frames_matrix[f] = (p_root.matrix*root_m_inv).inverted() * p_bone.matrix
						else:
							frames_matrix[f] = (p_root.matrix*root_m_inv) * p_bone.matrix
						
					for f in frames_matrix:
						bpy.context.scene.frame_set(f)
						bpy.context.scene.update()
						p_bone.matrix = frames_matrix[f]
						p_bone.keyframe_insert("rotation_quaternion", -1, f, group.name)
						p_bone.keyframe_insert("location", -1, f, group.name)
					for fcu in group.channels:
						m = fcu.modifiers
						for mod in m:
							if mod.type == "CYCLES":
								mod.mode_after = "REPEAT_OFFSET"
								mod.mode_before = "REPEAT_OFFSET"
	loop_fcurve_tangents()
	return {'FINISHED'}
				
def reorient_bone(operator, context, fixed_items, layers=(), location=mathutils.Vector((0,0,1)), rotation=mathutils.Euler((0,0,1)) ):

	#say we want to rotate 180° around Y in bone's local space, as if it was posed with this euler
	rot_mat = rotation.to_matrix().to_4x4()
	#when no object exists, or when we are in edit mode when script is run
	armature = get_armature()
	if armature:
		bpy.context.scene.objects.active = armature
		bpy.ops.object.mode_set(mode='EDIT')
		bone_names = [bone.name for bone in armature.data.edit_bones if bone.select]
		print(bone_names)
		for bone_name in bone_names:
			b1 = armature.data.edit_bones[bone_name]
			locally_rotated = b1.matrix * rot_mat
			tail, roll = bpy.types.Bone.AxisRollFromMatrix(locally_rotated.to_3x3())
			b1.head = locally_rotated.to_translation()
			b1.tail = tail + b1.head
			b1.roll = roll
			fix_bone_length(b1)
		bpy.ops.object.mode_set(mode='POSE')

		for action in bpy.data.actions:
			for group in action.groups:
				if group.name in bone_names:
					#rotate the translation so the movement of the bone remains identical
					for data_type in ("location", "quaternion"):
						curves = [fcurve for fcurve in group.channels if fcurve.data_path.endswith(data_type)]
						if curves:
							num_keys = len(curves[0].keyframe_points)
							for i in range(0, num_keys):
								frame = curves[0].keyframe_points[i].co[0]
								key_in = [fcurve.keyframe_points[i].co[1] for fcurve in curves]
								if data_type == "location":
									mat =  mathutils.Matrix.Translation( key_in )
									mat = rot_mat.inverted() * mat *rot_mat
									key = mat.to_translation()
								else:
									mat = mathutils.Quaternion(key_in).to_matrix().to_4x4()
									mat = rot_mat.inverted() * mat *rot_mat
									key = mat.to_quaternion()
								for a in range(0, len(curves)):
									curves[a].keyframe_points[i].co[1] = key[a]
			for fcurve in action.fcurves:
				fcurve.update()
		#call the tangent function
		loop_fcurve_tangents()
		bpy.context.scene.update()
	return {'FINISHED'}
	
	
def add_correction_bone(operator, context, layers=(), location=mathutils.Vector((0,0,1)), rotation=mathutils.Euler((0,0,1)) ):
	#location and rotation of the new bone in bonespace	
	c_bspace = rotation.to_matrix().to_4x4()
	#c_bspace.translation = location
	pbone = bpy.context.active_bone
	
	parent = None
	for bone in bpy.context.selected_bones:
		parent = bone.parent
		
	if parent:
		p_aspace = parent.matrix
		cc_bspace = p_aspace * c_bspace
		cbone = bpy.context.active_object.data.edit_bones.new("Test")
		cbone.head = location+mathutils.Vector((0,0,0))
		cbone.tail = location+mathutils.Vector((0,1,0))
		cbone.parent = parent
		cbone.transform(cc_bspace)
		cbone.roll = cbone.parent.roll
		
		#rotation about the cbone head
		mat = (mathutils.Matrix.Translation(cbone.head) * c_bspace * mathutils.Matrix.Translation(-cbone.head))
		dir = cbone.head-cbone.parent.head
		
	for bone in bpy.context.selected_bones:
		bone.parent = cbone
	
	#transform all children, first translation, then rotation
	for a in cbone.children_recursive:
		a.translate(dir)
		a.transform(mat)
		
	#fix the bone length
	for bone in bpy.context.active_object.data.edit_bones:
		#don't change Bip01
		if bone.parent:
			childheads = mathutils.Vector()
			for child in bone.children:
				childheads += child.head
			if bone.children:
				bone.length = (bone.head - childheads/len(bone.children)).length
				if bone.length < 0.01:
					bone.length = 0.25
			# end of a chain
			else:
				bone.length = bone.parent.length
				
	return {'FINISHED'}