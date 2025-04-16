from bfb_gen.formats.base.basic import Ushort, Float, Short, Ubyte

class PackedUshort(Float):

    @staticmethod
    def get_size(instance, context, arg=0, template=None):
        return 2


class Ubyte50(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ubyte.from_stream(stream, context, arg, template) / 50

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Ubyte.to_stream(Ubyte.from_value(round(instance * 50)), stream)

    @staticmethod
    def get_size(instance, context, arg=0, template=None):
        return 1

class Ushort1000(PackedUshort):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ushort.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Ushort.to_stream(Ushort.from_value(round(instance * 1000)), stream)


class Short1000(PackedUshort):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Short.to_stream(Short.from_value(round(instance * 1000)), stream)


class Short10000(PackedUshort):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 10000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Short.to_stream(Short.from_value(round(instance * 10000)), stream)
