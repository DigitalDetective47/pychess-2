from importlib import import_module
from io import open_code
from os import name as os_name
from os import system
from typing import Final, Sequence
import settings

SYSTEM_CLEAR_SCREEN_COMMAND: Final[str] = "cls" if os_name == "nt" else "clear"
del os_name


def clear_screen() -> None:
    system(SYSTEM_CLEAR_SCREEN_COMMAND)


def menu_str(title: str, options: Sequence[str]) -> str:
    if not isinstance(title, str):
        raise TypeError("title must be of type str (not " + type(title).__name__ + ")")
    if not isinstance(options, Sequence):
        raise TypeError(
            "options must be of a sequence type (not " + type(options).__name__ + ")"
        )
    option_list_number_length: Final[int] = len(str(len(options)))
    title_offset: Final[str] = " " * (option_list_number_length + 1)
    output: str = title_offset + title + "\n" + title_offset + "-" * len(title)
    for option, option_id in zip(options, range(1, len(options) + 1)):
        output += (
            "\n"
            + ("{:>" + str(option_list_number_length) + "}|").format(option_id)
            + option
        )
    return output


def get_menu_selection(menu_length: int) -> int:
    selection: str = input()
    while not (selection.isdigit() and 1 <= (result := int(selection)) <= menu_length):
        selection = input("Enter an integer corresponding to a menu item.\n")
    return result


char_set: settings.CharSet = settings.CharSet.ASCII
