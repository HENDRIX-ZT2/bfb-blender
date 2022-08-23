from generated.base_enum import BaseEnum

from generated.formats.bf.basic import Ubyte50


class Ubyte50Enum(BaseEnum):

	def read(self, stream):
		self._value_ = Ubyte50.from_stream(stream, None, 0, None)

	def write(self, stream):
		Ubyte50.to_stream(stream, self.value)

	@classmethod
	def from_stream(cls, stream, context=None, arg=0, template=None):
		instance = cls.from_value(Ubyte50.from_stream(stream, None, 0, None))
		return instance

	@classmethod
	def to_stream(cls, stream, instance):
		Ubyte50.to_stream(stream, instance.value)
		return instance

from generated.formats.bf.basic import Ushort1000


class Ushort1000Enum(BaseEnum):

	def read(self, stream):
		self._value_ = Ushort1000.from_stream(stream, None, 0, None)

	def write(self, stream):
		Ushort1000.to_stream(stream, self.value)

	@classmethod
	def from_stream(cls, stream, context=None, arg=0, template=None):
		instance = cls.from_value(Ushort1000.from_stream(stream, None, 0, None))
		return instance

	@classmethod
	def to_stream(cls, stream, instance):
		Ushort1000.to_stream(stream, instance.value)
		return instance

from generated.formats.bf.basic import Short1000


class Short1000Enum(BaseEnum):

	def read(self, stream):
		self._value_ = Short1000.from_stream(stream, None, 0, None)

	def write(self, stream):
		Short1000.to_stream(stream, self.value)

	@classmethod
	def from_stream(cls, stream, context=None, arg=0, template=None):
		instance = cls.from_value(Short1000.from_stream(stream, None, 0, None))
		return instance

	@classmethod
	def to_stream(cls, stream, instance):
		Short1000.to_stream(stream, instance.value)
		return instance

from generated.formats.bf.basic import Short10000


class Short10000Enum(BaseEnum):

	def read(self, stream):
		self._value_ = Short10000.from_stream(stream, None, 0, None)

	def write(self, stream):
		Short10000.to_stream(stream, self.value)

	@classmethod
	def from_stream(cls, stream, context=None, arg=0, template=None):
		instance = cls.from_value(Short10000.from_stream(stream, None, 0, None))
		return instance

	@classmethod
	def to_stream(cls, stream, instance):
		Short10000.to_stream(stream, instance.value)
		return instance
