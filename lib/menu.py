import collections.abc as abc
from functools import partial
from importlib import import_module
from os import name as os_name
from os import system
from types import CodeType as code
from types import ModuleType as module
from typing import Any, Callable, Final, Iterator, Mapping, NoReturn


class MenuExit(BaseException):
    "Base class for menu-closing exceptions."


class StopMenu(MenuExit):
    "Close the current menu."


class BreakMenu(MenuExit):
    "Close the current menu and re-raise this exception."


class MenuOption(abc.Callable):
    def __init__(self, name: str, action: Callable[[], None]) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "name must be of type str (not " + type(name).__name__ + ")"
            )
        elif not callable(action):
            raise TypeError("action must be a callable object")
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
    pass


class StaticMenu(Menu, abc.MutableMapping):
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
        "Displays the menu and prompts the user to select an option. This repeats until a StopMenu is recieved."
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
        except StopMenu:
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


class DynamicMenu(Menu):
    def __init__(
        self,
        title_expression: code | str,
        options_expression: code | str,
        global_context: dict[str, Any],
        local_context: dict[str, Any],
    ) -> None:
        self.title_expr: Final[code | str] = title_expression
        self.options_expr: Final[code | str] = options_expression
        self.globals: dict[str, Any] = global_context
        self.locals: dict[str, Any] = local_context

    def generate_static(self) -> StaticMenu:
        return StaticMenu(
            eval(self.title_expr, self.globals, self.locals),
            eval(self.options_expr, self.globals, self.locals),
        )

    def __bytes__(self) -> bytes:
        return bytes(self.generate_static())

    def __call__(self) -> None:
        "Displays the menu and prompts the user to select an option. This repeats until a StopMenu is recieved."
        try:
            while True:
                title: str = eval(self.title_expr, self.globals, self.locals)
                options: Mapping[str, MenuOption] = eval(
                    self.options_expr, self.globals, self.locals
                )
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
        except StopMenu:
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


def raise_stop_menu() -> NoReturn:
    raise StopMenu


def raise_break_menu() -> NoReturn:
    raise BreakMenu


def run_variant(path: str, confirm: bool = True) -> bool:
    'Runs a variant. path is the import path of the variant relative to variants. confirm controls whether to display the standard "variant infobox". If the infobox is displayed, and the user cancels, returns False. Any unhandled exceptions within the variant\'s code are propogated. Otherwise, returns True.'
    if not isinstance(path, str):
        raise TypeError("path must be of type str (not " + type(path).__name__ + ")")
    elif not isinstance(confirm, bool):
        raise TypeError(
            "confirm must be of type bool (not " + type(confirm).__name__ + ")"
        )
    variant_module: module = import_module("variants." + path)
    if confirm:
        raise NotImplementedError("variant infobox not yet created")
    else:
        variant_module.main()
        return True


clear_screen: partial = partial(system, "cls" if os_name == "nt" else "clear")
del os_name
BACK_OPTION: Final[MenuOption] = MenuOption("BACK", raise_stop_menu)
QUIT_VARIANT_OPTION: Final[MenuOption] = MenuOption(
    "RETURN TO VARIANT MENU", raise_break_menu
)
RESUME_OPTION: Final[MenuOption] = MenuOption("RESUME", raise_stop_menu)
