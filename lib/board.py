"""Board data for PyChess 2.

Classes:
BoardArchiveMode -- A set of conditions for storing archives in board objects.
CastlingRights -- A player's right to castle in a certian direction.
Coordinate -- A location on a board.
Board -- A chess board.
BoardArchive -- An archive for a board.

Functions:
widen -- Return a string with all ASCII characters in an input string converted to their fullwidth forms.

Objects:
CHESS_FEN -- The starting FEN for standard chess.
FULLWIDTH_INVERTED_CHECKERBOARD -- An inverted checkerboard pattern of fullwidth characters.
FULLWIDTH_STANDARD_CHECKERBOARD -- A standard checkerboard made of fullwidth characters.
INVERTED_CHECKERBOARD -- An inverted checkerboard pattern.
NO_CASTLING_FEN -- The starting FEN for chess, but without castling rights.
STANDARD_CHECKERBOARD -- A standard checkerboard pattern.
"""

from __future__ import annotations

from collections.abc import Hashable as HashableABC
from collections.abc import MutableMapping as MutableMappingABC
from collections.abc import Sequence as SequenceABC
from copy import copy as shallow_copy
from enum import Enum, Flag
from enum import auto as enum_gen
from enum import unique
from typing import Final, Iterator, Mapping, Optional, Sequence, SupportsIndex

from lib import pieces


def widen(value: str) -> str:
    """Return a string with all ASCII characters in an input string converted to their fullwidth forms.

    Required positional arguments:
    value -- The string to be widened.
    """
    return "".join(
        [(chr(ord(i) + 65248) if 33 <= ord(i) < 127 else i) for i in value]
    ).replace(" ", "\u3000")


@unique
class BoardArchiveMode(Enum):
    """A set of conditions for storing archives in board objects.

    Enumeration members:
    NONE
    PARTIAL
    FULL
    """

    NONE = enum_gen()
    """Do not store board archives."""
    PARTIAL = enum_gen()
    """Clear archives after each reset of the halfmove counter used for the fifty-move rule."""
    FULL = enum_gen()
    """Keep archives throughout the whole game."""


class CastlingRights(Flag):
    """A player's right to castle in a certian direction.

    Enumeration members:
    NONE
    WHITE_KINGSIDE
    WHITE_QUEENSIDE
    BLACK_KINGSIDE
    BLACK_QUEENSIDE
    """

    NONE = 0
    WHITE_KINGSIDE = enum_gen()
    WHITE_QUEENSIDE = enum_gen()
    BLACK_KINGSIDE = enum_gen()
    BLACK_QUEENSIDE = enum_gen()


class Coordinate(HashableABC, SequenceABC):
    """A location on a board.

    Instance methods:
    __add__
    __complex__
    __eq__
    __getitem__
    __hash__
    __len__
    __repr__
    __str__

    Instance attributes:
    file (Read-only)
    rank (Read-only)

    Usable as:
    Sequence -- Acts as a two-element sequence of file, rank.
    """

    def __init__(
        self,
        position_or_file: str | Sequence[SupportsIndex] | complex | SupportsIndex,
        rank: Optional[SupportsIndex] = None,
        /,
    ) -> None:
        """Create a new coordinate pointing to the given space.

        Required positional arguments:
        position_or_file -- If a string, should specify the space in standard notation. If a sequence, should be a zero-indexed file, rank pair. If a complex number, the real component is used as the file index, and the imaginary component is used as the rank index. If an integer, should be a file index.

        Optional positional arguments:
        rank -- If position_or_file is a file index, should be the rank index. Otherwise, should not be specified.
        """
        pos_value: tuple[int, int]
        if isinstance(position_or_file, str):
            if rank is not None:
                raise TypeError("Coordinate(str) does not take second argument")
            elif not 2 <= len(position_or_file) < 4:
                raise ValueError(
                    f"position_or_file must be of length 2 or 3 (not {len(position_or_file)})"
                )
            elif not 97 <= ord(position_or_file[0]) < 123:
                raise ValueError(
                    f"position_or_file must begin with a lowercase letter (not {position_or_file[0]})"
                )
            elif not 1 <= int(position_or_file[1:]) < 27:
                raise ValueError(
                    f"position_or_file must end with an integer between 1 and 26 (not {position_or_file[1:]})"
                )
            pos_value = (ord(position_or_file[0]) - 97, int(position_or_file[1:]) - 1)
        elif isinstance(position_or_file, Sequence):
            if rank is not None:
                raise TypeError("Coordinate(Sequence) does not take second argument")
            elif len(position_or_file) != 2:
                raise ValueError(
                    f"position_or_file must be of length 2 (not {len(position_or_file)})"
                )
            pos_value = (
                position_or_file[0].__index__(),
                position_or_file[1].__index__(),
            )
        elif isinstance(position_or_file, complex):
            if rank is not None:
                raise TypeError("Coordinate(complex) does not take second argument")
            elif position_or_file.real % 1.0:
                raise ValueError(
                    f"position_or_file must have integer real component (not {position_or_file.real})"
                )
            elif position_or_file.imag % 1.0:
                raise ValueError(
                    f"position_or_file must have integer imaginary component (not {position_or_file.real})"
                )
            pos_value = (int(position_or_file.real), int(position_or_file.imag))
        elif isinstance(position_or_file, SupportsIndex):
            if rank is None:
                raise TypeError(
                    "Coordinate(SupportsIndex, SupportsIndex) requires second argument"
                )
            pos_value = (position_or_file.__index__(), rank.__index__())
        else:
            raise TypeError(
                f"position_or_file must be of type str | Sequence | complex | SupportsIndex (not {type(position_or_file).__name__})"
            )
        if not 0 <= pos_value[0] < 26:
            raise IndexError(
                f"file index must be between 0 and 25 (not {pos_value[0]})"
            )
        elif not 0 <= pos_value[1] < 26:
            raise IndexError(
                f"rank index must be between 0 and 25 (not {pos_value[1]})"
            )
        self._location: Final[tuple[int, int]] = pos_value

    def __add__(self, other: Sequence[SupportsIndex], /) -> Coordinate:
        """Offset this coordinate by the sequence's values, and return the shifted coordinate"""
        if (
            isinstance(other, Sequence)
            and len(other) == 2
            and isinstance(other[0], SupportsIndex)
            and isinstance(other[1], SupportsIndex)
        ):
            return Coordinate(
                self.file + other[0].__index__(), self.rank + other[1].__index__()
            )
        return NotImplemented

    def __complex__(self) -> complex:
        return complex(*self)

    def __eq__(self, other: Coordinate, /) -> bool:
        return (
            self.file == other.file and self.rank == other.rank
            if isinstance(other, Coordinate)
            else NotImplemented
        )

    @property
    def file(self) -> int:
        """The file index of this coordinate."""
        return self[0]

    def __getitem__(self, key: int, /) -> int:
        return self._location[key]

    def __hash__(self) -> int:
        return self.file + (self.rank << 5)

    def __len__(self) -> int:
        return 2

    @property
    def rank(self) -> int:
        """The rank index of this coordinate."""
        return self[1]

    def __repr__(self) -> str:
        return f"Coordinate({str(self)!r})"

    def __str__(self) -> str:
        return chr(self.file + 97) + str(self.rank + 1)


class Board(MutableMappingABC):
    """A chess board.

    Instance methods:
    __delitem__
    __eq__
    increment_halfmove
    __iter__
    __getitem__
    __len__
    render
    reset_halfmove
    __setitem__

    Instance atributes:
    archive_mode
    archives
    castling_rights
    files (Read-only)
    pawn_ranks (Read-only)
    ranks (Read-only)
    turn

    Usable as:
    Mutable Mapping -- Contains the pieces on the board. Coordinates are keys, and pieces are values.
    """

    def __init__(
        self,
        fen: str,
        piece_table: Mapping[str, type],
        *,
        archive_mode: BoardArchiveMode = BoardArchiveMode.PARTIAL,
        pawn_ranks: Mapping[pieces.Color, SupportsIndex] = {},
    ) -> None:
        """Create a new board.

        Required positional arguments:
        fen -- The FEN for the initial position.
        piece_table -- A mapping with keys being character in the FEN, and values being the piece class that should be instantiated by it.

        Optional keyword arguments:
        archive_mode -- Conditions for storing position archives.
        pawn_ranks -- A mapping with keys being player colors and values being the rank that pawns can double-move. If empty, auto-fills to the second rank from the edge. If only one is specified, the other is automatically calculated to be the same distance from the edge.
        """
        for symbol in piece_table:
            if len(symbol) != 1:
                raise ValueError(
                    f"piece_table keys must be of length 1 (not {len(symbol)})"
                )
        fen_components: Final[list[str]] = fen.split(" ")
        if len(fen_components) != 6:
            raise ValueError("fen parameter is not valid fen")
        rank_data: Final[list[str]] = fen_components[0].split("/")[::-1]
        self._ranks: Final[int] = len(rank_data)
        for color, rank in pawn_ranks.items():
            if color not in pieces.PLAYER_COLORS:
                raise ValueError(
                    f"pawn_ranks keys must be either Color.WHITE or Color.BLACK (not {color!r})"
                )
            elif 0 <= rank.__index__() < self._ranks:
                raise ValueError("values of pawn_ranks must be within the board")
        if self._ranks > 26:
            raise ValueError("board cannot have more than 26 ranks")
        self.archive_mode: Final[BoardArchiveMode] = archive_mode
        """Conditions for storing position archives."""
        digit_buffer: str = ""
        file: int
        num_files: Optional[int] = None
        self._piece_array: Final[dict[Coordinate, pieces.Piece]] = {}
        for rank in range(self._ranks):
            file = 0
            for char in rank_data[rank]:
                if char.isdigit():
                    digit_buffer += char
                else:
                    if digit_buffer:
                        file += int(digit_buffer)
                        digit_buffer = ""
                    pos: Coordinate = Coordinate(file, rank)
                    self._piece_array[pos] = piece_table[char.upper()](
                        pos,
                        pieces.Color.BLACK
                        if char.islower()
                        else (
                            pieces.Color.WHITE
                            if char.isupper()
                            else pieces.Color.NEUTRAL
                        ),
                        self,
                    )
                    file += 1
            if digit_buffer:
                file += int(digit_buffer)
                digit_buffer = ""
            if file != num_files:
                if num_files is None:
                    num_files = file
                else:
                    raise ValueError("board cannot have non-square shape")
        if num_files > 25:
            raise ValueError("board cannot have more than 26 files")
        self._files: Final[int] = num_files
        assert all(
            [pos == piece.pos for pos, piece in self._piece_array.items()]
        ), "position desync detected"
        assert all(
            [self is piece.board for piece in self._piece_array.values()]
        ), "board reference desync detected"
        assert all(
            [
                (pos.file <= self._files and pos.rank <= self.ranks)
                for pos in self._piece_array
            ]
        ), "piece exists outside of board edge"
        self.turn: pieces.Color
        """The color of the player to move."""
        match fen_components[1]:
            case "w":
                self.turn = pieces.Color.WHITE
            case "b":
                self.turn = pieces.Color.BLACK
            case _:
                raise ValueError("current turn must be either 'w' or 'b'")
        self.first_player: Final[pieces.Color] = self.turn
        """The color who moves first."""
        self.castling_rights: CastlingRights = CastlingRights.NONE
        """The castling rights of the players."""
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
        """The number of half-moves since the last reset."""
        self.fullmove_clock: int = int(fen_components[5])
        """The current turn number."""
        pawn_ranks_mem: Mapping[pieces.Color, int]
        match dict(pawn_ranks):
            case {}:
                pawn_ranks_mem = {pieces.Color.WHITE: 1, pieces.Color.BLACK: self._ranks - 2}
            case {pieces.Color.WHITE: white_pawn_rank}:
                pawn_ranks_mem = pawn_ranks | {pieces.Color.BLACK: self._ranks - 1 - white_pawn_rank}
            case {pieces.Color.BLACK: black_pawn_rank}:
                pawn_ranks_mem = {pieces.Color.WHITE: self._ranks - 1 - black_pawn_rank} | pawn_ranks
            case {pieces.Color.WHITE: _, pieces.Color.BLACK: _}:
                pawn_ranks_mem = dict(pawn_ranks)
            case {pieces.Color.BLACK: black_pawn_rank, pieces.Color.WHITE: white_pawn_rank}:
                pawn_ranks_mem = {pieces.Color.WHITE: white_pawn_rank, pieces.Color.BLACK: black_pawn_rank}
        self._pawn_ranks: Final[dict[pieces.Color, int]] = pawn_ranks_mem
        self.archives: list[BoardArchive] = (
            [] if self.archive_mode is BoardArchiveMode.NONE else [BoardArchive(self)]
        )

    def __delitem__(self, key: Coordinate) -> None:
        del self._piece_array[key]

    def __eq__(self, other: Board) -> bool:
        return (
            dict(self) == dict(other)
            and self.castling_rights == other.castling_rights
            and self.files == other.files
            and self.pawn_ranks == other.pawn_ranks
            and self.ranks == other.ranks
            and self.turn == other.turn
            if isinstance(other, Board)
            else NotImplemented
        )

    @property
    def files(self) -> int:
        """The number of files this board has."""
        return self._files

    def increment_halfmove(self) -> None:
        """Increment the halfmove clock and store a new board archive if necessary."""
        self.halfmove_clock += 1
        if self.archives is not BoardArchiveMode.NONE:
            self.archives.append(BoardArchive(self))

    def __iter__(self) -> Iterator[Coordinate]:
        return iter(self._piece_array)

    def __getitem__(self, key: Coordinate) -> pieces.Piece:
        return self._piece_array[key]

    def __len__(self) -> int:
        return len(self._piece_array)

    @property
    def pawn_ranks(self) -> dict[pieces.Color, int]:
        """The ranks that pawns can double-move on."""
        return self._pawn_ranks

    @property
    def ranks(self) -> int:
        """The number of ranks this board has."""
        return self._ranks

    def render(
        self,
        piece_symbols: Mapping[frozenset[type | pieces.Color], str],
        checker_pattern: str,
        fullwidth: bool = False,
        perspective: pieces.Color = pieces.Color.WHITE,
    ) -> str:
        """Return a string representation of the board with the specified formatting options.

        Required positional arguments:
        piece_symbols -- The strings used to represent pieces. Keys should be a frozenset containing the piece class and color, and values should be the string that they display.
        checker_pattern -- The checkerboard pattern used to fill in empty spaces.

        Optional positional arguments:
        fullwidth -- Whether the board should use fullwidth characters for the edges.
        perspective -- Which player should be displayed at the bottom.
        """
        if perspective not in pieces.PLAYER_COLORS:
            raise ValueError(
                f"perspective must be either pieces.Color.WHITE or pieces.Color.BLACK (not {perspective!r})"
            )
        elif checker_pattern.replace("\n", "") == "":
            raise ValueError("checker_pattern must constain non-newline characters.")
        checker_list: Final[list[str]] = checker_pattern.splitlines()[::-1]
        rank_label_length: Final[int] = (self.ranks >= 10) + 1
        file_label_offset: Final[str] = ("\u3000" if fullwidth else " ") * (
            rank_label_length + 1
        )
        perspective_ordering_temp: slice
        match perspective:
            case pieces.Color.WHITE:
                perspective_ordering_temp = slice(None)
            case pieces.Color.BLACK:
                perspective_ordering_temp = slice(None, None, -1)
        perspective_ordering: Final[slice] = perspective_ordering_temp
        file_labels: Final[str] = (
            "\uFF41\uFF42\uFF43\uFF44\uFF45\uFF46\uFF47\uFF48\uFF49\uFF4A\uFF4B\uFF4C\uFF4D\uFF4E\uFF4F\uFF50\uFF51\uFF52\uFF53\uFF54\uFF55\uFF56\uFF57\uFF58\uFF59\uFF5A"
            if fullwidth
            else "abcdefghijklmnopqrstuvwxyz"
        )[: self.files][perspective_ordering]
        board_top_bottom_border: Final[str] = (
            "\uFF0D" if fullwidth else "-"
        ) * self.files
        board_str: str = f"{file_label_offset}{file_labels}\n{file_label_offset}{board_top_bottom_border}\n"
        checker_rank: int
        current_rank_label: str
        for rank in reversed(range(self.ranks)[perspective_ordering]):
            current_rank_label = f"{str(rank + 1).rjust(rank_label_length)}|"
            if fullwidth:
                current_rank_label = widen(current_rank_label)
            board_str += current_rank_label
            for file in range(self.files)[perspective_ordering]:
                try:
                    current_piece = self[Coordinate(file, rank)]
                except KeyError:
                    checker_rank = rank % len(checker_list)
                    board_str += checker_list[checker_rank][
                        file % len(checker_list[checker_rank])
                    ]
                else:
                    board_str += piece_symbols[frozenset({type(current_piece), current_piece.color})]
            current_rank_label = f"|{rank + 1}"
            if fullwidth:
                current_rank_label = widen(current_rank_label)
            board_str += f"{current_rank_label}\n"
        return f"{board_str}{file_label_offset}{board_top_bottom_border}\n{file_label_offset}{file_labels}"

    def reset_halfmove(self) -> None:
        """Reset the halfmove clock and clear the board archives if necessary."""
        self.halfmove_clock = 0
        if self.archive_mode is BoardArchiveMode.PARTIAL:
            self.archives.clear()
            self.archives.append(BoardArchive(self))

    def __setitem__(self, key: Coordinate, value) -> None:
        if key.file > self.files or key.rank > self.ranks:
            raise IndexError("Board keys must point to spaces within the board")
        self._piece_array[key] = value


class BoardArchive:
    """An archive for a board.

    Instance methods:
    __eq__
    """

    def __init__(self, source: Board) -> None:
        """Create a board archive.

        Required positional arguments:
        source -- The board to create an archive of.
        """
        self._castling_rights: Final[CastlingRights] = source.castling_rights
        self._files: Final[int] = source.files
        self._pawn_ranks: Final[dict[pieces.Color, int]] = source.pawn_ranks
        self._piece_array: Final[dict[Coordinate, pieces.Piece]] = {}
        for location, piece in source.items():
            current_piece = shallow_copy(piece)
            current_piece.board = self
            self._piece_array[location] = current_piece
        self._ranks: Final[int] = source.ranks
        self._turn: Final[pieces.Color] = source.turn

    def __eq__(self, other: BoardArchive | Board) -> bool:
        return (
            self._castling_rights == other._castling_rights
            and self._files == other._files
            and self._pawn_ranks == other._pawn_ranks
            and self._piece_array == other._piece_array
            and self._ranks == other._ranks
            and self._turn == other._turn
            if isinstance(other, BoardArchive)
            else (
                self._castling_rights == other.castling_rights
                and self._files == other.files
                and self._pawn_ranks == other.pawn_ranks
                and self._piece_array == dict(other)
                and self._ranks == other.ranks
                and self._turn == other.turn
                if isinstance(other, Board)
                else NotImplemented
            )
        )


CHESS_FEN: Final[str] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
"""The starting FEN for standard chess."""
FULLWIDTH_INVERTED_CHECKERBOARD: Final[str] = "\uFF03\uFF0E\n\uFF0E\uFF03"
"""An inverted checkerboard pattern of fullwidth characters."""
FULLWIDTH_STANDARD_CHECKERBOARD: Final[str] = "\uFF0E\uFF03\n\uFF03\uFF0E"
"""A standard checkerboard made of fullwidth characters."""
INVERTED_CHECKERBOARD: Final[str] = "#.\n.#"
"""An inverted checkerboard pattern."""
NO_CASTLING_FEN: Final[str] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
"""The starting FEN for chess, but without castling rights."""
STANDARD_CHECKERBOARD: Final[str] = ".#\n#."
"""A standard checkerboard pattern."""
