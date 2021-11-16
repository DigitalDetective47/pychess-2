from functools import partial
from glob import glob
from importlib import import_module
from io import BufferedRandom
from os import chdir, path
from pathlib import Path
from string import ascii_uppercase
from types import ModuleType as module
from typing import Callable, Final, Optional, SupportsIndex

from lib import menu, settings

# Set working directory to location of run.py
chdir(path.dirname(path.abspath(__file__)))
del chdir, path

# Load all variants
unsorted_builtin_variants: Final[dict[str, module]] = {}
full_name: str
truncated_name: str
unfiltered_name: str
unsorted_user_variants: Final[dict[str, module]] = {}
for file_path in glob("variants/*.py") + glob("variants/*/*.py"):
    unfiltered_name = file_path[:-3]
    if "." in unfiltered_name:
        raise RuntimeError("variant paths should not contain periods")
    full_name = unfiltered_name.replace("/", ".").replace("\\", ".")
    truncated_name = full_name[9:]
    if "." in truncated_name:
        unsorted_user_variants[truncated_name] = import_module(full_name)
    else:
        unsorted_builtin_variants[truncated_name] = import_module(full_name)
sorted_variants: Final[
    Callable[[dict[str, module]], dict[str, module]]
] = lambda x: dict(sorted(x.items(), key=lambda y: y[1].UUID))
builtin_variants: Final[dict[str, module]] = sorted_variants(unsorted_builtin_variants)
user_variants: Final[dict[str, module]] = sorted_variants(unsorted_user_variants)
all_variants: Final[dict[str, module]] = builtin_variants | user_variants
del (
    file_path,
    full_name,
    truncated_name,
    unfiltered_name,
    unsorted_builtin_variants,
    unsorted_user_variants,
)

# Disambiguate any shared short names
fixed_names_flags: Final[list[bool]] = [False] * len(all_variants)
variants_tuple: Final[tuple[module]] = tuple(all_variants.values())
unique_names: set[str] = set()
variant_name: str
while len(unique_names) != len(all_variants):
    variant_name = variants_tuple[len(unique_names)].SHORT_NAME
    if variant_name in unique_names:
        unique_names = set()
        for variant, internal_variant_name, is_name_fixed, variant_index in zip(
            variants_tuple,
            all_variants,
            fixed_names_flags,
            range(len(all_variants)),
            strict=True,
        ):
            if not is_name_fixed and variant.SHORT_NAME == variant_name:
                variant.SHORT_NAME += (
                    (" (" + internal_variant_name.split(".", 1)[0].upper() + ")")
                    if "." in internal_variant_name
                    else " (BUILT-IN)"
                )
                fixed_names_flags[variant_index] = True
    else:
        unique_names.add(variant_name)
del (
    fixed_names_flags,
    variant_name,
    variants_tuple,
    unique_names,
)

# Load settings file
settings_file_path: Final[Path] = Path.cwd() / "config.pkl"
temp_settings_file: BufferedRandom
try:
    temp_settings_file = open(settings_file_path, "r+b")
except FileNotFoundError:
    temp_settings_file = open(settings_file_path, "x+b")
    settings.user_settings = {
        None: {
            "char_set": settings.CharSet.ASCII,
            "dark_mode": False,
        }
    }
else:
    settings.read(temp_settings_file)
settings_file: Final[BufferedRandom] = temp_settings_file
del settings_file_path, temp_settings_file

try:
    # Add variant settings to settings file if not already added
    for variant in all_variants.values():
        if variant.UUID not in settings.user_settings:
            settings.user_settings[variant.UUID] = variant.DEFAULT_VARIANT_SETTINGS
        del variant.DEFAULT_VARIANT_SETTINGS
    del variant

    def letter_index(number: SupportsIndex) -> str:
        try:
            value: int = number.__index__() + 1
        except AttributeError:
            raise TypeError(
                "number must be of type SupportsIndex (not "
                + type(number).__name__
                + ")"
            )
        letters: Final[list[str]] = []
        remainder: int
        while value > 0:
            value, remainder = divmod(value)
            if remainder == 0:
                value -= 1
                remainder += 26
            letters.append(ascii_uppercase[remainder - 1])
        return "".join(reversed(letters))

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
        settings.user_settings[None]["char_set"] = char_set
        settings.write(settings_file)

    def set_dark_mode(value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError(
                "value must be of type bool (not " + type(value).__name__ + ")"
            )
        settings.user_settings[None]["dark_mode"] = value
        settings.write(settings_file)

    def variant_infobox(variant: module) -> None:
        if not isinstance(variant, module):
            raise TypeError(
                "variant must be of type ModuleType (not "
                + type(variant).__name__
                + ")"
            )
        user_input: Optional[str] = None
        menu.clear_screen()
        while user_input not in frozenset({"Y", "N"}):
            user_input = input(
                "|"
                + variant.LONG_NAME
                + "\n|"
                + (
                    ""
                    if variant.INVENTOR is None
                    else "\n|Inventor: " + variant.INVENTOR
                )
                + "\n|Programmer: "
                + variant.PROGRAMMER
                + "\n|\n|"
                + variant.DESCRIPTION
                + "\n\nWould you like to play this variant (Y/N)? "
                if user_input is None
                else 'Type either "Y" or "N". '
            )
        if user_input == "Y":
            variant.main()

    BACK_OPTION_DICT: Final[dict[str, menu.MenuOption]] = {"<": menu.BACK_OPTION}

    CHAR_SET_MENU: Final[menu.DynamicMenu] = menu.DynamicMenu(
        compile(
            "'CHARACTER SET: ' + settings.user_settings[None]['char_set'].name",
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
            "'DARK MODE: ON' if settings.user_settings[None]['dark_mode'] else 'DARK MODE: OFF'",
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

    VARIANT_SPECIFIC_SETTINGS_MENU_OPTION: Final[menu.MenuOption] = menu.MenuOption(
        "VARIANT-SPECIFIC SETTINGS",
        menu.StaticMenu(
            "VARIANT-SPECIFIC SETTINGS",
            {
                letter_index(variant_id): menu.MenuOption(
                    variant.SHORT_NAME, variant.SETTINGS_MENU
                )
                for variant_id, variant in zip(
                    range(len(builtin_variants)),
                    builtin_variants.values(),
                    strict=True,
                )
                if variant.SETTINGS_MENU is not None
            }
            | {
                str(variant_id): menu.MenuOption(
                    variant.SHORT_NAME, variant.SETTINGS_MENU
                )
                for variant_id, variant in zip(
                    range(1, len(user_variants) + 1),
                    user_variants.values(),
                    strict=True,
                )
                if variant.SETTINGS_MENU is not None
            }
            | BACK_OPTION_DICT,
        ),
    )

    menu.StaticMenu(
        "MAIN MENU",
        {
            "1": menu.MenuOption(
                "PLAY VARIANT",
                menu.StaticMenu(
                    "PLAY VARIANT",
                    {
                        str(variant_id): menu.MenuOption(
                            variant_module.SHORT_NAME,
                            partial(
                                variant_infobox,
                                variant_module,
                            ),
                        )
                        for variant_id, variant_module in zip(
                            range(1, len(user_variants) + 1),
                            user_variants.values(),
                            strict=True,
                        )
                    }
                    | {"<": menu.BACK_OPTION},
                ),
            ),
            "2": menu.MenuOption("SANDBOX", builtin_variants["sandbox"].main),
            "3": menu.MenuOption(
                "SETTINGS",
                menu.DynamicMenu(
                    compile("'SETTINGS'", __file__, "eval"),
                    compile(
                        "{'1': menu.MenuOption('CHARACTER SET: ' + settings.user_settings[None]['char_set'].name, CHAR_SET_MENU), '2': menu.MenuOption('DARK MODE: ON' if settings.user_settings[None]['dark_mode'] else 'DARK MODE: OFF', DARK_MODE_MENU)} | ({} if all([variant.SETTINGS_MENU is None for variant in all_variants.values()]) else {'...': VARIANT_SPECIFIC_SETTINGS_MENU_OPTION}) | BACK_OPTION_DICT",
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
    settings_file.close()
