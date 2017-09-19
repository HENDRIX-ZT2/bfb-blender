import os
import time
import bpy
from struct import unpack_from,iter_unpack,calcsize

def mesh_from_data(name, verts, faces):
	me = bpy.data.meshes.new(name)
	me.from_pydata(verts, [], faces)
	me.update()
	ob = bpy.data.objects.new(name, me)
	bpy.context.scene.objects.link(ob)
	return ob, me

def load(operator, context, filepath = ""):
	starttime = time.clock()
	errors = []

	
	#when no object exists, or when we are in edit mode when script is run
	try: bpy.ops.object.mode_set(mode='OBJECT')
	except: pass
	
	print("\nImporting",os.path.basename(filepath))
	f = open(filepath, 'rb')
	datastream = f.read()
	f.close()
	
	#u1 = vanilla 10, mm 13, custom 14 - maybe version?! -> somehow related to vertex length? correlation or just assigned?
	#len = number of grid squares
	# res always 3
	#u2,3 ? resolution per square/ edge?
	# x_verts related to x y len, maybe res?
	#x_verts = (x_len*4/3) + 1
	#(x_verts-1)*3/4 = x_len
	#u4, u5 always 9 - maybe resolution of stencil map?
	u1, x_len, y_len, x_res, y_res, u2, u3, x_verts, y_verts, u4, u5, numbiomes  = unpack_from('=i4f7i',datastream, 0)
	p=48
	lutbiomes=[]
	for i in range(0,numbiomes):
		l=unpack_from('=i',datastream, p)[0]
		lutbiomes.append("08_b_"+datastream[p+4:p+3+l].decode("utf8"))
		p+=4+l
	#print(lutbiomes)

	#0,1,2,3 = height
	#4, 5, 6, 7 = likely float
	#int4 looks clipped
	#float4 looks alright but very faint
	#8 = unkn
	#9,10,11 = 0
	#14,15,16=0
	#18,19 = 0
	#20,21, fail
	#22,23 = 0
	#24,25,26 = fail
	#28,29 fail
	info=["00_f_height","04_f","08_b_biome","09_b","10_b","11_b","12_b_dirt","13_b_shore","14_b","15_b","16_b","17_b_protected","18_b","19_b","20_b_intersection","21_b","22_b","23_b","24_b","25_b","26_b_cliff","27_b_conservation","28_b_tankwall"]

	info=["00_f_height","04_f","08_b_biome","09_b","10_b","11_b","12_b_dirt","13_b_shore","14_b","15_b","16_b","17_b_protected","18_f","22_f","26_b_cliff","27_b_conservation","28_b_tankwall"]
	
	#vanilla 28, mm 29, custom 29 - additional byte for tankwall edges
	#was 14 before, prolly error?!
	if u1 < 13:
		vlen = 28
		#delete that tankwall byte
		info.pop()
	else:
		vlen = 29
	formatstr = "="
	for pair in info:
		formatstr += pair[3]
	vertlist = list(iter_unpack(formatstr, datastream[p : p+calcsize(formatstr)*x_verts*y_verts]))
	
	#list1
	#80904
	#list2 -padding?
	#5839
	#root 284
	
	#print(x_len,y_len,x_res,y_res,x_verts,y_verts)
	#print(vertlist[0:5])
	verts=[]
	i=0
	for x in range(0,x_verts):
		for y in range(0,y_verts):
			verts.append((-x,y,vertlist[i][0]),)
			i+=1
	quads=[]
	i=0
	for x in range(0,x_verts-1):
		for y in range(0,y_verts-1):
			quads.append((i+1,i,i+y_verts,i+y_verts+1))
			i+=1
		i+=1
	ob, me = mesh_from_data("map", verts=verts, faces=quads)	
	for face in me.polygons:
		face.use_smooth = True
	
	for biome in lutbiomes: ob.vertex_groups.new(biome)
	for t, key in enumerate(info):
		if key == "00_f_height": pass
		elif key == "08_b_biome":
			for i in range(0,len(vertlist)):
				biome = lutbiomes[vertlist[i][t]]
				ob.vertex_groups[biome].add([i], 1, 'REPLACE')
		else:
			ob.vertex_groups.new(key)
			for i in range(0,len(vertlist)):
				#prevent clipping
				if "f" in key:
					ob.vertex_groups[key].add([i], vertlist[i][t]/100, 'REPLACE')
				else:
					ob.vertex_groups[key].add([i], vertlist[i][t], 'REPLACE')
					
	#p += calcsize(formatstr)*x_verts*y_verts
	
	#p += 16
	#s = int((x_len-1)*(y_len-1))*4
	#s= 81000
	#print(p)
	#print(s)
	#vertlist = list(iter_unpack("=H", datastream[p:p+s]))
	#print(vertlist)
	# verts=[]
	# i=0
	# for x in range(0,int(140)):
		# for y in range(0,int(140)):
			# #verts.append((-x,y,vertlist[i]),)
			# verts.append((-x,y,1),)
			# i+=1
	# quads=[]
	# # i=0
	# # for x in range(0,int(139)):
		# # for y in range(0,int(139)):
			# # quads.append((i+1,i,i+y_verts,i+y_verts+1))
			# # i+=1
		# # i+=1
	# ob, me = mesh_from_data("water", verts=verts, faces=quads)	
	# for face in me.polygons:
		# face.use_smooth = True
	
	success = '\nFinished DAT Import in %.2f seconds\n' %(time.clock()-starttime)
	print(success)
	return errors