"""Settings data for PyChess 2.

Classes:
CharSet -- Character sets for the program to use.

Functions:
read -- Load the contents of the given file into user_settings.
write -- Write the current settings to the given file.

Objects:
user_settings -- A dict containing all of the user's settings.
"""

from enum import Enum
from enum import auto as enum_gen
from enum import unique
from io import BufferedRandom
from pickle import dump, load
from typing import Any, Optional


@unique
class CharSet(Enum):
    """Character sets for the program to use.

    Enumeration members:
    ASCII
    BMP
    FULL
    """

    ASCII = enum_gen()
    """Only use ASCII characters (U+0000-U+007F)"""
    BMP = enum_gen()
    """Use only characters from the BMP (U+0000-U+FFFF)"""
    FULL = enum_gen()
    """Use all possible unicode characters (U+0000-U+10FFFF)"""


user_settings: dict[Optional[bytes], Any]
"""A dict containing all of the user's settings.

Global settings are contained within the None key, and variant-specific settings are contained within the key of their UUID.
"""


def read(file: BufferedRandom, /) -> None:
    """Load the contents of the given file into user_settings.

    Required positional arguments:
    file -- The file to load settings from.
    """
    global user_settings
    user_settings = load(file)
    file.seek(0)


def write(file: BufferedRandom, /) -> None:
    """Write the current settings to the given file.

    Required positional arguments:
    file -- The file to write settings to.
    """
    file.truncate()
    dump(user_settings, file, 5)
    file.seek(0)
