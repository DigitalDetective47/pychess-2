from functools import partial
from io import BufferedRandom
from os import chdir, path
from pathlib import Path
from typing import Final

from lib import menu, settings

chdir(path.dirname(path.abspath(__file__)))
del chdir, path

settings_file_path: Path = Path.cwd() / "config.pkl"
settings_file: BufferedRandom
try:
    settings_file = open(settings_file_path, "r+b")
except FileNotFoundError:
    settings_file = open(settings_file_path, "x+b")
    settings.global_user_settings = {
        "char_set": settings.CharSet.ASCII,
        "dark_mode": False,
    }
else:
    settings.read(settings_file)
del settings_file_path

try:
    def option_info(info: str) -> None:
        if not isinstance(info, str):
            raise ValueError(
                "info must be of type str (not " + type(info).__name__ + ")"
            )
        menu.clear_screen()
        input(info + "\n")

    def set_char_set(char_set: settings.CharSet) -> None:
        if not isinstance(char_set, settings.CharSet):
            raise ValueError(
                "char_set must be of type CharSet (not " + type(char_set).__name__ + ")"
            )
        settings.global_user_settings["char_set"] = char_set

    def set_dark_mode(value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError(
                "value must be of type bool (not " + type(value).__name__ + ")"
            )
        settings.global_user_settings["dark_mode"] = value

    CHAR_SET_MENU: Final[menu.DynamicMenu] = menu.DynamicMenu(
        compile(
            "'CHARACTER SET: ' + settings.global_user_settings['char_set'].name",
            __file__,
            "eval",
        ),
        compile("CHAR_SET_MENU_OPTIONS", __file__, "eval"),
        globals(),
        locals(),
    )
    CHAR_SET_MENU_OPTIONS: Final[dict[str, menu.MenuOption]] = {
        "?": menu.MenuOption(
            "ABOUT THIS OPTION",
            partial(
                option_info,
                "Controls what characters are used in the game's output. A wider character range leads to nicer looking output, but also increases the risk of missing characters.\n\n - ASCII (COMPATIBILITY MODE, DEFAULT): Only allows letters, numbers, and other symbols found on a standard US keyboard. Most limited, but universally compatible.\n - EXTENDED (RECCOMENDED): Allows all characters in ASCII, alongside many additional characters included in default fonts on most operating systems. More varied, but less compatible.\n - FULL: Allows all possible characters. Most varied, but poor compatibility.",
            ),
        ),
        "1": menu.MenuOption(
            "ASCII (COMPATIBILITY MODE, DEFAULT)",
            partial(set_char_set, settings.CharSet.ASCII),
        ),
        "2": menu.MenuOption(
            "EXTENDED (RECCOMENDED)",
            partial(set_char_set, settings.CharSet.EXTENDED),
        ),
        "3": menu.MenuOption("FULL", partial(set_char_set, settings.CharSet.FULL)),
        "<": menu.BACK_OPTION,
    }

    DARK_MODE_MENU: Final[menu.DynamicMenu] = menu.DynamicMenu(
        compile(
            "'DARK MODE: O' + ('N' if settings.global_user_settings['dark_mode'] else 'FF')",
            __file__,
            "eval",
        ),
        compile("DARK_MODE_MENU_OPTIONS", __file__, "eval"),
        globals(),
        locals(),
    )
    DARK_MODE_MENU_OPTIONS: Final[dict[str, menu.MenuOption]] = {
        "?": menu.MenuOption(
            "ABOUT THIS OPTION",
            partial(
                option_info,
                "Inverts the game's checkerboard pattern and swaps black and white piece characters. Enable this option if text is lighter than the background.",
            ),
        ),
        "1": menu.MenuOption("DISABLED (DEFAULT)", partial(set_dark_mode, False)),
        "2": menu.MenuOption("ENABLED", partial(set_dark_mode, True)),
        "<": menu.BACK_OPTION,
    }

    menu.StaticMenu(
        "MAIN MENU",
        {
            "1": menu.MenuOption(
                "SANDBOX", partial(menu.run_variant, "sandbox", False)
            ),
            "2": menu.MenuOption(
                "SETTINGS",
                menu.DynamicMenu(
                    compile("'SETTINGS'", __file__, "eval"),
                    compile(
                        "{'1': menu.MenuOption('CHARACTER SET: ' + settings.global_user_settings['char_set'].name, CHAR_SET_MENU), '2': menu.MenuOption('DARK MODE: O' + ('N' if settings.global_user_settings['dark_mode'] else 'FF'), DARK_MODE_MENU), '<': menu.BACK_OPTION}",
                        __file__,
                        "eval",
                    ),
                    globals(),
                    locals(),
                ),
            ),
            "X": menu.MenuOption("QUIT", menu.raise_stop_menu),
        },
    )()
finally:
    settings.write(settings_file)
    settings_file.close()
