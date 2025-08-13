import os
import sys
import logging
import bpy
import mathutils
from bpy.props import StringProperty, FloatProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper
import bpy.utils.previews

import common_bfb
import export_bf
import export_bfb
import export_dat
from util.operators import BaseOp


class ExportOp(BaseOp, ExportHelper):

	def execute(self, context):
		return self.report_messages(self.target, filepath=self.filepath, **self.kwargs)


class ExportDAT(ExportOp):
	"""Export to DAT map format (.dat)"""
	bl_idname = "export_scene.bluefang_dat"
	bl_label = 'Export DAT'
	filename_ext = ".dat"
	filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})
	target = export_dat.save


class ExportBFB(ExportOp):
	"""Export to BFB file format (.bfb)"""
	bl_idname = "export_scene.bluefang_bfb"
	bl_label = 'Export BFB'
	filename_ext = ".bfb"
	filter_glob: StringProperty(default="*.bfb", options={'HIDDEN'})
	try:
		cfg = common_bfb.load_config()
		author = cfg["author"]
	except:
		author = "somebody"
	export_materials: BoolProperty(name="Export Materials",
								   description="Should BFMAT materials be exported? Beware, they might not be identical to the existing material!",
								   default=True)
	author_name: StringProperty(name="Author", description="A signature included in the BFB file.", default=author)
	create_lods: BoolProperty(name="Create LODs", description="Adds Levels of Detail - overwrites existing LODs!",
							  default=False)
	num_lods: IntProperty(name="Number of LODs",
						 description="Number of Levels Of Detail, including the original",
						 min=1, max=5,
						 default=2, )
	rate: IntProperty(name="Detail Decrease Rate",
					  description="The higher, the faster the detail will decrease: ratio = 1 /(LODX + Rate)",
					  min=1, max=5,
					  default=2, )
	target = export_bfb.save


	def execute(self, context):
		try:
			common_bfb.update_config("author", self.author_name)
		except:
			pass
		super().execute(context)


class ExportBF(ExportOp):
	"""Export to BF file format (.bf)"""
	bl_idname = "export_scene.bluefang_bf"
	bl_label = 'Export BF'
	filename_ext = ".bf"
	filter_glob: StringProperty(default="*.bf", options={'HIDDEN'})
	fix_tangents: BoolProperty(name="Fix Tangents",
							   description="Smoothes tangents between actions",
							   default=True)
	error: FloatProperty(name="Cleaning Error",
						 description="Adaptive Error - the more children a bone has, the less error it gets. The larger the error value, the smaller the file size, but the more error you get.",
						 precision=3, step=0.1, soft_min=0.0, min=0.0, default=0.002)
	exp_power: FloatProperty(name="Error Exponent",
							 description="This influences how fast the error increases along the bone chain. Use larger values for a steeper falloff",
							 precision=3, step=1, soft_min=1.0, min=1.0, default=1.0)

	# TODO: replace these settings with the more transparent curve UI
	# https://blender.stackexchange.com/questions/61618/add-a-custom-curve-mapping-property-for-an-add-on

	target = export_bf.save
