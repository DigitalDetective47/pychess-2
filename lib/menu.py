import collections.abc as abc
from functools import partial
from importlib import import_module
from inspect import signature
from os import name as os_name
from os import system
from types import CodeType as code
from typing import Callable, Final, Iterator, Mapping, NoReturn

import lib.settings

SYSTEM_CLEAR_SCREEN_COMMAND: Final[str] = "cls" if os_name == "nt" else "clear"
del os_name


def clear_screen() -> None:
    "Clears the terminal."
    system(SYSTEM_CLEAR_SCREEN_COMMAND)


class MenuExit(BaseException):
    pass


class MenuOption(abc.Callable):
    def __init__(self, name: str, action: Callable[[], None]) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "name must be of type str (not " + type(name).__name__ + ")"
            )
        elif not callable(action):
            raise TypeError("action must be a callable object")
        elif signature(action).parameters:
            raise ValueError("action must not have arguments")
        self.name: Final[str] = name
        self.action: Final[Callable[[], None]] = action

    def __bytes__(self) -> bytes:
        return bytes(self.name)

    def __call__(self) -> None:
        self.action()

    def __repr__(self) -> str:
        return "MenuOption(" + repr(self.name) + ", " + repr(self.action) + ")"

    def __str__(self) -> str:
        return self.name


class StaticMenu(abc.Callable, abc.MutableMapping):
    def __init__(self, title: str, options: Mapping[str, MenuOption]) -> None:
        if not isinstance(title, str):
            raise TypeError(
                "title must be of type str (not " + type(title).__name__ + ")"
            )
        elif not isinstance(options, Mapping):
            raise TypeError(
                "options must be of type Mapping (not " + type(title).__name__ + ")"
            )
        self.options: Final[dict[str, MenuOption]] = {}
        for index, option in options.items():
            if not isinstance(index, str):
                raise TypeError(
                    "options keys must be of type str (not "
                    + type(index).__name__
                    + ")"
                )
            elif not isinstance(option, MenuOption):
                raise TypeError(
                    "options values must be of type MenuOption (not "
                    + type(option).__name__
                    + ")"
                )
            self.options[str(index)] = option
        menu_option_width: Final[int] = max([len(index) for index in options.keys()])
        title_offset: Final[str] = " " * (menu_option_width + 1)
        appearance: str = title_offset + title + "\n" + title_offset + "-" * len(title)
        for index, option in options.items():
            appearance += ("\n{:>" + str(menu_option_width) + "}|").format(
                index
            ) + option.name
        self.appearance: Final[str] = appearance

    def __bytes__(self) -> bytes:
        return bytes(self.appearance)

    def __call__(self) -> None:
        "Displays the menu and prompts the user to select an option. This repeats until a MenuExit is recieved."
        try:
            while True:
                clear_screen()
                print(self.appearance + "\n")
                selected_action: Callable[[], None]
                try:
                    selected_action = self.options[input()].action
                except KeyError:
                    while True:
                        try:
                            selected_action = self.options[
                                input("Select a menu item listed.\n")
                            ].action
                        except KeyError:
                            pass
                        else:
                            break
                selected_action()
        except MenuExit:
            pass

    def __delitem__(self, key: str) -> None:
        try:
            line_number: int = tuple(self.options).index(key) + 2
        except ValueError:
            raise KeyError(key)
        del self.options[key]
        appearance_lines: str = self.appearance.splitlines(True)
        self.appearance = "".join(
            appearance_lines[:line_number] + appearance_lines[line_number + 1 :]
        )

    def __getitem__(self, key: str) -> MenuOption:
        return self.options[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.options)

    def __len__(self) -> int:
        return len(self.options)

    def __repr__(self) -> str:
        display_lines: Final[list[str]] = self.appearance.splitlines()
        return (
            "StaticMenu("
            + repr(display_lines[0][display_lines[1].count(" ") :])
            + ", "
            + repr(self.options)
            + ")"
        )

    def __setitem__(self, key: str, value: MenuOption) -> None:
        if key in self.options:
            self.options[key] = value
            line_number: int = tuple(self.options).index(key) + 2
            appearance_lines: str = self.appearance.splitlines()
            self.appearance = "\n".join(
                appearance_lines[:line_number]
                + [
                    ("{:>" + str(appearance_lines[1].count(" ")) + "}|").format(key)
                    + value.name
                ]
                + appearance_lines[line_number + 1 :]
            )
        else:
            self.options[key]
            self.appearance += (
                "\n{:>" + str(self.appearance.splitlines()[1].count(" ") - 1) + "}|"
            ).format(key) + value.name

    def __str__(self) -> str:
        return self.appearance


class DynamicMenu(abc.Callable):
    def __init__(
        self, title_expression: code | str, options_expression: code | str
    ) -> None:
        self.title_expr: Final[code | str] = title_expression
        self.options_expr: Final[code | str] = options_expression

    def generate_static(self) -> StaticMenu:
        return StaticMenu(eval(self.title_expr), eval(self.options_expr))

    def __bytes__(self) -> bytes:
        return bytes(self.generate_static())

    def __call__(self) -> None:
        "Displays the menu and prompts the user to select an option. This repeats until a MenuExit is recieved."
        try:
            while True:
                title: str = eval(self.title_expr)
                options: Mapping[str, MenuOption] = eval(self.options_expr)
                if not isinstance(title, str):
                    raise TypeError(
                        "title_expression must evaluate to type str (not "
                        + type(title).__name__
                        + ")"
                    )
                elif not isinstance(options, Mapping):
                    raise TypeError(
                        "options_expressions must evaluate to type Mapping (not "
                        + type(title).__name__
                        + ")"
                    )
                actions: Final[dict[str, Callable[[], None]]] = {}
                for index, option in options.items():
                    if not isinstance(index, str):
                        raise TypeError(
                            "options_expressions keys must be of type str (not "
                            + type(index).__name__
                            + ")"
                        )
                    elif not isinstance(option, MenuOption):
                        raise TypeError(
                            "options_expressions values must be of type MenuOption (not "
                            + type(option).__name__
                            + ")"
                        )
                    actions[str(index)] = option.action
                menu_option_width: Final[int] = max(
                    [len(index) for index in options.keys()]
                )
                title_offset: Final[str] = " " * (menu_option_width + 1)
                appearance: str = (
                    title_offset + title + "\n" + title_offset + "-" * len(title)
                )
                for index, option in options.items():
                    appearance += (
                        "\n"
                        + ("{:>" + str(menu_option_width) + "}|").format(index)
                        + option.name
                    )
                clear_screen()
                print(appearance + "\n")
                selected_action: Callable[[], None]
                try:
                    selected_action = actions[input()]
                except KeyError:
                    while True:
                        try:
                            selected_action = actions[
                                input("Select a menu item listed.\n")
                            ]
                        except KeyError:
                            pass
                        else:
                            break
                selected_action()
        except MenuExit:
            pass

    def __repr__(self) -> str:
        return (
            "DynamicMenu("
            + repr(self.title_expr)
            + ", "
            + repr(self.options_expr)
            + ")"
        )

    def __str__(self) -> str:
        return str(self.generate_static())


def raise_menuexit() -> NoReturn:
    raise MenuExit


BACK_OPTION: Final[MenuOption] = MenuOption("BACK", raise_menuexit)


def main():
    def set_user_char_set(char_set: lib.settings.CharSet) -> None:
        if not isinstance(char_set, lib.settings.CharSet):
            raise ValueError(
                "char_set must be of type CharSet (not " + type(char_set).__name__ + ")"
            )
        lib.settings.user_char_set = char_set

    def option_info(info: str) -> None:
        if not isinstance(info, str):
            raise ValueError(
                "info must be of type str (not " + type(info).__name__ + ")"
            )
        clear_screen()
        input(info + "\n")

    global CHAR_SET_INFO_OPTION
    global CHAR_SET_ASCII_OPTION
    global CHAR_SET_EXTENDED_OPTION
    global CHAR_SET_FULL_OPTION
    CHAR_SET_INFO_OPTION = MenuOption(
        "ABOUT THIS OPTION",
        partial(
            option_info,
            "Controls what characters are used in the game's output. A wider character range leads to nicer looking output, but also increases the risk of missing characters.\n\n - ASCII (COMPATIBILITY MODE, DEFAULT): Only allows letters, numbers, and other symbols found on a standard US keyboard. Most limited, but universally compatible.\n - EXTENDED (RECCOMENDED): Allows all characters in ASCII, alongside many additional characters included in default fonts on most operating systems. More varied, but less compatible.\n - FULL: Allows all possible characters. Most varied, but poor compatibility.",
        ),
    )
    CHAR_SET_ASCII_OPTION = MenuOption(
        "ASCII (COMPATIBILITY MODE, DEFAULT)",
        partial(set_user_char_set, lib.settings.CharSet.ASCII),
    )
    CHAR_SET_EXTENDED_OPTION = MenuOption(
        "EXTENDED (RECCOMENDED)",
        partial(set_user_char_set, lib.settings.CharSet.EXTENDED),
    )
    CHAR_SET_FULL_OPTION = MenuOption(
        "FULL", partial(set_user_char_set, lib.settings.CharSet.FULL)
    )

    StaticMenu(
        "MAIN MENU",
        {
            "1": MenuOption(
                "SETTINGS",
                DynamicMenu(
                    compile("'SETTINGS'", __file__, "eval"),
                    compile(
                        "{'1': MenuOption('CHARACTER SET: ' + lib.settings.user_char_set.name, DynamicMenu(compile(\"'CHARACTER SET: ' + lib.settings.user_char_set.name\", __file__, 'eval'), compile(\"{'?': CHAR_SET_INFO_OPTION, '1': CHAR_SET_ASCII_OPTION, '2': CHAR_SET_EXTENDED_OPTION, '3': CHAR_SET_FULL_OPTION, '<': BACK_OPTION}\", __file__, 'eval'))), '<': BACK_OPTION}",
                        __file__,
                        "eval",
                    ),
                ),
            ),
            "X": MenuOption("QUIT", raise_menuexit),
        },
    )()
