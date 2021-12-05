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


def main() -> None:
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
    builtin_variants: Final[dict[str, module]] = sorted_variants(
        unsorted_builtin_variants
    )
    user_variants: Final[dict[str, module]] = sorted_variants(unsorted_user_variants)
    all_variants: Final[dict[str, module]] = builtin_variants | user_variants

    # Disambiguate any shared short names
    fixed_names_flags: Final[list[bool]] = [False] * len(all_variants)
    variants_tuple: Final[tuple[module]] = tuple(all_variants.values())
    unique_names: set[str] = set()
    variant_name: str
    while len(unique_names) != len(all_variants):
        variant_name = variants_tuple[len(unique_names)].SHORT_NAME
        if variant_name in unique_names:
            unique_names = set()
            for variant_index, (
                variant,
                internal_variant_name,
                is_name_fixed,
            ) in enumerate(
                zip(variants_tuple, all_variants, fixed_names_flags, strict=True)
            ):
                if not is_name_fixed and variant.SHORT_NAME == variant_name:
                    variant.SHORT_NAME += (
                        f" ({internal_variant_name.split('.', 1)[0].upper()})"
                        if "." in internal_variant_name
                        else " (BUILT-IN)"
                    )
                    fixed_names_flags[variant_index] = True
        else:
            unique_names.add(variant_name)

    # Load settings file
    settings_file_path: Final[Path] = Path.cwd() / "config.pkl"
    temp_settings_file: BufferedRandom
    try:
        with open(settings_file_path, "x+b") as settings_file:
            settings.user_settings = {
                None: {"char_set": settings.CharSet.ASCII, "dark_mode": False}
            }
            settings.write(temp_settings_file)
    except FileExistsError:
        pass
    with open(settings_file_path, "r+b") as settings_file:
        settings.read(settings_file)

        # Add variant settings to settings file if not already added
        for variant in all_variants.values():
            if variant.UUID not in settings.user_settings:
                settings.user_settings[variant.UUID] = variant.DEFAULT_VARIANT_SETTINGS
            del variant.DEFAULT_VARIANT_SETTINGS

        def letter_index(number: SupportsIndex) -> str:
            value: int = number.__index__() + 1
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
            menu.clear_screen()
            input(info + "\n")

        def set_char_set(char_set: settings.CharSet) -> None:
            settings.user_settings[None]["char_set"] = char_set
            settings.write(settings_file)

        def set_dark_mode(value: bool) -> None:
            settings.user_settings[None]["dark_mode"] = value
            settings.write(settings_file)

        def variant_infobox(variant: module) -> None:
            user_input: str = input(
                f"|{variant.LONG_NAME}\n|\n|Programmer: {variant.PROGRAMMER}\n|\n|{variant.DESCRIPTION}\n\nWould you like to play this variant (Y/N)? "
                if variant.INVENTOR is None
                else f"|{variant.LONG_NAME}\n|\n|Inventor: {variant.INVENTOR}\n|Programmer: {variant.PROGRAMMER}\n|\n|{variant.DESCRIPTION}\n\nWould you like to play this variant (Y/N)? "
            )
            menu.clear_screen()
            while user_input not in frozenset({"N", "Y"}):
                user_input = input('Type either "Y" or "N". ')
            if user_input == "Y":
                variant.main()

        BACK_OPTION_DICT: Final[dict[str, menu.MenuOption]] = {"<": menu.BACK_OPTION}

        CHAR_SET_MENU: Final[menu.DynamicMenu] = menu.DynamicMenu(
            compile(
                "f'CHARACTER SET: {settings.user_settings[None][\"char_set\"].name}'",
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
                    "Controls what characters are used in the game's output. A wider character range leads to nicer looking output, but also increases the risk of missing characters.\n\n - ASCII (COMPATIBILITY MODE, DEFAULT): Only allows letters, numbers, and other symbols found on a standard US keyboard. Most limited, but universally compatible.\n - BMP (RECCOMENDED): Allows all characters in ASCII, alongside many other common characters that are available by default in most operating systems. More varied, but less compatible.\n - FULL: Allows all possible characters. Most varied, but poor compatibility.",
                ),
            ),
            "1": menu.MenuOption(
                "ASCII (COMPATIBILITY MODE, DEFAULT)",
                partial(set_char_set, settings.CharSet.ASCII),
            ),
            "2": menu.MenuOption(
                "BMP (RECCOMENDED)", partial(set_char_set, settings.CharSet.BMP)
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
                    for variant_id, variant in enumerate(builtin_variants.values())
                    if variant.SETTINGS_MENU is not None
                }
                | {
                    str(variant_id): menu.MenuOption(
                        variant.SHORT_NAME, variant.SETTINGS_MENU
                    )
                    for variant_id, variant in enumerate(user_variants.values(), 1)
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
                                variant.SHORT_NAME, partial(variant_infobox, variant)
                            )
                            for variant_id, variant in enumerate(
                                user_variants.values(), 1
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
                            "{'1': menu.MenuOption(f'CHARACTER SET: {settings.user_settings[None][\"char_set\"].name}', CHAR_SET_MENU), '2': menu.MenuOption('DARK MODE: ON' if settings.user_settings[None]['dark_mode'] else 'DARK MODE: OFF', DARK_MODE_MENU)} | ({} if all([variant.SETTINGS_MENU is None for variant in all_variants.values()]) else {'...': VARIANT_SPECIFIC_SETTINGS_MENU_OPTION}) | BACK_OPTION_DICT",
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


if __name__ == "__main__":
    # Set working directory to location of run.py
    chdir(path.dirname(path.abspath(__file__)))
    main()
