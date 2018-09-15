import bpy
import mathutils

def make_interpolater(left_min, left_max, right_min, right_max): 
    # Figure out how 'wide' each range is  
    leftSpan = left_max - left_min  
    rightSpan = right_max - right_min  

    # Compute the scale factor between left and right values 
    scaleFactor = float(rightSpan) / float(leftSpan) 

    # create interpolation function using pre-calculated scaleFactor
    def interp_fn(value):
        return right_min + (value-left_min)*scaleFactor

    return interp_fn

def add_fx_wind(fixed_items, wmin, wmax):
	for ob in bpy.context.selected_objects:
		print(ob.name)
		me = ob.data
		if type(me) == bpy.types.Mesh:
			if "fx_wind" not in ob.vertex_groups:
				ob.vertex_groups.new("fx_wind")
			
			#set the center
			center = mathutils.Vector()
			if fixed_items == "1":
				for v in me.vertices:
					center+=v.co
				center/=len(me.vertices)
				
			if fixed_items == "0": weights = [v.co.z for v in me.vertices]
			if fixed_items == "1": weights = [(v.co-center).length for v in me.vertices]
			if fixed_items == "2": weights = [(v.co-center).length for v in me.vertices]
			if fixed_items == "3": weights = [(v.co.xy).length for v in me.vertices]
			
			scaler = make_interpolater(min(weights), max(weights), wmin, wmax)
			weights = [scaler(x) for x in weights]
			for i in range(0,len(weights)):
				ob.vertex_groups["fx_wind"].add([i], weights[i], 'REPLACE')
