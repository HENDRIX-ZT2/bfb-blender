import os
import xml.etree.ElementTree as ET

class bfmat():
	def __init__(self, dirname, bfmat_file_name):
		self.dir = dirname
		self.bfmat_file = self.find_recursive(os.path.join("Materials", bfmat_file_name))
		self.tex_range = range(3)
		self.errors = []
		self.root = None
		try:
			self.root = ET.parse(self.bfmat_file).getroot()
		except TypeError:
			self.errors.append("Could not find Materials/"+bfmat_file_name)
		except ET.ParseError:
			self.errors.append("Materials/"+bfmat_file_name+" cannot be parsed, likely due to an XML syntax error!")
	
	def find_recursive(self, filename, recursiveDepth = 5):
		mat_dir = self.dir
		for dirLevel in range(0,recursiveDepth):
			file = os.path.join(mat_dir, filename)
			if os.path.exists(file): return file
			file = os.path.join(mat_dir, "shared", filename)
			if os.path.exists(file): return file
			mat_dir = os.path.dirname(mat_dir)

	def get_data(self, param):
		#return this element's data string as an appropriate data type
		res = param.text
		if "type" in param.attrib:
			if param.attrib["type"] in ("vector4", "matrix"):
				res = [float(t) for t in param.text.split(", ")]
				if param.attrib["type"] == "matrix":
					res = [res[i:i+4] for i in range(0,16,4)]
			elif param.attrib["type"] == "float":
				res = float(param.text)
			elif param.attrib["type"] == "bool":
				res = False if "false" in res.lower() else True
			# else:
				# #dword also stores ints, might not be necessary to do this
				# try:
					# res = int(res)
				# except:
					# pass
		return res

	def get_keys(self, param):
		#return this element's keys
		return [ (float(key.attrib["time"]), float(key.attrib["value"])) for key in param]
		
	def get(self, att_name):
		#get all static data of att_name
		for param in self.root:
			if param.tag == "param" and param.attrib["name"] == att_name:
				return self.get_data(param)
		
	def get_anim(self, att_name):
		dic = {}
		#get all animated data of att_name
		for param in self.root:
			if param.tag == "animate" and param.attrib["name"] == att_name:
				for child in param:
					dic[child.tag] = self.get_keys(child)
		return dic
		
	def get_range(self, att_name):
		#get all data of att_name in self.tex_range
		return [self.get(att_name+str(i)) for i in self.tex_range]
		
	def get_anim_range(self, att_name):
		#get all data of att_name in self.tex_range
		return [self.get_anim(att_name+str(i)) for i in self.tex_range]
		
	@property
	def fx(self): return self.root.attrib["fx"]
	
	@property
	def TextureTransform(self): return self.get_range("TextureTransform")
		
	@property
	def TextureAnimation(self): return self.get_anim_range("TextureTransform")
		
	@property
	def Texture(self): return self.get_range("Texture")
		
	@property
	def Texture_paths(self): return [self.find_recursive(t+".dds") for t in self.Texture if t]
		
	@property
	def TexCoordIndex(self): return self.get_range("TexCoordIndex")
		
	@property
	def MaterialEmissive(self): return self.get("MaterialEmissive")
		
	@property
	def MaterialAmbient(self): return self.get("MaterialAmbient")
		
	@property
	def MaterialPower(self): return self.get("MaterialPower")
		
	@property
	def AlphaBlendEnable(self): return self.get("AlphaBlendEnable")
		
	@property
	def AlphaTestEnable(self): return self.get("AlphaTestEnable")
		
	@property
	def CullMode(self): return self.get("CullMode")
	

# mat = bfmat("PerepatTree","PerepatTree_Wetlands_Trunk_Mat_mod0.bfmat")
# mat = bfmat("bathroomlarge_xt","bathroomlarge_xt_falling_water_mod0.bfmat")