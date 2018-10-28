import bpy, mathutils, math
from mathutils import Vector, Matrix
from math import pi
import os
import xml.etree.ElementTree as ET
 
def createColorRamp(tex, values):
	tex.use_color_ramp = True
	ramp = tex.color_ramp
	for n,value in enumerate(values):
		(pos, color) = value
		try:
			elt = ramp.elements[n]
			elt.position = pos
		except:
			 elt = ramp.elements.new(pos)
		elt.color = color
	return
	
def create_material(filepath,ob,matname):
	print("MATERIAL:",matname)
	#only create the material if we haven't already created it, then just grab it
	dirname = os.path.dirname(filepath)
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
		matpath = os.path.join(dirname, matname + ".bfmat")
		print(matpath)
		if os.path.exists(matpath):
			try:
				tree = ET.parse(matpath)
			except:
				print("Materials/"+matname+".BFMAT cannot be parsed, likely due to an XML syntax error!")
				return
		else:
			print("Could not find Materials/"+matname+".BFMAT!")
			return mat
		
		mat.specular_intensity = 0.0
		mat.ambient = 1
		mat.use_transparency = True
		
		material = tree.getroot()
		fx = material.attrib["fx"]
		print("FX SHADER:",fx)
		for param in material:
			name = param.attrib["name"]
			if "type" in param.attrib:
				if param.attrib["type"] == "vector4":
					text = param.text.split(", ")
				else:
					text = param.text
			#set stuff on the material
			if name == "MaterialAmbient":
				mat.diffuse_color=float(text[0]),float(text[1]),float(text[2])#
				#always put to 0
				mat.alpha=0
			if name == "MaterialPower":
				mat.diffuse_intensity=float(text)
			
			#new and experimental
			if param.tag == "animate":
				fps = bpy.context.scene.render.fps
				for i in range(0,2):
					if name == "TextureTransform"+str(i):
						for key in param.find("./offsetu"):
							mat.texture_slots[i].offset[0] = float(key.attrib["value"])
							mat.texture_slots[i].keyframe_insert("offset", index = 0, frame = int(float(key.attrib["time"])*fps))
						for key in param.find("./offsetv"):
							mat.texture_slots[i].offset[1] = float(key.attrib["value"])
							mat.texture_slots[i].keyframe_insert("offset", index = 1, frame = int(float(key.attrib["time"])*fps))
			#multi-textures
			for i in range(0,2):
				if name == "Texture"+str(i):
					#only import the image and texture if we haven't already imported it!
					#we may use the same texture in different materials!
					text= os.path.basename(text)
					try:
						if text not in bpy.data.textures:
							tex = bpy.data.textures.new(text, type = 'IMAGE')
							recursiveDepth = 5
							texpath = dirname
							for dirLevel in range(0,recursiveDepth):
								texturepath = os.path.join(texpath,text+".dds")
								print(texturepath)
								if os.path.exists(texturepath): break
								texturepath = os.path.join(texpath,"shared",text+".dds")
								print(texturepath)
								if os.path.exists(texturepath): break
								texpath = os.path.dirname(texpath)
							try:
								img = bpy.data.images.load(texturepath)
							except:
								print("Could not find image "+text+".dds, generating blank image!")
								img = bpy.data.images.new(text+".dds",1,1)
							tex.image = img
						else: tex = bpy.data.textures[text]
						#now create the slot in the material for the texture
						mtex = mat.texture_slots.add()
						mtex.texture = tex
						mtex.texture_coords = 'UV'
						mtex.use_map_color_diffuse = True 
						mtex.use_map_color_emission = True 
						mtex.emission_color_factor = 0.5
						mtex.use_map_density = True 
						mtex.mapping = 'FLAT'
						#mtex.use_stencil = True
						#RR reflection effect
						if (fx == "BaseReflectRR" and i == 1) or (fx == "BaseDecalReflectRR" and i == 2):
							mtex.blend_type = 'OVERLAY'
							mtex.texture_coords = 'REFLECTION'
						if (fx == "BaseDetail" and i == 1):
							mtex.blend_type = 'OVERLAY'
						#TO DO: cull mode -> african violets
						
						#see if there is an alternative UV index specified. If so, set it as the UV layer. If not, use i.
						mtex.uv_layer = str(i)
						for param in material:
							if param.attrib["name"] == "TexCoordIndex"+str(i):
								mtex.uv_layer = param.text
								break
						
						#for the icon renderer
						tex.use_mipmap = False
						tex.use_interpolation = False
						tex.filter_type = "BOX"
						tex.filter_size = 0.1
						# we only want to render default tex for icons
						if i > 0: mat.use_textures[i] = False
					except:
						log_error(name+" in Materials/"+matname+".BFMAT has no image reference! Add the image name in the .BFMAT to fix!")
	else: mat = bpy.data.materials[matname]
	
	#now finally set all the textures we have in the mesh
	me = ob.data
	me.materials.append(mat)
	return mat	
def getv(param): return [float(v) for v in param.text.split(",")]
def load(operator, context, filepath = ""):
	try:
		tree = ET.parse(filepath)
	except:
		print(filepath+" cannot be parsed, likely due to an XML syntax error!")
		return {'FINISHED'}
		
	fps = bpy.context.scene.render.fps
	
	#init here
	lcol = []
	
	#create psys
	bpy.ops.mesh.primitive_plane_add(location=mathutils.Vector((0,0,0)))
	emitter = bpy.context.object
	bpy.ops.mesh.uv_texture_add()
	bpy.context.scene.objects.active = emitter
	bpy.ops.object.particle_system_add()	
	psys = emitter.particle_systems[-1]
	psys.name = os.path.basename(filepath)[:-5]
	pset = psys.settings
	pset.name = psys.name+'_Settings'
		
	# Physics
	pset.physics_type = 'NEWTON'
	pset.mass = 1.0
	pset.particle_size = 10.0
	pset.use_multiply_size_mass = True

	# # Effector weights
	# ew = pset.effector_weights
	# ew.gravity = 0.0
	# ew.wind = 1.0


	# # Children
	# pset.child_type = 'SIMPLE'
	# pset.rendered_child_count = 50
	# pset.child_radius = 1.1
	# pset.child_roundness = 0.5
	
	#note that some may have more than one top-level simulator!
	simulator = tree.getroot()
	for block in simulator:
		if block.tag == "emitter":
			#unknown stuff
			pset.emit_from = 'FACE'
			pset.use_render_emitter = False
			pset.distribution = 'RAND'
			pset.object_align_factor = (0,0,1)
			for param in block:
				if param.tag == "param":
					if param.attrib["label"] == "initpos":
						emitter.location = getv(param)
					if param.attrib["label"] == "minspeed":
						pass
					if param.attrib["label"] == "maxspeed":
						pass
					if param.attrib["label"] == "ratetospawn":
						pass
					if param.attrib["label"] == "probability":
						pass
					if param.attrib["label"] == "areaout":
						pass
					if param.attrib["label"] == "areaup":
						pass
					if param.attrib["label"] == "transform":
						matrix = mathutils.Matrix((getv(param)[0:4],getv(param)[4:8],getv(param)[8:12],getv(param)[12:16]))
						emitter.rotation_quaternion = matrix.to_quaternion()
					if param.attrib["label"] == "min radius":
						pass
					if param.attrib["label"] == "max radius":
						emitter.scale = (getv(param)[0], getv(param)[0], getv(param)[0])
					if param.attrib["label"] == "velocity base":
						pass
				if param.tag == "birthrate":
					#sadly we must use the maximum birthrate and can't animate it
					count = 0
					end = 0
					for key in param:
						count = max(count, float(key.attrib["value"]))
						end = max(end, float(key.attrib["time"]))
					pset.count = int(count)
					pset.frame_start = 1
					pset.frame_end = end * fps
		
		if block.tag == "modifier":
			if block.attrib["name"] == "Age":
				for param in block:
					if param.attrib["label"] == "minlife":
						lmin = getv(param)[0] * fps
					if param.attrib["label"] == "maxlife":
						lmax = getv(param)[0] * fps
				pset.lifetime = (lmin + lmax) / 2
				pset.lifetime_random = (lmax - pset.lifetime) / pset.lifetime
			
			if block.attrib["name"] == "Color":
				for param in block:
					if param.attrib["label"] == "Color":
						values = getv(param)
						colors = [getv(param)[i*4:i*4+4] for i in range(0,len(getv(param))//4)]
					if param.attrib["label"] == "Age":
						ages = [0.0,] + getv(param) + [1.0,]
				lcol = zip(ages, colors)
					
			if block.attrib["name"] == "Fade":
				for param in block:
					if param.attrib["label"] == "initcolor":
						initcolor = getv(param)
					if param.attrib["label"] == "fade":
						fade = getv(param)
					if param.attrib["label"] == "age":
						ages = getv(param)
				lfade = [(ages[0], initcolor),(ages[1], fade)]
				
			if block.attrib["name"] == "Velocity":
				# Velocity
				pset.normal_factor = 0.55
				pset.factor_random = 0.5
				pass
			if block.attrib["name"] == "Gravity":
				for param in block:
					if param.attrib["label"] == "accel":
						bpy.context.scene.gravity = (0, 0, -getv(param)[0])
			if block.attrib["name"] == "Flutter Velocity":
				for param in block:
					if param.attrib["label"] == "accel":
						pset.brownian_factor = getv(param)[0]/100
				
			if block.attrib["name"] == "Size":
				for param in block:
					if param.attrib["label"] == "value":
						values = getv(param)
					if param.attrib["label"] == "age":
						ages = [0.0,] + getv(param) + [pset.lifetime,]
				for i in range(0, len(ages)):
					pset.particle_size = values[i]
					pset.keyframe_insert("particle_size", frame = ages[i])
					
					#material is not yet created at this stage?!
					#material.halo.size = values[i]
					#material.keyframe_insert("halo.size", frame = ages[i])
					#print(ages[i],values[i])
		
		if block.tag == "renderer":
			# Display and render
			pset.draw_percentage = 100
			pset.draw_method = 'RENDER'
			pset.material = 1
			pset.render_type = 'BILLBOARD'
			pset.render_step = 3
			for param in block:
				if param.attrib["label"] == "width":
					pass
				if param.attrib["label"] == "height":
					pass
				if param.attrib["label"] == "numtilesu":
					pass
				if param.attrib["label"] == "numtilesv":
					pass
				if param.attrib["label"] == "material":
					material = create_material(filepath,emitter,param.text)
	#set the color texture ramp
	tex = bpy.data.textures.new('Color', type = 'BLEND')
	tex.progression = 'LINEAR'
	if lcol:
		createColorRamp(tex, lcol)
	mtex = material.texture_slots.add()
	mtex.texture = tex
	mtex.texture_coords = "STRAND"
	#set the fade texture ramp
	tex = bpy.data.textures.new('Fade', type = 'BLEND')
	tex.progression = 'LINEAR'
	createColorRamp(tex, lfade)
	mtex = material.texture_slots.add()
	mtex.texture = tex
	mtex.texture_coords = "STRAND"
	return {'FINISHED'}