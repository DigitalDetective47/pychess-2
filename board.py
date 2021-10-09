from enum import Enum, Flag
from enum import auto as enum_gen
from typing import Any, Final, Optional, Sequence, SupportsIndex


class Color(Enum):
    "A player color."
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
    "A location on a board."

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
            pos_value: tuple[int, int] = (
                ord(position[0]) - 97, int(position[1:]) - 1)
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
                position[0].__index__(), position[1].__index__())
            if not 0 <= pos_value[0] < 26:
                raise IndexError(
                    "file index must be between 0 and 25 (not " + str(pos_value[0]) + ")")
            elif not 0 <= pos_value[1] < 26:
                raise IndexError(
                    "rank index must be between 0 and 25 (not " + str(pos_value[1]) + ")")
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
    default_piece_table: dict[str, type] = {}

    def __init__(
        self,
        fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        piece_table: dict[str, type] = default_piece_table,
        **ex_attributes
    ) -> None:
        if not isinstance(fen, str):
            raise TypeError(
                "fen must be of type string (not " + type(fen).__name__ + ")"
            )
        fen_components: Final[list[str]] = fen.split(" ")
        if len(fen_components) != 6:
            raise ValueError("fen parameter is not valid fen")
        rank_data: Final[list[str]] = fen_components[0].split("/")
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
                        pos, Color.BLACK if char.islower() else Color.WHITE, self)
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
        assert all([pos == piece.pos for pos,
                   piece in self.piece_array.items()])
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


import pieces  # nopep8

Board.default_piece_table.update({"A": pieces.Amazon, "B": pieces.Bishop, "C": pieces.Princess, "K": pieces.King,
                                 "M": pieces.Empress, "N": pieces.Knight, "P": pieces.Pawn, "Q": pieces.Queen, "R": pieces.Rook, "S": pieces.Nightrider, "-": pieces.Piece})
del Board.default_piece_table
