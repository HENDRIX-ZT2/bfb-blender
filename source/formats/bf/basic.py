from generated.formats.base.basic import Ushort, Float, Short, Ubyte


class Ubyte50(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ubyte.from_stream(stream, context, arg, template) / 50

    @staticmethod
    def to_stream(stream, instance):
        Ubyte.to_stream(stream, round(instance * 50))


class Ushort1000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Ushort.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(stream, instance):
        Ushort.to_stream(stream, round(instance * 1000))


class Short1000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 1000

    @staticmethod
    def to_stream(stream, instance):
        Short.to_stream(stream, round(instance * 1000))


class Short10000(Float):
    @staticmethod
    def from_stream(stream, context=None, arg=0, template=None):
        return Short.from_stream(stream, context, arg, template) / 10000

    @staticmethod
    def to_stream(stream, instance):
        Short.to_stream(stream, round(instance * 10000))
