import bpy
import logging
import collections

class BaseOp(bpy.types.Operator):
	bl_options = {'REGISTER', 'UNDO'}
	target = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.infos = []
		self.warnings = []

	def show_info(self, msg: str):
		self.infos.append(msg)
		logging.info(msg)

	def show_warning(self, msg: str):
		self.warnings.append(msg)
		logging.warning(msg)

	def show_error(self, exception: Exception):
		self.report({"ERROR"}, str(exception))
		logging.exception('Got exception on main handler')

	@staticmethod
	def count(msgs):
		for msg, count in collections.Counter(msgs).items():
			if count > 1:
				msg = f"{msg} (x{count})"
			yield msg

	def flush_messages(self):
		for msg in self.count(self.warnings):
			self.report({"WARNING"}, msg)
		for msg in self.count(self.infos):
			self.report({"INFO"}, msg)

	def report_messages(self, class_method, *args, **kwargs):
		try:
			class_method(*args, **kwargs)
			result = {'FINISHED'}
		except Exception as err:
			self.show_error(err)
			result = {'CANCELLED'}
		self.flush_messages()
		return result

	@property
	def kwargs(self) -> dict:
		return self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "files", "filepath", "directory", "check_existing"))

	def execute(self, context):
		return self.report_messages(self.target, **self.kwargs)