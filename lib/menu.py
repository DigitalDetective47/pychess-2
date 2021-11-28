"""Menu data for PyChess 2.

Exceptions:
MenuExit -- Base class for menu-closing exceptions.
StopMenu -- Close the current menu.
BreakMenu -- Close the current menu and re-raise this exception.

Classes:
MenuOption -- An option in a menu.
StaticMenu -- A simple menu with (relatively) static contents.
DynamicMenu -- A menu with contents evaluated each time the menu is displayed.

Functions:
raise_stop_menu -- Raise a StopMenu exception.
raise_break_menu -- Raise a BreakMenu exception.
clear_screen -- Clear the terminal.

Objects:
BACK_OPTION -- The back option present in many menus.
QUIT_VARIANT_OPTION -- The quit variant option present in variant menus.
RESUME_OPTION -- The resume option present in variant menus.
"""

from collections.abc import Callable as CallableABC
from collections.abc import Hashable as HashableABC
from collections.abc import Mapping as MappingABC
from collections.abc import MutableMapping as MutableMappingABC
from copy import copy as shallow_copy
from functools import partial
from os import name as os_name
from os import system
from types import CodeType as code
from typing import Any, Callable, Final, Iterator, Mapping, NoReturn


class MenuExit(BaseException):
    """Base class for menu-closing exceptions."""


class StopMenu(MenuExit):
    """Close the current menu."""


class BreakMenu(MenuExit):
    """Close the current menu and re-raise this exception."""


class MenuOption(CallableABC, HashableABC, MappingABC):
    """An option in a menu.

    Instance methods:
    __call__
    __getitem__
    __hash__
    __iter__
    __len__
    __repr__
    __str__

    Usable as:
    Callable -- Performs the action of the menu option.
    Mapping -- Contains a single key-value pair with the name as the key and the action as the item.
    """

    def __init__(self, name: str, action: Callable) -> None:
        """Create a new menu option with the given name and action.

        Required positional arguments:
        name -- The string representing the option when a menu containing it is displayed.
        action -- The object that is called when the option is selected. It is called with no arguments.
        """
        self._name: Final[str] = name
        self._action: Final[Callable] = action

    def __call__(self, *args, **kwargs) -> Any:
        """Perform the action of this menu option."""
        return self._action(*args, **kwargs)

    def __getitem__(self, key: str, /) -> Callable:
        if key == str(self):
            return self._action
        else:
            raise KeyError(key)

    def __hash__(self) -> int:
        return hash((str(self), self._action))

    def __iter__(self) -> Iterator[str]:
        return iter({str(self): self._action})

    def __len__(self) -> int:
        return 1

    def __repr__(self) -> str:
        return f"MenuOption({str(self)!r}, {self._action!r})"

    def __str__(self) -> str:
        """Return the name of this menu option."""
        return self._name


class StaticMenu(CallableABC, MutableMappingABC):
    """A simple menu with (relatively) static contents.

    Instance methods:
    __call__
    __delitem__
    __getitem__
    __iter__
    __len__
    __repr__
    __str__

    Usable as:
    Callable -- Displays the menu.
    Mutable Mapping -- Contains the menu's options. Keys are the identifers of the options, and values are the options themselves.
    """

    def __init__(self, title: str, options: Mapping[str, MenuOption]) -> None:
        """Create a new static menu with the given title and contents.

        Required positional arguments:
        title -- The title of the menu.
        options -- A mapping containing the menu's options. Each key is the option's "identifier", displayed left of the vertical bar, and which must be typed by the user to select the option, and its corresponding value is the option that it points to.
        """
        self._options: Final[dict[str, MenuOption]] = shallow_copy(options)
        menu_option_width: Final[int] = max([len(index) for index in options.keys()])
        title_offset: Final[str] = " " * (menu_option_width + 1)
        appearance: str = f"{title_offset}{title}\n{title_offset}{'-' * len(title)}"
        for index, option in options.items():
            appearance += f"\n{index.rjust(menu_option_width)}|{option}"
        self._appearance: Final[str] = appearance

    def __call__(self) -> None:
        """Repeatedly display this menu and prompt the user to select an option until a StopMenu is raised."""
        try:
            while True:
                clear_screen()
                print(f"{self}\n")
                selected_option: MenuOption
                options: dict[str, MenuOption] = dict(self)
                try:
                    selected_option = options[input()]
                except KeyError:
                    while True:
                        try:
                            selected_option = options[
                                input("Select a menu item listed.\n")
                            ]
                        except KeyError:
                            pass
                        else:
                            break
                selected_option()
        except StopMenu:
            pass

    def __delitem__(self, key: str, /) -> None:
        try:
            line_number: int = tuple(self._options).index(key) + 2
        except ValueError:
            raise KeyError(key)
        del self._options[key]
        appearance_lines: str = str(self).splitlines()
        self._appearance = "\n".join(
            appearance_lines[:line_number] + appearance_lines[line_number + 1 :]
        )

    def __getitem__(self, key: str, /) -> MenuOption:
        return self._options[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._options)

    def __len__(self) -> int:
        return len(self._options)

    def __repr__(self) -> str:
        display_lines: Final[list[str]] = str(self).splitlines()
        return f"StaticMenu({display_lines[0][display_lines[1].count(' ') :]!r}, {self._options!r})"

    def __setitem__(self, key: str, value: MenuOption) -> None:
        if key in self._options:
            self._options[key] = value
            line_number: int = tuple(self._options).index(key) + 2
            appearance_lines: str = str(self).splitlines()
            self._appearance = "\n".join(
                appearance_lines[:line_number]
                + [f"{key.rjust(appearance_lines[1].count(' '))}|{value}"]
                + appearance_lines[line_number + 1 :]
            )
        else:
            self._options[key]
            self._appearance += (
                f"\n{key.rjust(str(self).splitlines()[1].count(' '))}|{value}"
            )

    def __str__(self) -> str:
        """Return what this menu would look like when displayed."""
        return self._appearance


class DynamicMenu(CallableABC):
    """A menu with contents evaluated each time the menu is displayed.

    Instance methods:
    __call__
    generate_static
    __repr__

    Instance attributes:
    globals
    locals
    options_expression
    title_expression

    Usable as:
    Callable -- Displays the menu.
    """

    def __init__(
        self,
        title_expression: code | str,
        options_expression: code | str,
        global_context: dict[str, Any],
        local_context: dict[str, Any],
    ) -> None:
        """Create a dynamic menu with the given title and options expression in the context of the given globals and locals.

        Required positional arguments:
        title_expression -- An expression that returns the menu's title when passed into eval.
        options_expression -- An expression that returns the menu's contents when passed into eval.
        global_context -- The globals of the menu's scope. Should be globals() in most circumstances.
        local_context -- The locals of the menu's scope. Should be locals() in most circumstances.
        """
        self.title_expression: code | str = title_expression
        """An expression that returns this menu's title when passed into eval"""
        self.options_expression: code | str = options_expression
        """An expression that returns this menu's contents when passed into eval"""
        self.globals: dict[str, Any] = global_context
        """The globals of this menu's scope."""
        self.locals: dict[str, Any] = local_context
        """The locals of this menu's scope."""

    def __call__(self) -> None:
        """Repeatedly display this menu and prompt the user to select an option until a StopMenu is raised."""
        try:
            while True:
                title: str = eval(self.title_expression, self.globals, self.locals)
                options: Mapping[str, MenuOption] = eval(
                    self.options_expression, self.globals, self.locals
                )
                menu_option_width: Final[int] = max(
                    [len(index) for index in options.keys()]
                )
                title_offset: Final[str] = " " * (menu_option_width + 1)
                appearance: str = (
                    f"{title_offset}{title}\n{title_offset}{'-' * len(title)}"
                )
                for index, option in options.items():
                    appearance += f"\n{index.rjust(menu_option_width)}|{option}"
                clear_screen()
                print(f"{appearance}\n")
                selected_option: MenuOption
                try:
                    selected_option = options[input()]
                except KeyError:
                    while True:
                        try:
                            selected_option = options[
                                input("Select a menu item listed.\n")
                            ]
                        except KeyError:
                            pass
                        else:
                            break
                selected_option()
        except StopMenu:
            pass

    def generate_static(self) -> StaticMenu:
        """Return a static menu with the current contents of this menu."""
        return StaticMenu(
            eval(self.title_expression, self.globals, self.locals),
            eval(self.options_expression, self.globals, self.locals),
        )

    def __repr__(self) -> str:
        return f"DynamicMenu({self.title_expression!r}, {self.options_expression!r})"


def raise_stop_menu() -> NoReturn:
    """Raise a StopMenu exception."""
    raise StopMenu


def raise_break_menu() -> NoReturn:
    """Raise a BreakMenu exception."""
    raise BreakMenu


clear_screen: Final[Callable[[], None]] = partial(
    system, "cls" if os_name == "nt" else "clear"
)
"""Clear the terminal."""

BACK_OPTION: Final[MenuOption] = MenuOption("BACK", raise_stop_menu)
"""The back option present in many menus."""
QUIT_VARIANT_OPTION: Final[MenuOption] = MenuOption(
    "RETURN TO VARIANT MENU", raise_break_menu
)
"""The quit variant option present in variant menus."""
RESUME_OPTION: Final[MenuOption] = MenuOption("RESUME", raise_stop_menu)
"""The resume option present in variant menus."""
