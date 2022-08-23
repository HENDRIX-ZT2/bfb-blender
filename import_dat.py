import os
import time
import bpy
from struct import unpack_from,iter_unpack,calcsize
from .common_bfb import *

def generate_mesh(x_verts, y_verts, scale, heights):
	verts=[]
	i=0
	for y in range(y_verts):
		for x in range(x_verts):
			verts.append((x*scale, y*scale, heights[i]-7),)
			i+=1
	quads=[]
	i=0
	for x in range(x_verts-1):
		for y in range(y_verts-1):
			quads.append((i+1,i,i+y_verts,i+y_verts+1))
			i+=1
		i+=1
	return verts, quads
	
def load(operator, context, filepath = ""):
	starttime = time.time()
	errors = []
	
	sculpt_settings = bpy.context.scene.tool_settings.sculpt
	sculpt_settings.lock_x = True
	sculpt_settings.lock_y = True
	
	#when no object exists, or when we are in edit mode when script is run
	try: bpy.ops.object.mode_set(mode='OBJECT')
	except: pass
	
	print("\nImporting",os.path.basename(filepath))
	f = open(filepath, 'rb')
	datastream = f.read()
	f.close()
	
	#version = vanilla 10, ES+AA 11, MM 13, EA +custom 14
	# influence on vertex len & water padding
	#len = number of grid squares
	# res always 3
	#u2,3 ? resolution per square/ edge?
	# x_verts related to x y len, maybe res?
	#x_verts = (x_len*4/3) + 1
	#(x_verts-1)*3/4 = x_len
	#u4, u5 always 9 - maybe resolution of stencil map?
	# changing x_res crashes the game
	# changing u2 distorts the map
	# changing u4 does nothing
	version, x_len, y_len, x_res, y_res, u2, u3, x_verts, y_verts, u4, u5, numbiomes  = unpack_from('=i4f7i',datastream, 0)
	print("Version:",version)
	print("X Size:",x_len)
	print("Y Size:",y_len)
	print("X Verts:",x_verts)
	print("Y Verts:",y_verts)
	p=48
	lutbiomes=[]
	biomes=[]
	for i in range(numbiomes):
		l=unpack_from('=i',datastream, p)[0]
		biome = datastream[p+4:p+3+l].decode("utf8")
		biomes.append(biome)
		lutbiomes.append("08_b_"+biome)
		p+=4+l

	info=["00_f_height","04_f_unk","08_b_biome","09_b_unk","10_b_unk","11_b_unk","12_b_dirt","13_b_seafloor","14_b_unk","15_b_unk","16_b_unk","17_b_protected","18_f_shore","22_f_unk","26_b_cliff","27_b_conservation","28_b_tankwall"]
	
	#vanilla 27, ES AA 28, MM EA custom 29 - additional byte for tankwall edges & conservation areas
	vlen = 29
	missing = []
	for v in (13, 11):
		if version < v:
			vlen -= 1
			missing.append( info.pop() )
	scale = y_len / (y_verts-1)
	formatstr = "="+"".join([pair[3] for pair in info])
	vertlist = list(iter_unpack(formatstr, datastream[p : p+calcsize(formatstr)*x_verts*y_verts]))
	verts, quads = generate_mesh(x_verts, y_verts, scale, [v[0] for v in vertlist])
	map_ob, me = mesh_from_data("map", verts, quads, False)
	for face in me.polygons:
		face.use_smooth = True
	
	for biome in lutbiomes: map_ob.vertex_groups.new(biome)
	for t, key in enumerate(info):
		if key == "00_f_height": pass
		elif key == "08_b_biome":
			for i in range(len(vertlist)):
				biome = lutbiomes[vertlist[i][t]]
				map_ob.vertex_groups[biome].add([i], 1, 'REPLACE')
		else:
			map_ob.vertex_groups.new(key)
			for i in range(len(vertlist)):
				#prevent clipping
				if "_f_" in key:
					map_ob.vertex_groups[key].add([i], vertlist[i][t]/100, 'REPLACE')
				else:
					map_ob.vertex_groups[key].add([i], vertlist[i][t], 'REPLACE')
	#for compatibility with export
	for key in reversed(missing):
		map_ob.vertex_groups.new(key)
	
	p += calcsize(formatstr)*x_verts*y_verts
	num_water_bodies = unpack_from('=I',datastream, p)[0]
	print("Water Bodies:",num_water_bodies)
	p+= 4
	v, f = generate_mesh(x_verts, y_verts, scale, [0 for v in vertlist])
	water_ob, water_me = mesh_from_data("water", v, f, False)
	water_padding = 5 if version > 11 else 0
	for face in water_me.polygons:
		face.use_smooth = True
	for body in range(num_water_bodies):
		height, biome_i, num_entries = unpack_from('=fII',datastream, p)
		water_biome = biomes[biome_i]
		entries = unpack_from('='+str(num_entries)+'I',datastream, p+12)
		p+=num_entries*4+12+water_padding
		for i in entries:
			water_me.vertices[i].co[2] = height-7
		group_name = str(body)+"_"+water_biome
		water_ob.vertex_groups.new(group_name)
		water_ob.vertex_groups[group_name].add(entries, 1, 'REPLACE')

	success = 'Finished DAT Import in %.2f seconds\n' %(time.time()-starttime)
	print(success)
	return errors