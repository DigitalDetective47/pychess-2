import collections.abc as abc
from functools import partial
from importlib import import_module
from inspect import signature
from os import name as os_name
from os import system
from types import CodeType as code
from typing import Callable, Final, NoReturn

import settings

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


class Menu(abc.Callable):
    def __init__(self, title: str, options: dict[str, MenuOption]) -> None:
        if not isinstance(title, str):
            raise TypeError(
                "title must be of type str (not " + type(title).__name__ + ")"
            )
        elif not isinstance(options, dict):
            raise TypeError(
                "options must be of type dict (not " + type(title).__name__ + ")"
            )
        self.actions: Final[dict[str, Callable[[], None]]] = {}
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
            self.actions[str(index)] = option.action
        menu_option_width: Final[int] = max([len(index) for index in options.keys()])
        title_offset: Final[str] = " " * (menu_option_width + 1)
        appearance: str = title_offset + title + "\n" + title_offset + "-" * len(title)
        for index, option in options.items():
            appearance += (
                "\n"
                + ("{:>" + str(menu_option_width) + "}|").format(index)
                + option.name
            )
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
                    selected_action = self.actions[input()]
                except KeyError:
                    while True:
                        try:
                            selected_action = self.actions[
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
        display_lines: Final[list[str]] = self.appearance.splitlines()
        sidebar_width: Final[int] = display_lines[1].count(" ")
        return (
            "Menu("
            + repr(display_lines[0][sidebar_width:])
            + ", {"
            + ", ".join(
                [
                    repr(index)
                    + ": MenuOption("
                    + repr(display_lines[line_number][sidebar_width:])
                    + ", "
                    + repr(action)
                    + ")"
                    for index, line_number, action in zip(
                        self.actions.keys(),
                        range(2, len(display_lines)),
                        self.actions.values(),
                    )
                ]
            )
            + "})"
        )

    def __str__(self) -> str:
        return self.appearance


class DynamicMenu(Menu):
    def __init__(
        self, title_expression: code | str, options_expression: code | str
    ) -> None:
        self.title_expr: Final[code | str] = title_expression
        self.options_expr: Final[code | str] = options_expression

    def generate_static(self) -> Menu:
        return Menu(eval(self.title_expr), eval(self.options_expr))

    def __bytes__(self) -> bytes:
        return bytes(self.generate_static())

    def __call__(self) -> None:
        "Displays the menu and prompts the user to select an option. This repeats until a MenuExit is recieved."
        try:
            while True:
                title: str = eval(self.title_expr)
                options: dict[str, MenuOption] = eval(self.options_expr)
                if not isinstance(title, str):
                    raise TypeError(
                        "title must be of type str (not " + type(title).__name__ + ")"
                    )
                elif not isinstance(options, dict):
                    raise TypeError(
                        "options must be of type dict (not "
                        + type(title).__name__
                        + ")"
                    )
                actions: Final[dict[str, Callable[[], None]]] = {}
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
    def set_user_char_set(char_set: settings.CharSet) -> None:
        if not isinstance(char_set, settings.CharSet):
            raise ValueError(
                "char_set must be of type CharSet (not " + type(char_set).__name__ + ")"
            )
        settings.user_char_set = char_set


    def option_info(info: str) -> None:
        if not isinstance(info, str):
            raise ValueError("info must be of type str (not " + type(info).__name__ + ")")
        clear_screen()
        input(info + "\n")


    CHAR_SET_INFO_OPTION: Final[MenuOption] = MenuOption(
        "ABOUT THIS OPTION",
        partial(
            option_info,
            "Controls what characters are used in the game's output. A wider character range leads to nicer looking output, but also increases the risk of missing characters.\n\n - ASCII (COMPATIBILITY MODE, DEFAULT): Only allows letters, numbers, and other symbols found on a standard US keyboard. Most limited, but universally compatible.\n - EXTENDED (RECCOMENDED): Allows all characters in ASCII, alongside many additional characters included in default fonts on most operating systems. More varied, but less compatible.\n - FULL: Allows all possible characters. Most varied, but poor compatibility.",
        ),
    )
    CHAR_SET_ASCII_OPTION: Final[MenuOption] = MenuOption(
        "ASCII (COMPATIBILITY MODE, DEFAULT)",
        partial(set_user_char_set, settings.CharSet.ASCII),
    )
    CHAR_SET_EXTENDED_OPTION: Final[MenuOption] = MenuOption(
        "EXTENDED (RECCOMENDED)", partial(set_user_char_set, settings.CharSet.EXTENDED)
    )
    CHAR_SET_FULL_OPTION: Final[MenuOption] = MenuOption(
        "FULL", partial(set_user_char_set, settings.CharSet.FULL)
    )

    Menu(
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
