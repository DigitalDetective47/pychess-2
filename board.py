from enum import Enum, Flag
from enum import auto as enum_gen
from typing import Any, Final, Optional, Sequence, SupportsIndex

CHESS_FEN: Final[str] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
FULLWIDTH_INVERTED_CHECKERBOARD: Final[str] = "\uFF03\uFF0E\n\uFF0E\uFF03"
FULLWIDTH_STANDARD_CHECKERBOARD: Final[str] = "\uFF0E\uFF03\n\uFF03\uFF0E"
INVERTED_CHECKERBOARD: Final[str] = "#.\n.#"
STANDARD_CHECKERBOARD: Final[str] = ".#\n#."


def widen(value: str) -> str:
    "Replaces all ASCII characters in the string with their fullwidth forms as a new string and returns it."
    return "".join(
        [(chr(ord(i) + 65248) if 33 <= ord(i) < 127 else i) for i in value]
    ).replace(" ", "\u3000")


class Color(Enum):
    NEUTRAL = enum_gen()
    WHITE = enum_gen()
    BLACK = enum_gen()

    def next(self):
        if self == Color.NEUTRAL:
            raise ValueError("Color NEUTRAL has no next color")
        return {Color.WHITE: Color.BLACK, Color.BLACK: Color.WHITE}[self]


class CastlingRights(Flag):
    NONE = 0
    WHITE_KINGSIDE = enum_gen()
    WHITE_QUEENSIDE = enum_gen()
    BLACK_KINGSIDE = enum_gen()
    BLACK_QUEENSIDE = enum_gen()


class Coordinate:
    def __init__(self, position: str | Sequence[SupportsIndex]) -> None:
        if isinstance(position, str):
            if not 2 <= len(position) < 4:
                raise ValueError(
                    "argument position must be of length 2 or 3 (not "
                    + str(len(position))
                    + ")"
                )
            elif not 97 <= ord(position[0]) < 123:
                raise ValueError(
                    "argument position must begin with a lowercase letter (not "
                    + position[0]
                    + ")"
                )
            elif not 1 <= int(position[1:]) < 27:
                raise ValueError(
                    "argument position must end with an integer between 1 and 26 (not "
                    + position[1:]
                    + ")"
                )
            pos_value: tuple[int, int] = (ord(position[0]) - 97, int(position[1:]) - 1)
        elif isinstance(position, Sequence):
            if len(position) != 2:
                raise ValueError(
                    "argument position must be of length 2 (not "
                    + str(len(position))
                    + ")"
                )
            elif not isinstance(position[0], SupportsIndex):
                raise TypeError(
                    "file index must be of an index type (not "
                    + type(position[0]).__name__
                    + ")"
                )
            elif not isinstance(position[1], SupportsIndex):
                raise TypeError(
                    "row index must be of an index type (not "
                    + type(position[0]).__name__
                    + ")"
                )
            pos_value: tuple[int, int] = (
                position[0].__index__(),
                position[1].__index__(),
            )
            if not 0 <= pos_value[0] < 26:
                raise IndexError(
                    "file index must be between 0 and 25 (not "
                    + str(pos_value[0])
                    + ")"
                )
            elif not 0 <= pos_value[1] < 26:
                raise IndexError(
                    "rank index must be between 0 and 25 (not "
                    + str(pos_value[1])
                    + ")"
                )
        else:
            raise TypeError(
                "argument position must be of type str or Sequence (not "
                + type(position).__name__
                + ")"
            )
        self.file: Final[int] = pos_value[0]
        self.pos: Final[tuple[int, int]] = pos_value
        self.rank: Final[int] = pos_value[1]

    def __add__(self, other):
        if (
            isinstance(other, Sequence)
            and len(other) == 2
            and isinstance(other[0], SupportsIndex)
            and -25 <= other[0].__index__() < 26
            and isinstance(other[1], SupportsIndex)
            and -25 <= other[1].__index__() < 26
        ):
            coords: tuple[int, int] = (
                self.pos[0] + other[0].__index__(),
                self.pos[1] + other[1].__index__(),
            )
            if 0 <= coords[0] < 26 and 0 <= coords[1] < 26:
                return Coordinate(coords)
            raise IndexError("coordinate offset out of bounds")
        return NotImplemented

    def __bytes__(self) -> bytes:
        return bytes(str(self))

    def __eq__(self, other) -> bool:
        return (
            hash(self) == hash(other)
            if isinstance(other, Coordinate)
            else NotImplemented
        )

    def __hash__(self) -> int:
        return self.pos[0] + (self.pos[1] << 5)

    def __repr__(self) -> str:
        return "Coordinate('" + str(self) + "')"

    def __str__(self) -> str:
        return chr(self.pos[0] + 97) + str(self.pos[1] + 1)


class Board:
    def __init__(self, fen: str, piece_table: dict[str, type], **ex_attributes) -> None:
        if not isinstance(fen, str):
            raise TypeError(
                "fen must be of type string (not " + type(fen).__name__ + ")"
            )
        if not isinstance(piece_table, dict):
            raise TypeError(
                "piece_table must be of type dict (not "
                + type(piece_table).__name__
                + ")"
            )
        for symbol in piece_table:
            if not isinstance(symbol, str):
                raise TypeError(
                    "piece_table must have keys of type str (not "
                    + type(symbol).__name__
                    + ")"
                )
            elif len(symbol) != 1:
                raise ValueError(
                    "piece_table must have keys of length 1 (not "
                    + str(len(symbol))
                    + ")"
                )
        fen_components: Final[list[str]] = fen.split(" ")
        if len(fen_components) != 6:
            raise ValueError("fen parameter is not valid fen")
        rank_data: Final[list[str]] = fen_components[0].split("/")[::-1]
        self.ranks: Final[int] = len(rank_data)
        if self.ranks > 26:
            raise ValueError("board cannot have more than 26 ranks")
        num_files: int = -1
        digit_buffer: str = ""
        file: int
        self.piece_array: dict[Coordinate, pieces.Piece] = {}
        for rank in range(self.ranks):
            file = 0
            for char in rank_data[rank]:
                if char.isdigit():
                    digit_buffer += char
                else:
                    if digit_buffer:
                        file += int(digit_buffer)
                        digit_buffer = ""
                    pos: Coordinate = Coordinate((file, rank))
                    self.piece_array[pos] = piece_table[char.upper()](
                        pos,
                        Color.BLACK
                        if char.islower()
                        else (Color.WHITE if char.isupper() else Color.NEUTRAL),
                        self,
                    )
                    file += 1
            if digit_buffer:
                file += int(digit_buffer)
                digit_buffer = ""
            if file != num_files:
                if num_files == -1:
                    num_files = file
                else:
                    raise ValueError("board cannot have non-square shape")
        if num_files > 25:
            raise ValueError("board cannot have more than 26 files")
        self.files: Final[int] = num_files
        assert all(
            [pos == piece.pos for pos, piece in self.piece_array.items()]
        ), "position desync detected"
        assert not any(
            [
                (pos.rank >= self.ranks or pos.file >= self.files)
                for pos in self.piece_array
            ]
        ), "piece exists outside of board edge"
        match fen_components[1]:
            case "w":
                self.turn: Color = Color.WHITE
            case "b":
                self.turn: Color = Color.BLACK
            case _:
                raise ValueError("current turn must be either 'w' or 'b'")
        self.first_player: Final[Color] = self.turn
        self.castling_rights: CastlingRights = CastlingRights.NONE
        if "K" in fen_components[2]:
            self.castling_rights |= CastlingRights.WHITE_KINGSIDE
        if "Q" in fen_components[2]:
            self.castling_rights |= CastlingRights.WHITE_QUEENSIDE
        if "k" in fen_components[2]:
            self.castling_rights |= CastlingRights.BLACK_KINGSIDE
        if "q" in fen_components[2]:
            self.castling_rights |= CastlingRights.BLACK_QUEENSIDE
        self.en_passant: Optional[Coordinate] = (
            None if fen_components[3] == "-" else Coordinate(fen_components[3])
        )
        self.halfmove_clock: int = int(fen_components[4])
        self.fullmove_clock: int = int(fen_components[5])
        self.ex_attributes: dict[str, Any] = ex_attributes

    def render(
        self,
        piece_symbols: dict[type, dict[Color, str]],
        checker_pattern: str,
        perspective: Color,
        fullwidth: bool = False,
    ) -> str:
        "Returns a string representation of the board meant to be printed to the terminal."
        if not isinstance(piece_symbols, dict):
            raise TypeError(
                "piece_symbols must be of type dict (not "
                + type(piece_symbols).__name__
                + ")"
            )
        for piece_type in piece_symbols.values():
            if not isinstance(piece_type, dict):
                raise TypeError(
                    "piece_symbols must have dict values (not "
                    + type(piece_type).__name__
                    + ")"
                )
            for color, symbol in piece_type.items():
                if not isinstance(color, Color):
                    raise TypeError(
                        "keys of piece_symbols values must be of type Color (not "
                        + type(color).__name__
                        + ")"
                    )
                if not isinstance(symbol, str):
                    raise TypeError(
                        "values of piece_symbols values must be of type str (not "
                        + type(symbol).__name__
                        + ")"
                    )
        if not isinstance(checker_pattern, str):
            raise TypeError(
                "checker_pattern must be of type str (not "
                + type(checker_pattern).__name__
                + ")"
            )
        elif not isinstance(perspective, Color):
            raise TypeError(
                "perspective must be of type Color (not "
                + type(perspective).__name__
                + ")"
            )
        elif not isinstance(fullwidth, bool):
            raise TypeError(
                "fullwidth must be of type bool (not " + type(fullwidth).__name__ + ")"
            )
        elif perspective not in {Color.WHITE, Color.BLACK}:
            raise ValueError(
                "perspective must be either Color.WHITE or Color.BLACK (not "
                + str(perspective)
                + ")"
            )
        elif checker_pattern.replace("\n", "") == "":
            raise ValueError("checker_pattern must constain non-newline characters.")
        checker_list: Final[list[str]] = checker_pattern.splitlines()[::-1]
        rank_label_length: Final[int] = (self.ranks >= 10) + 1
        file_label_offset: Final[str] = ("\u3000" if fullwidth else " ") * (
            rank_label_length + 1
        )
        perspective_ordering: Final[slice] = slice(
            None, None, -1 if perspective == Color.BLACK else 1
        )
        file_labels: Final[str] = (
            "\uFF41\uFF42\uFF43\uFF44\uFF45\uFF46\uFF47\uFF48\uFF49\uFF4A\uFF4B\uFF4C\uFF4D\uFF4E\uFF4F\uFF50\uFF51\uFF52\uFF53\uFF54\uFF55\uFF56\uFF57\uFF58\uFF59\uFF5A"
            if fullwidth
            else "abcdefghijklmnopqrstuvwxyz"
        )[: self.files][perspective_ordering]
        board_str: str = (
            file_label_offset
            + file_labels
            + "\n"
            + file_label_offset
            + ("\uFF0D" if fullwidth else "-") * self.files
            + "\n"
        )
        checker_rank: int
        current_piece: pieces.Piece
        current_rank_label: str
        for rank in range(self.ranks)[perspective_ordering][::-1]:
            current_rank_label = str(rank + 1).rjust(rank_label_length) + "|"
            if fullwidth:
                current_rank_label = widen(current_rank_label)
            board_str += current_rank_label
            for file in range(self.files)[perspective_ordering]:
                try:
                    current_piece = self.piece_array[Coordinate((file, rank))]
                except KeyError:
                    checker_rank = rank % len(checker_list)
                    board_str += checker_list[checker_rank][file % len(checker_list[checker_rank])]
                else:
                    board_str += piece_symbols[type(current_piece)][current_piece.color]
            current_rank_label = "|" + str(rank + 1)
            if fullwidth:
                current_rank_label = widen(current_rank_label)
            board_str += current_rank_label + "\n"
        board_str += (
            file_label_offset
            + ("\uFF0D" if fullwidth else "-") * self.files
            + "\n"
            + file_label_offset
            + file_labels
        )
        return board_str


import pieces

STANDARD_PIECE_TABLE: Final[dict[str, type]] = {
    "A": pieces.Amazon,
    "B": pieces.Bishop,
    "C": pieces.Princess,
    "K": pieces.King,
    "N": pieces.Knight,
    "M": pieces.Empress,
    "P": pieces.Pawn,
    "Q": pieces.Queen,
    "R": pieces.Rook,
    "S": pieces.Nightrider,
    "-": pieces.Piece,
}
STANDARD_PIECE_SYMBOLS: Final[dict[type, dict[Color, str]]] = {
    pieces.Amazon: {Color.WHITE: "A", Color.BLACK: "a"},
    pieces.Bishop: {Color.WHITE: "B", Color.BLACK: "b"},
    pieces.Empress: {Color.WHITE: "M", Color.BLACK: "m"},
    pieces.King: {Color.WHITE: "K", Color.BLACK: "k"},
    pieces.Knight: {Color.WHITE: "N", Color.BLACK: "n"},
    pieces.Nightrider: {Color.WHITE: "S", Color.BLACK: "s"},
    pieces.Pawn: {Color.WHITE: "P", Color.BLACK: "p"},
    pieces.Piece: {Color.NEUTRAL: " "},
    pieces.Princess: {Color.WHITE: "C", Color.BLACK: "c"},
    pieces.Queen: {Color.WHITE: "Q", Color.BLACK: "q"},
    pieces.Rook: {Color.WHITE: "R", Color.BLACK: "r"},
}
