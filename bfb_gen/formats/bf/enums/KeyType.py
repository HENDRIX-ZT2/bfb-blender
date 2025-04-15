from bfb_gen.base_enum import BaseEnum
from bfb_gen.formats.base.basic import Ushort


class KeyType(BaseEnum):

	__name__ = 'KeyType'
	_storage = Ushort

	LOC_QUADRATIC = 1
	LOC_LINEAR = 2
	EULER_X_QUADRATIC = 6
	EULER_Y_QUADRATIC = 7
	EULER_Z_QUADRATIC = 8
	QUATERNION_QUADRATIC = 12
	QUATERNION_LINEAR = 14
	SCALE_QUADRATIC = 16
	SCALE_LINEAR = 17
