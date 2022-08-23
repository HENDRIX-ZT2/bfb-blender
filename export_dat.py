import os
import time
import math
import bpy
from struct import pack

def save(operator, context, filepath = ''):
	
	print('Exporting',filepath,'...')
	errors = []
	#just in case - probably not needed
	#make sure there is an active object - is it needed?
	try: bpy.ops.object.mode_set(mode="OBJECT")
	except:
		bpy.context.scene.objects.active = bpy.context.scene.objects[0]
		bpy.ops.object.mode_set(mode="OBJECT")
	
	starttime = time.time()
	
	map_ob = bpy.data.objects["map"]
	me = map_ob.data
	biomes = []
	for vgroup in map_ob.vertex_groups:
		if "08_b_" in vgroup.name:
			biomes.append(vgroup.name)
	verts=[]
	for vert in me.vertices:
		s = pack('=f', vert.co.z+7)
		bw = 0
		for vertex_group in vert.groups:
			name = map_ob.vertex_groups[vertex_group.group].name
			if not "08_b" in name:
				v = vertex_group.weight
			else:
				if not vertex_group.weight > bw: continue
				bw = vertex_group.weight
				biome = name
				v = biomes.index(biome)
			if "_f_" in name:
				s+=pack('=f', v*100)
			elif "_b_" in name:
				s+=pack('=b', int(v))
		#whyyyy??
		verts.append(s[0:29])
	#add a ratio control if possible
	xverts = yverts = math.sqrt(len(me.vertices))
	x_len = y_len = (xverts-1)*3/4
	biomesstr = b""
	biomes_clean = []
	for biome in biomes:
		name = biome.replace("08_b_","")
		biomes_clean.append(name)
		l = len(name)
		biomesstr+=pack("=i"+str(l)+"sb", l+1, name.encode('utf-8'),0)
	#print(biomesstr)
	water_ob = bpy.data.objects["water"]
	num_water_bodies = len(water_ob.vertex_groups)
	water_me = water_ob.data
	
	#init the storage
	bodies = []
	biomes_weights_map = {}
	for vgroup in water_ob.vertex_groups:
		biomes_weights_map[vgroup.name] = []
	#gather all vert indices for each water body
	for vert in water_me.vertices:
		for vertex_group in vert.groups:
			name = water_ob.vertex_groups[vertex_group.group].name
			if vertex_group.weight > .9:
				biomes_weights_map[name].append( vert.index )
				#maybe add a "continue" here; if the vert has to be exclusive for one water body in game
	#get the height and write all the data
	for vgroup in water_ob.vertex_groups:
		ind_str, biome_name = vgroup.name.split("_")
		vert_indices = biomes_weights_map[vgroup.name]
		num_vert_indices = len(vert_indices)
		#todo: do average or random sampling?
		height = water_me.vertices[vert_indices[0]].co[2]+7
		bodies.append( pack('=fII'+str(num_vert_indices)+"I", height, biomes_clean.index(biome_name), num_vert_indices, *vert_indices) )
	
	dirname = os.path.dirname(filepath)
	if not os.path.exists(dirname):
		os.makedirs(dirname)
	f = open(filepath, 'wb')
	f.write(pack('=l4f7i', 14, x_len, y_len, 3, 3, 5, 5, int(xverts), int(yverts), 9, 9, len(biomes)) + biomesstr + b"".join(verts) + pack('=I', num_water_bodies) + pack("5B",0,0,0,0,0).join(bodies))
	f.close()

	print('Finished DAT Export in %.2f seconds' %(time.time()-starttime))
	return errors