from typing import Callable, Final, Optional

from lib import pieces, board, menu, settings


def main() -> None:
    def add_file_left() -> None:
        game_board.files += 1
        for piece in sorted(
            game_board.values(), key=lambda x: x.pos.file, reverse=True
        ):
            game_board[piece.pos].move(piece.pos + (1, 0))

    def add_file_right() -> None:
        game_board.files += 1

    def add_rank_down() -> None:
        game_board.ranks += 1
        for piece in sorted(
            game_board.values(), key=lambda x: x.pos.rank, reverse=True
        ):
            game_board[piece.pos].move(piece.pos + (0, 1))

    def add_rank_up() -> None:
        game_board.ranks += 1

    def flip_board() -> None:
        nonlocal perspective
        perspective = perspective.next()

    def remove_file_left() -> None:
        for piece in sorted(game_board.values(), key=lambda x: x.pos.file):
            if piece.pos.file == 0:
                del game_board[piece.pos]
            else:
                game_board[piece.pos].move(piece.pos + (-1, 0))
        game_board.files -= 1

    def remove_file_right() -> None:
        for piece in game_board.values():
            if piece.pos.file == game_board.files:
                del game_board[piece.pos]
        game_board.files -= 1

    def remove_rank_down() -> None:
        for piece in sorted(game_board.values(), key=lambda x: x.pos.rank):
            if piece.pos.rank == 0:
                del game_board[piece.pos]
            else:
                game_board[piece.pos].move(piece.pos + (0, -1))
        game_board.ranks -= 1

    def remove_rank_up() -> None:
        for piece in game_board.values():
            if piece.pos.rank == game_board.ranks:
                del game_board[piece.pos]
        game_board.ranks -= 1

    ADD_FILE_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "+<": menu.MenuOption("ADD FILE TO LEFT", add_file_left),
        "+>": menu.MenuOption("ADD FILE TO RIGHT", add_file_right),
    }
    ADD_RANK_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "+^": menu.MenuOption("ADD RANK TO TOP", add_rank_up),
        "+v": menu.MenuOption("ADD RANK TO BOTTOM", add_rank_down),
    }
    GAME_MENU_TRAILING_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "X": menu.MenuOption("RETURN TO MAIN MENU", menu.raise_break_menu)
    }
    GAME_MENU_LEADING_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "R": menu.RESUME_OPTION,
        "F": menu.MenuOption("FLIP BOARD", flip_board),
    }
    REMOVE_FILE_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "-<": menu.MenuOption("REMOVE FILE FROM LEFT", remove_file_left),
        "->": menu.MenuOption("REMOVE FILE FROM RIGHT", remove_file_right),
    }
    REMOVE_RANK_ENTRIES: Final[dict[str, menu.MenuOption]] = {
        "-^": menu.MenuOption("REMOVE RANK FROM TOP", remove_rank_up),
        "-v": menu.MenuOption("REMOVE RANK FROM BOTTOM", remove_rank_down),
    }

    drop_location: board.Coordinate
    first_coordinate_length: int
    game_board: board.Board = board.Board(
        "--------/--------/8/8/8/8/--------/-------- w - - 0 1",
        pieces.STANDARD_PIECE_TABLE,
        archive_mode=board.BoardArchiveMode.NONE,
    )
    game_board[board.Coordinate("a1")].symbol = "R"
    game_board[board.Coordinate("b1")].symbol = "N"
    game_board[board.Coordinate("c1")].symbol = "B"
    game_board[board.Coordinate("d1")].symbol = "Q"
    game_board[board.Coordinate("e1")].symbol = "K"
    game_board[board.Coordinate("f1")].symbol = "B"
    game_board[board.Coordinate("g1")].symbol = "N"
    game_board[board.Coordinate("h1")].symbol = "R"
    game_board[board.Coordinate("a2")].symbol = "P"
    game_board[board.Coordinate("b2")].symbol = "P"
    game_board[board.Coordinate("c2")].symbol = "P"
    game_board[board.Coordinate("d2")].symbol = "P"
    game_board[board.Coordinate("e2")].symbol = "P"
    game_board[board.Coordinate("f2")].symbol = "P"
    game_board[board.Coordinate("g2")].symbol = "P"
    game_board[board.Coordinate("h2")].symbol = "P"
    game_board[board.Coordinate("a7")].symbol = "p"
    game_board[board.Coordinate("b7")].symbol = "p"
    game_board[board.Coordinate("c7")].symbol = "p"
    game_board[board.Coordinate("d7")].symbol = "p"
    game_board[board.Coordinate("e7")].symbol = "p"
    game_board[board.Coordinate("f7")].symbol = "p"
    game_board[board.Coordinate("g7")].symbol = "p"
    game_board[board.Coordinate("h7")].symbol = "p"
    game_board[board.Coordinate("a8")].symbol = "r"
    game_board[board.Coordinate("b8")].symbol = "n"
    game_board[board.Coordinate("c8")].symbol = "b"
    game_board[board.Coordinate("d8")].symbol = "q"
    game_board[board.Coordinate("e8")].symbol = "k"
    game_board[board.Coordinate("f8")].symbol = "b"
    game_board[board.Coordinate("g8")].symbol = "n"
    game_board[board.Coordinate("h8")].symbol = "r"
    input_error_prompt: str = ""
    move: str
    perspective: pieces.Color = pieces.Color.WHITE
    try:
        while True:
            if input_error_prompt == "":
                checker_list: Final[list[str]] = (
                    board.INVERTED_CHECKERBOARD
                    if settings.user_settings[None]["dark_mode"]
                    else board.STANDARD_CHECKERBOARD
                ).splitlines()[::-1]
                rank_label_length: Final[int] = (game_board.ranks >= 10) + 1
                file_label_offset: Final[str] = " " * (rank_label_length + 1)
                perspective_ordering: Final[slice] = slice(
                    None, None, -1 if perspective == pieces.Color.BLACK else None
                )
                file_labels: Final[str] = "abcdefghijklmnopqrstuvwxyz"[
                    : game_board.files
                ][perspective_ordering]
                board_str: str = (
                    file_label_offset
                    + file_labels
                    + "\n"
                    + file_label_offset
                    + "-" * game_board.files
                    + "\n"
                )
                checker_rank: int
                for rank in range(game_board.ranks)[perspective_ordering][::-1]:
                    board_str += str(rank + 1).rjust(rank_label_length) + "|"
                    for file in range(game_board.files)[perspective_ordering]:
                        try:
                            current_piece = game_board[board.Coordinate((file, rank))]
                        except KeyError:
                            checker_rank = rank % len(checker_list)
                            board_str += checker_list[checker_rank][
                                file % len(checker_list[checker_rank])
                            ]
                        else:
                            board_str += current_piece.symbol
                    board_str += "|" + str(rank + 1) + "\n"
                menu.clear_screen()
                print(
                    board_str
                    + file_label_offset
                    + "-" * game_board.files
                    + "\n"
                    + file_label_offset
                    + file_labels
                    + "\n"
                )
            move = input(input_error_prompt)
            if move == "menu":
                menu.DynamicMenu(
                    compile("'IN-GAME MENU'", __file__, "eval"),
                    compile(
                        "GAME_MENU_LEADING_ENTRIES | ({} if game_board.files == 26 else ADD_FILE_ENTRIES) | ({} if game_board.ranks == 26 else ADD_RANK_ENTRIES) | ({} if game_board.files == 1 else REMOVE_FILE_ENTRIES) | ({} if game_board.ranks == 1 else REMOVE_RANK_ENTRIES) | GAME_MENU_TRAILING_ENTRIES",
                        __file__,
                        "eval",
                    ),
                    globals(),
                    locals(),
                )()
                input_error_prompt = ""
            elif len(move) < 3:
                input_error_prompt = "Malformed move input. Please re-type your move.\n"
            elif move[1] == "@":
                try:
                    drop_location = board.Coordinate(move[2:])
                    game_board[drop_location] = pieces.Piece(
                        drop_location, pieces.Color.NEUTRAL, game_board
                    )
                    game_board[drop_location].symbol = move[0]
                except (IndexError, ValueError):
                    input_error_prompt = (
                        "Invalid or unreadable coordinate. Please re-type your move.\n"
                    )
            elif move.startswith("*"):
                try:
                    del game_board[board.Coordinate(move[1:])]
                except ValueError:
                    input_error_prompt = (
                        "Invalid or unreadable coordinate. Please re-type your move.\n"
                    )
                except KeyError:
                    input_error_prompt = "The space you entered is already empty. Please re-type your move.\n"
                else:
                    input_error_prompt = ""
            else:
                try:
                    first_coordinate_length = 2 + move[2].isdigit()
                    game_board[board.Coordinate(move[:first_coordinate_length])].move(
                        board.Coordinate(move[first_coordinate_length:])
                    )
                except (IndexError, ValueError):
                    input_error_prompt = (
                        "Invalid or unreadable coordinate. Please re-type your move.\n"
                    )
                except KeyError:
                    input_error_prompt = "The origin space you entered is empty. Please re-type your move.\n"
                else:
                    input_error_prompt = ""
    except menu.BreakMenu:
        pass


DEFAULT_VARIANT_SETTINGS: Final = {}
DESCRIPTION: Final[
    str
] = "A board with no rules. The board can be resized, and pieces can be placed and removed at will."
INVENTOR: Final[Optional[str]] = None
LONG_NAME: Final[str] = "Sandbox Mode"
PROGRAMMER: Final[str] = "DigitalDetective47"
SETTINGS_MENU: Final[Optional[Callable]] = None
SHORT_NAME: str = "SANDBOX"
UUID: Final[
    bytes
] = b"W\x7F\xC4\x83j\xBD_\xB5\xFA\x1F\xD5\x16'\x19\xAC\x00\xDE\xFC].8\x99O\xC7\xC2\xC9\xC4v\xF8>\xE76"
