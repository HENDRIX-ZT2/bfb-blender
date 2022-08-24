from generated.formats.bf import BfFile
import os
from root_path import root_dir

in_dir = os.path.join(root_dir, "bf_input")
out_dir = os.path.join(root_dir, "bf_output")

bf = BfFile()
for root, dirs, files in os.walk(in_dir):
	for name in files:
		if name.lower().endswith(".bf"):
			src_path = os.path.join(root, name)
			rel = os.path.relpath(src_path, in_dir)
			out_path = os.path.join(out_dir, rel)
			os.makedirs(out_path, exist_ok=True)
			print(f"Converting {src_path} to {out_path}")

			bf.load(src_path)
			bf.header.version = 2
			bf.context.version = 2
			bf.save(out_path)
