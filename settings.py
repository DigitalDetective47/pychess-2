from enum import Enum
from enum import auto as enum_gen


class CharSet(Enum):
    ASCII = enum_gen()
    EXTENDED = enum_gen()
    FULL = enum_gen()
