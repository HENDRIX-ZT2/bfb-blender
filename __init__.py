bl_info = {	"name": "Blue Fang BFB format (Zoo Tycoon 2)",
			"author": "HENDRIX",
			"blender": (2, 74, 0),
			"location": "File > Import-Export",
			"description": "Import-Export models, skeletons and animations, batch-process models to add LODs. Experimental map support.",
			"warning": "",
			"wiki_url": "http://z14.invisionfree.com/ZT2_Designing_Center/index.php?showtopic=4385&st=0#entry22010275",
			"support": 'COMMUNITY',
			"tracker_url": "http://z14.invisionfree.com/ZT2_Designing_Center/index.php?showtopic=4385&st=0#entry22010275",
			"category": "Import-Export"}
#need this?
if "bpy" in locals():
	import importlib
	if "import_bfb" in locals():
		importlib.reload(import_bfb)
	if "import_dat" in locals():
		importlib.reload(import_dat)
	if "export_bfb" in locals():
		importlib.reload(export_bfb)
	if "export_dat" in locals():
		importlib.reload(export_dat)
	if "batch_bfb" in locals():
		importlib.reload(batch_bfb)
	if "import_bf" in locals():
		importlib.reload(import_bf)
	if "export_bf" in locals():
		importlib.reload(export_bf)

import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, CollectionProperty
from bpy_extras.io_utils import (ImportHelper, ExportHelper)
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import bpy.utils.previews
preview_collection = bpy.utils.previews.new()

class AddCapsule(bpy.types.Operator, AddObjectHelper):
	"""Create a new BFB Capsule Collider"""
	bl_idname = "mesh.add_bfb_capsule_collider"
	bl_label = "BFB Capsule Collider"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		from . import common_bfb
		import mathutils
		start = mathutils.Vector((0,0,0))
		end = mathutils.Vector((1,0,0))
		r = 1
		ob = common_bfb.create_capsule("capsule", start, end, r)
		for pa in bpy.context.scene.objects:
			print(type(pa.data))
			if type(pa.data) == bpy.types.Armature:
				ob.parent = pa
				ob.parent_type = 'BONE'
				for name in ("Bip01 Spine1", "Bip01 Spine", "Bip01 Pelvis", "Bip01"):
					try:
						ob.parent_bone = name
						bone = pa.data.bones[name]
						ob.location.y = -bone.length
						break
					except: pass
				break
		return {'FINISHED'}

class AddSphere(bpy.types.Operator, AddObjectHelper):
	"""Create a new BFB Sphere Collider"""
	bl_idname = "mesh.add_bfb_sphere_collider"
	bl_label = "BFB Sphere Collider"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		from . import common_bfb
		import mathutils
		x = 0
		y = 0
		z = 1
		r = 1
		pa = None
		col = common_bfb.create_sphere("sphere", x, y, z, r)
		for ob in bpy.context.scene.objects:
			if ob.name.startswith("paint_"):
				pa = ob
				break
		if not pa:
			pa = common_bfb.create_empty(None,"paint_cover_grassland",mathutils.Matrix())
		col.parent = pa
		return {'FINISHED'}
		
class AddBox(bpy.types.Operator, AddObjectHelper):
	"""Create a new BFB Box Collider"""
	bl_idname = "mesh.add_bfb_box_collider"
	bl_label = "BFB Box Collider"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		from . import common_bfb
		import mathutils
		x = 1
		y = 1
		z = 1
		pa = None
		col = common_bfb.create_bounding_box("orientedbox", mathutils.Matrix(), x, y, z)
		for ob in bpy.context.scene.objects:
			if ob.name.startswith("footprint"):
				pa = ob
				break
		if not pa:
			pa = common_bfb.create_empty(None,"footprint",mathutils.Matrix())
		col.parent = pa
		return {'FINISHED'}
		
class ImportBF(bpy.types.Operator, ImportHelper):
	"""Import from BF file format (.bf)"""
	bl_idname = "import_scene.bluefang_bf"
	bl_label = 'Import BF'
	bl_options = {'UNDO'}
	filename_ext = ".bf"
	filter_glob = StringProperty(default="*.bf", options={'HIDDEN'})
	files = CollectionProperty(type=bpy.types.PropertyGroup)
	set_fps = BoolProperty(name="Adjust FPS", description="Set the scene to 30 frames per second to conform with the BFs.", default=True)
	def execute(self, context):
		from . import import_bf
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		return import_bf.load(self, context, **keywords)


class ImportPSYS(bpy.types.Operator, ImportHelper):
	"""Import from PSYS file format (.psys)"""
	bl_idname = "import_scene.bluefang_psys"
	bl_label = 'Import PSYS'
	bl_options = {'UNDO'}
	filename_ext = ".psys"
	filter_glob = StringProperty(default="*.psys", options={'HIDDEN'})
	def execute(self, context):
		from . import import_psys
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		return import_psys.load(self, context, **keywords)
		
class ImportBFB(bpy.types.Operator, ImportHelper):
	"""Import from BFB file format (.bfb)"""
	bl_idname = "import_scene.bluefang_bfb"
	bl_label = 'Import BFB'
	bl_options = {'UNDO'}
	filename_ext = ".bfb"
	filter_glob = StringProperty(default="*.bfb", options={'HIDDEN'})
	use_custom_normals = BoolProperty(name="Use BFB Normals", description="Preserves the original shading of a BFB.", default=False)
	mirror_mesh = BoolProperty(name="Mirror Rigged Meshes", description="Mirrors models with a skeleton. Careful, sometimes bones don't match!", default=False)
	def execute(self, context):
		from . import import_bfb
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		errors = import_bfb.load(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}

class ImportDAT(bpy.types.Operator, ImportHelper):
	"""Import from DAT map format (.dat)"""
	bl_idname = "import_scene.bluefang_dat"
	bl_label = 'Import DAT'
	bl_options = {'UNDO'}
	filename_ext = ".dat"
	filter_glob = StringProperty(default="*.dat", options={'HIDDEN'})
	def execute(self, context):
		from . import import_dat
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		errors = import_dat.load(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}
		
class ExportDAT(bpy.types.Operator, ExportHelper):
	"""Export to DAT map format (.dat)"""
	bl_idname = "export_scene.bluefang_dat"
	bl_label = 'Export DAT'
	filename_ext = ".dat"
	filter_glob = StringProperty(default="*.dat", options={'HIDDEN'})
	def execute(self, context):
		from . import export_dat
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "check_existing"))
		errors = export_dat.save(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}
		
class ExportBFB(bpy.types.Operator, ExportHelper):
	"""Export to BFB file format (.bfb)"""
	bl_idname = "export_scene.bluefang_bfb"
	bl_label = 'Export BFB'
	filename_ext = ".bfb"
	filter_glob = StringProperty(default="*.bfb", options={'HIDDEN'})
	try:
		from . import common_bfb
		cfg = common_bfb.load_config()
		author = cfg["author"]
	except:
		author="somebody"
	export_materials = BoolProperty(name="Export Materials", description="Should BFMAT materials be exported? Beware, they might not be identical to the existing material!", default=True)
	author_name = StringProperty(name="Author", description="A signature included in the BFB file.", default=author)
	fix_root_bones = BoolProperty(name="Fix Root Bones", description="Deletes surplus root bones automatically.", default=False)
	create_lods = BoolProperty(name="Create LODs", description="Adds Levels of Detail - overwrites existing LODs!", default=True)
	numlods = IntProperty(	name="Number of LODs",
							description="Number of Levels Of Detail, including the original",
							min=1, max=5,
							default=2,)
	rate = IntProperty(	name="Detail Decrease Rate",
							description="The higher, the faster the detail will decrease: ratio = 1 /(LODX + Rate)",
							min=1, max=5,
							default=2,)
	def execute(self, context):
		from . import export_bfb
		try: common_bfb.update_config("author", self.author_name)
		except: pass
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "check_existing"))
		errors = export_bfb.save(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}
		
class ExportBF(bpy.types.Operator, ExportHelper):
	"""Export to BF file format (.bf)"""
	bl_idname = "export_scene.bluefang_bf"
	bl_label = 'Export BF'
	filename_ext = ".bf"
	filter_glob = StringProperty(default="*.bf", options={'HIDDEN'})
	bake_actions = BoolProperty(name="Fix Tangents, Bake Actions and Clean Results", description="Smoothes tangents between actions, creates armature without constraints and baked actions for armatures and actions marked with *.", default=True)
	error = FloatProperty(name="Max Cleaning Error", description="Adaptive Error - the more children a bone has, the less error it gets. The larger the error value, the smaller the file size, but the more error you get.", precision=3, step=1, soft_min=0.0, min=0.0, default=0.05)
	exp_power = FloatProperty(name="Error Exponent", description="This influences how fast the error increases along the bone chain. Use larger values for a steeper falloff", precision=3, step=1, soft_min=0.0, min=0.0, default=1.0)
	
	#TODO: replace these settings with the more transparent curve UI
	#https://blender.stackexchange.com/questions/61618/add-a-custom-curve-mapping-property-for-an-add-on
	def execute(self, context):
		from . import export_bf
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "check_existing"))
		errors = export_bf.save(self, context, **keywords)
		for error in errors:
			self.report({"ERROR"}, error)
		return {'FINISHED'}
		
class BatchBFB(bpy.types.Operator, ImportHelper):
	"""Batch process BFB and NIF files. Converts all NIFs to BFBs, and adds LODs to all BFBs."""
	bl_idname = "import_scene.bluefang_bfb_batch"
	bl_label = 'Batch Process'
	bl_options = {'UNDO'}
	filename_ext = ".bfb"
	filter_glob = StringProperty(default="*.bfb;*.nif", options={'HIDDEN'})
	files = CollectionProperty(type=bpy.types.PropertyGroup)
	numlods = IntProperty(	name="Number of LODs",
							description="Number of Levels Of Detail, including the original",
							min=1, max=5,
							default=2,)
	rate = IntProperty(	name="Detail Decrease Rate",
							description="The higher, the faster the detail will decrease: ratio = 1 /(LODX + Rate)",
							min=1, max=5,
							default=2,)
							
	def execute(self, context):
		from . import batch_bfb
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
		return batch_bfb.process(self, context, **keywords)

class ToggleIKLink(bpy.types.Operator):
	"""Toggle the IK link between limbs etc. and the root. Useful for animations, if you want to switch between treadmill and standard motion for easier workflow."""
	bl_idname = "bone.toggle_ik_link"
	bl_label = "Toggle IK link from Bip01 root"
	bl_options = {'REGISTER', 'UNDO'}
	root_name = StringProperty(name="Root bone name", description="The name of the root bone.", default="Bip01")
	ik_names = StringProperty(name="Limb IK bone names", description="The names of the bones to (un)link.", default="*IKH.L,*IKH.R,*IKF.L,*IKF.R")
	def execute(self, context):
		from . import bone_tools
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "view_align"))
		return bone_tools.toggle_link_ik_controllers(self, context, **keywords)
		
class ReorientBone(bpy.types.Operator, AddObjectHelper):
	"""Reorient a bone while maintaining its global space animation. Useful if Bip01 is causing trouble."""
	bl_idname = "bone.reorient_bone"
	bl_label = "Reorient bone"
	bl_options = {'REGISTER', 'UNDO'}
	bone_name = StringProperty(name="Bone name", description="The bone you want to rotate.", default="Bip01")
	fixed_items = bpy.props.EnumProperty(items= (('0', 'Worldspace', 'Keep the worldspace rotation intact.'),
												 ('1', 'Bonespace', 'Correct against the changed restpose.')),
												 name = "Anim Mode")  
	def execute(self, context):
		from . import bone_tools
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "view_align"))
		return bone_tools.reorient_bone(self, context, **keywords)
		
class AddCorrectionBone(bpy.types.Operator, AddObjectHelper):
	"""Add a correction bone, which will allow you to rearrange the skeleton without breaking existing animations."""
	bl_idname = "bone.add_correction_bone"
	bl_label = "Add Correction bone"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		from . import bone_tools
		keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "view_align"))
		return bone_tools.add_correction_bone(self, context, **keywords)

class AddFXWind(bpy.types.Operator):
	"""Add a vertex group for BFB wind effect."""
	bl_idname = "object.fx_wind_add"
	bl_label = "Add FX Wind Weights"
	bl_options = {'REGISTER', 'UNDO'}
	fixed_items = bpy.props.EnumProperty(items= (('0', 'Height', 'Use height coordinate of the mesh.'),
												 ('1', 'Mesh Center Radius', 'Use distance to the mesh center.'),
												 ('2', 'Object Origin Radius', 'Use distance to the mesh origin.'),
												 ('3', 'Z Axis Distance', 'Use distance to the Z axis.')),
												 name = "Wind source")      
	wmin = FloatProperty(
			name="Minimal weight",
			description="Minimal weight used in the gradient",
			min=0.0, max=1.0,
			default=0.0, )
	wmax = FloatProperty(
			name="Maximal weight",
			description="Maximal weight used in the gradient",
			min=0.001, max=1.0,
			default=0.5, )
			
	def execute(self, context):
		from . import fx_wind
		fx_wind.add_fx_wind(self.fixed_items, self.wmin, self.wmax)
		return {'FINISHED'}

# Add to a menu
def menu_func_export(self, context):
	self.layout.operator(ExportBFB.bl_idname, text="Blue Fang Model (.bfb)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ExportDAT.bl_idname, text="Blue Fang Map (.dat)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ExportBF.bl_idname, text="Blue Fang Animation (.bf)", icon_value=preview_collection["zt2.png"].icon_id)

def menu_func_import(self, context):
	self.layout.operator(ImportBFB.bl_idname, text="Blue Fang Model (.bfb)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ImportDAT.bl_idname, text="Blue Fang Map (.dat)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ImportBF.bl_idname, text="Blue Fang Animation (.bf)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ImportPSYS.bl_idname, text="Blue Fang Particles (.psys)", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(BatchBFB.bl_idname, text="BFB and NIF Batch Processing (.bfb, .nif)", icon_value=preview_collection["zt2.png"].icon_id)

def menu_func_add_objects(self, context):
	self.layout.operator(AddCapsule.bl_idname, icon_value=preview_collection["bfb_capsule.png"].icon_id)
	self.layout.operator(AddSphere.bl_idname, icon_value=preview_collection["bfb_sphere.png"].icon_id)
	self.layout.operator(AddBox.bl_idname, icon_value=preview_collection["bfb_box.png"].icon_id)
	
def menu_func_armature(self, context):
	self.layout.operator(AddCorrectionBone.bl_idname, text="Add Correction Bone", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ReorientBone.bl_idname, text="Reorder Bone", icon_value=preview_collection["zt2.png"].icon_id)
	self.layout.operator(ToggleIKLink.bl_idname, text="Toggle IK Link", icon_value=preview_collection["zt2.png"].icon_id)
	
def menu_func_weights(self, context):
	self.layout.operator(AddFXWind.bl_idname, icon_value=preview_collection["zt2.png"].icon_id)

def register():
	import os
	icons_dir = os.path.join(os.path.dirname(__file__), "icons")
	for icon_name_ext in os.listdir(icons_dir):
		icon_name = os.path.basename(icon_name_ext)
		preview_collection.load(icon_name, os.path.join(os.path.join(os.path.dirname(__file__), "icons"), icon_name_ext), 'IMAGE')
	bpy.utils.register_module(__name__)
	
	bpy.types.INFO_MT_file_import.append(menu_func_import)
	bpy.types.INFO_MT_file_export.append(menu_func_export)
	bpy.types.INFO_MT_mesh_add.append(menu_func_add_objects)
	bpy.types.VIEW3D_PT_tools_armatureedit.append(menu_func_armature)
	bpy.types.VIEW3D_PT_tools_weightpaint.append(menu_func_weights)
	bpy.types.VIEW3D_PT_tools_object.append(menu_func_weights)
	
def unregister():
	bpy.utils.previews.remove(preview_collection)
	
	bpy.utils.unregister_module(__name__)

	bpy.types.INFO_MT_file_import.remove(menu_func_import)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)
	bpy.types.INFO_MT_mesh_add.remove(menu_func_add_objects)
	bpy.types.VIEW3D_PT_tools_armatureedit.remove(menu_func_armature)
	bpy.types.VIEW3D_PT_tools_weightpaint.remove(menu_func_weights)
	bpy.types.VIEW3D_PT_tools_object.remove(menu_func_weights)

if __name__ == "__main__":
	register()
