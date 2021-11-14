from enum import Enum
from enum import auto as enum_gen
from io import BufferedRandom
from pickle import dump, load


class CharSet(Enum):
    ASCII = enum_gen()
    EXTENDED = enum_gen()
    FULL = enum_gen()


user_settings: dict[str]


def read(file: BufferedRandom) -> None:
    "Loads the contents of the given file into user_settings."
    global user_settings
    user_settings = load(file)
    file.seek(0)


def write(file: BufferedRandom) -> None:
    "Writes the current settings to the given file."
    file.truncate()
    dump(user_settings, file, 5)
