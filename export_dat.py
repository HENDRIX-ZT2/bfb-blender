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
	
	starttime = time.clock()
	if len(bpy.context.scene.objects)<1:
		return ("More than one object in scene!",)
	
	ob=bpy.data.objects[0]
	me=ob.data
	biomes = []
	for vgroup in ob.vertex_groups:
		if "08_b_" in vgroup.name:
			biomes.append(vgroup.name)
	verts=[]
	for vert in me.vertices:
		s = pack('=f', vert.co.z)
		bw = 0
		for vertex_group in vert.groups:
			name = ob.vertex_groups[vertex_group.group].name
			if not "08_b" in name:
				v = vertex_group.weight
			else:
				if not vertex_group.weight > bw: continue
				bw = vertex_group.weight
				biome = name
				v = biomes.index(biome)
			if "f" in name:
				s+=pack('=f', v*100)
			elif "b" in name:
				s+=pack('=b', int(v))
		#whyyyy??
		verts.append(s[0:29])
	#add a ratio control if possible
	xverts = yverts = math.sqrt(len(me.vertices))
	x_len = y_len = (xverts-1)*3/4
	biomesstr = b""
	for biome in biomes:
		name = biome.replace("08_b_","")
		l = len(name)
		biomesstr+=pack("=i"+str(l)+"sb", l+1, name.encode('utf-8'),0)
	#print(biomesstr)
	
	dirname = os.path.dirname(filepath)
	if not os.path.exists(dirname):
		os.makedirs(dirname)
	f = open(filepath, 'wb')
	f.write(pack('=l4f7i', 14, x_len, y_len, 3, 3, 5, 5, int(xverts), int(yverts), 9, 9, len(biomes)) + biomesstr + b"".join(verts))
	f.close()

	print('Finished DAT Export in %.2f seconds' %(time.clock()-starttime))
	return errors