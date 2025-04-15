from bfb_gen.formats.base.basic import Ushort, Float, Short, Ubyte


class Ubyte50(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ubyte.from_stream(stream, context, arg, template) / 50

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Ubyte.to_stream(Ubyte.from_value(round(instance * 50)), stream)


class Ushort1000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ushort.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Ushort.to_stream(Ushort.from_value(round(instance * 1000)), stream)


class Short1000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Short.to_stream(Short.from_value(round(instance * 1000)), stream)


class Short10000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 10000

    @staticmethod
    def to_stream(instance, stream, context=None, arg=0, template=None):
        Short.to_stream(Short.from_value(round(instance * 10000)), stream)
