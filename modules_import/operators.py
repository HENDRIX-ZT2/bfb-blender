import os
import bpy.utils.previews
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from util.operators import BaseOp

import import_bf
import import_bfb
import import_dat
import import_psys


class ImportOp(BaseOp, ImportHelper):

	def execute(self, context):
		return self.report_messages(self.target, filepath=self.filepath, **self.kwargs)


class BulkImportOp(ImportOp):
	# ref: https://stackoverflow.com/questions/63299327/importing-multiple-files-in-blender-import-plugin

	# necessary to support multi-file import
	files: CollectionProperty(
		type=bpy.types.OperatorFileListElement,
		options={'HIDDEN', 'SKIP_SAVE'},
	)

	# necessary to support multi-file import
	directory: StringProperty(
		subtype='DIR_PATH',
	)

	def execute(self, context):
		if self.files:
			filepaths = [file.name for file in self.files]
			result = self.report_messages(self.target, files=filepaths, filepath=self.filepath, **self.kwargs)
		# return only material result
		return {'FINISHED'}


class ImportBF(BulkImportOp):
	"""Import from BF file format (.bf)"""
	bl_idname = "import_scene.bluefang_bf"
	bl_label = 'Import BF'
	filename_ext = ".bf"
	filter_glob: StringProperty(default="*.bf", options={'HIDDEN'})
	set_fps: BoolProperty(name="Adjust FPS",
						  description="Set the scene to 30 frames per second to conform with BFs", default=True)
	target = import_bf.load


class ImportPSYS(ImportOp):
	"""Import from PSYS file format (.psys)"""
	bl_idname = "import_scene.bluefang_psys"
	bl_label = 'Import PSYS'
	filename_ext = ".psys"
	filter_glob: StringProperty(default="*.psys", options={'HIDDEN'})
	target = import_psys.load


class ImportBFB(ImportOp):
	"""Import from BFB file format (.bfb)"""
	bl_idname = "import_scene.bluefang_bfb"
	bl_label = 'Import BFB'
	filename_ext = ".bfb"
	filter_glob: StringProperty(default="*.bfb", options={'HIDDEN'})
	use_custom_normals: BoolProperty(name="Use BFB Normals", description="Preserves the original shading of a BFB.",
									 default=True)
	use_mirror_mesh: BoolProperty(name="Mirror Rigged Meshes",
							  description="Mirrors models with a skeleton. Careful, sometimes bones don't match!",
							  default=False)
	target = import_bfb.load


class ImportDAT(bpy.types.Operator, ImportHelper):
	"""Import from DAT map format (.dat)"""
	bl_idname = "import_scene.bluefang_dat"
	bl_label = 'Import DAT'
	filename_ext = ".dat"
	filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})
	target = import_dat.load

