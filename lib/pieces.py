"""Piece data for PyChess 2.

Classes:
Color -- The color of a piece.
Piece -- A chess piece.
Amazon -- A hybrid of the Queen and Knight.
Bishop
Empress -- A hybrid of the Rook and Knight.
King
Knight
Nightrider -- Repeats Knight moves in one direction.
Pawn
Princess -- A hybrid of the Bishop and Knight.
Queen
Rook

Functions:
leap -- Return the location of a leap from the piece's position with an offset given if it is a legal position.
ride -- Return a line of empty spaces from the piece's position to the next occupied square or the edge of the board, using the step given.
sym_leap -- Return all possible reflections and rotations of leap with the given arguments.
sym_ride -- Return all possible reflections and rotations of ride with the given arguments.

Objects:
PLAYER_COLORS -- Both player colors.
DARK_MODE_PIECE_SYMBOLS -- Standard piece symbol set for dark mode. Index once with the character set before using.
STANDARD_PIECE_SYMBOLS -- Standard piece symbol set to be used with the render method of Boards. Index once with the character set before using.
STANDARD_PIECE_TABLE -- Standard piece table to be used with the Board constructor.
"""

from __future__ import annotations

from enum import Enum
from enum import auto as enum_gen
from enum import unique
from functools import cache
from itertools import product as all_pairs
from typing import Final, Optional, Sequence, SupportsIndex

from lib import settings


@unique
class Color(Enum):
    """The color of a piece.

    Enumeration members:
    NEUTRAL
    WHITE
    BLACK
    """

    NEUTRAL = enum_gen()
    WHITE = enum_gen()
    BLACK = enum_gen()

    def next(self) -> Color:
        try:
            return {Color.WHITE: Color.BLACK, Color.BLACK: Color.WHITE}[self]
        except KeyError:
            raise ValueError(f"{self!r} has no next color")

    def __str__(self) -> str:
        return {Color.NEUTRAL: "Neutral", Color.WHITE: "White", Color.BLACK: "Black"}[
            self
        ]


PLAYER_COLORS: Final[frozenset[Color]] = frozenset({Color.WHITE, Color.BLACK})
"""Both player colors."""

from lib import board


class Piece:
    """A chess piece.

    Instance methods:
    attacked_by
    __eq__
    move
    moves
    repr

    Instance attributes:
    pos
    color (Read-only)
    board
    """

    def __init__(
        self,
        position: board.Coordinate,
        color: Color,
        board_ref: board.Board | board.BoardArchive,
    ) -> None:
        """Create a new piece.

        Required positional arguments:
        position -- The location of the piece.
        color -- The color of the piece.
        board_ref -- The board that the piece is on.
        """
        self.board: board.Board | board.BoardArchive = board_ref
        """The board that this piece is on."""
        self._color: Final[Color] = color
        self.pos: board.Coordinate = position
        """The location of this piece."""

    def attacked_by(self) -> frozenset[Piece]:
        """Return all enemy pieces that can attack this piece."""
        attackers: set[Piece] = set()
        for rank, file in all_pairs(range(self.board.ranks), range(self.board.files)):
            piece_of_interest = self.board[board.Coordinate(file, rank)]
            if (
                self.color is not piece_of_interest.color
                and self.pos in piece_of_interest.moves()
            ):
                attackers.add(piece_of_interest)
        return frozenset(attackers)

    @property
    def color(self) -> Color:
        """The color of this piece."""
        return self._color

    def __eq__(self, other: Piece) -> bool:
        return (
            self.color == other.color if type(self) == type(other) else NotImplemented
        )

    def move(
        self, dest: board.Coordinate, promotion: Optional[type] = None
    ) -> Optional[Piece]:
        """Move this piece to the given destination. If a piece was captured, return it."""
        if dest.file > self.board.files or dest.rank > self.board.ranks:
            raise IndexError("dest must be inside of the piece's board")
        self.board.en_passant = None
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        try:
            captured_piece: Optional[Piece] = self.board[dest]
        except KeyError:
            captured_piece = None
        del self.board[self.pos]
        if promotion is None:
            self.pos = dest
            self.board[dest] = self
        else:
            self.board[dest] = promotion(dest, self.color, self.board)
        if captured_piece is None:
            self.board.increment_halfmove()
        else:
            self.board.reset_halfmove()
        return captured_piece

    def moves(self) -> set[board.Coordinate]:
        "Return all spaces that this piece can move to, excluding rules about check or self-capture."
        return set()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.pos!r}, {self.color!r}, {self.board!r})"


def leap(piece: Piece, step: Sequence[SupportsIndex]) -> set[board.Coordinate]:
    """Return the location of a leap from the piece's position with an offset given if it is a legal position.

    Required positional arguments:
    piece -- The piece to check moves of.
    step -- The length and direction of a step.
    """
    try:
        test_pos: board.Coordinate = piece.pos + step
        if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
            raise IndexError
        return {test_pos}
    except IndexError:
        return set()


def ride(piece: Piece, step: Sequence[SupportsIndex]) -> set[board.Coordinate]:
    """Return a line of empty spaces from the piece's position to the next occupied square or the edge of the board, using the step given.

    Required positional arguments:
    piece -- The piece to check moves of.
    step -- The length and direction of a step.
    """
    test_pos: board.Coordinate = piece.pos
    positions: set[board.Coordinate] = set()
    while True:
        try:
            test_pos += step
            if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
                raise IndexError
        except IndexError:
            return positions
        positions.add(test_pos)
        if test_pos in piece.board:
            return positions


def sym_leap(piece: Piece, step: Sequence[SupportsIndex]) -> set[board.Coordinate]:
    """Return all possible reflections and rotations of leap with the given arguments.

    Required positional arguments:
    piece -- The piece to check moves of.
    step -- The length of a step.
    """
    return (
        leap(piece, step)
        | leap(piece, (-step[0], step[1]))
        | leap(piece, (step[0], -step[1]))
        | leap(piece, (-step[0], -step[1]))
        | leap(piece, (step[1], step[0]))
        | leap(piece, (-step[1], step[0]))
        | leap(piece, (step[1], -step[0]))
        | leap(piece, (-step[1], -step[0]))
    )


def sym_ride(piece: Piece, step: Sequence[SupportsIndex]) -> set[board.Coordinate]:
    """Return all possible reflections and rotations of ride with the given arguments.

    Required positional arguments:
    piece -- The piece to check moves of.
    step -- The length of a step.
    """
    return (
        ride(piece, step)
        | ride(piece, (-step[0], step[1]))
        | ride(piece, (step[0], -step[1]))
        | ride(piece, (-step[0], -step[1]))
        | ride(piece, (step[1], step[0]))
        | ride(piece, (-step[1], step[0]))
        | ride(piece, (step[1], -step[0]))
        | ride(piece, (-step[1], -step[0]))
    )


class Amazon(Piece):
    """A hybrid of the Queen and Knight."""

    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Bishop(Piece):
    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 1))


class Empress(Piece):
    """A hybrid of the Rook and Knight."""

    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_leap(self, (2, 1))


class King(Piece):
    def moves(self) -> set[board.Coordinate]:
        return sym_leap(self, (1, 0)) | sym_leap(self, (1, 1))


class Knight(Piece):
    def moves(self) -> set[board.Coordinate]:
        return sym_leap(self, (2, 1))


class Nightrider(Piece):
    """Repeats Knight moves in one direction."""

    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (2, 1))


class Pawn(Piece):
    def __init__(
        self,
        position: board.Coordinate,
        color: Color,
        board_ref: board.Board | board.BoardArchive,
    ) -> None:
        if color not in PLAYER_COLORS:
            raise ValueError(f"color must be a player color (not {color!r})")
        super().__init__(position, color, board_ref)

    def move(
        self, dest: board.Coordinate, promotion: Optional[type] = None
    ) -> Optional[Piece]:
        self.board.reset_halfmove()
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        reverse_step: tuple[int, int]
        match self.color:
            case Color.WHITE:
                reverse_step = (0, 1)
            case Color.BLACK:
                reverse_step = (0, -1)
        if dest == self.board.en_passant:
            self.board.en_passant = None
            capture_location: Final[board.Coordinate] = dest + reverse_step
            try:
                captured_piece: Optional[Piece] = self.board[capture_location]
                del self.board[capture_location]
            except KeyError:
                captured_piece = None
        else:
            try:
                captured_piece: Optional[Piece] = self.board[dest]
            except KeyError:
                captured_piece = None
            self.board.en_passant = (
                dest + reverse_step if abs(self.pos.rank - dest.rank) == 2 else None
            )
        del self.board[self.pos]
        if promotion is None:
            self.pos = dest
            self.board[dest] = self
        else:
            self.board[dest] = promotion(dest, self.color, self.board)
        return captured_piece

    def moves(self) -> set[board.Coordinate]:
        base_step: tuple[int, int]
        test_pos: board.Coordinate
        match self.color:
            case Color.WHITE:
                base_step = (0, 1)
            case Color.BLACK:
                base_step = (0, -1)
        try:
            test_pos = self.pos + base_step
            if test_pos.rank >= self.board.ranks:
                raise IndexError
        except IndexError:
            return set()
        legal_moves: set[board.Coordinate] = set()
        if test_pos not in self.board:
            legal_moves.add(test_pos)
            if self.pos.rank == self.board.pawn_ranks[self.color]:
                try:
                    test_pos += base_step
                    if test_pos.rank >= self.board.ranks:
                        raise IndexError
                except IndexError:
                    pass
                else:
                    if test_pos not in self.board:
                        legal_moves.add(test_pos)
        try:
            test_pos = self.pos + base_step + (-1, 0)
        except IndexError:
            pass
        else:
            if test_pos == self.board.en_passant or test_pos in self.board:
                legal_moves.add(test_pos)
        try:
            test_pos = self.pos + base_step + (1, 0)
            if test_pos.file >= self.board.files:
                raise IndexError
        except IndexError:
            pass
        else:
            if test_pos == self.board.en_passant or test_pos in self.board:
                legal_moves.add(test_pos)
        return legal_moves


class Princess(Piece):
    """A hybrid of the Bishop and Knight."""

    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Queen(Piece):
    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1))


class Rook(Piece):
    def moves(self) -> set[board.Coordinate]:
        return sym_ride(self, (1, 0))


@cache
def _colored_piece(piece_type: type, piece_color: Color) -> frozenset[type | Color]:
    """Return a frozenset of its two arguments. Uses a cache to make multiple calls with the same arguments return the same frozenset."""
    return frozenset({piece_type, piece_color})


DARK_MODE_PIECE_SYMBOLS: Final[
    dict[settings.CharSet, dict[frozenset[type | Color], str]]
] = {
    settings.CharSet.ASCII: {
        _colored_piece(Amazon, Color.WHITE): "A",
        _colored_piece(Amazon, Color.BLACK): "a",
        _colored_piece(Bishop, Color.WHITE): "B",
        _colored_piece(Bishop, Color.BLACK): "b",
        _colored_piece(Empress, Color.WHITE): "M",
        _colored_piece(Empress, Color.BLACK): "m",
        _colored_piece(King, Color.WHITE): "K",
        _colored_piece(King, Color.BLACK): "k",
        _colored_piece(Knight, Color.WHITE): "N",
        _colored_piece(Knight, Color.BLACK): "n",
        _colored_piece(Nightrider, Color.WHITE): "S",
        _colored_piece(Nightrider, Color.BLACK): "s",
        _colored_piece(Pawn, Color.WHITE): "P",
        _colored_piece(Pawn, Color.BLACK): "p",
        _colored_piece(Piece, Color.NEUTRAL): " ",
        _colored_piece(Princess, Color.WHITE): "C",
        _colored_piece(Princess, Color.BLACK): "c",
        _colored_piece(Queen, Color.WHITE): "Q",
        _colored_piece(Queen, Color.BLACK): "q",
        _colored_piece(Rook, Color.WHITE): "R",
        _colored_piece(Rook, Color.BLACK): "r",
    },
    settings.CharSet.BMP: {
        _colored_piece(Amazon, Color.WHITE): "\uFF21",
        _colored_piece(Amazon, Color.BLACK): "\uFF41",
        _colored_piece(Bishop, Color.WHITE): "\u265D",
        _colored_piece(Bishop, Color.BLACK): "\u2657",
        _colored_piece(Empress, Color.WHITE): "\uFF2D",
        _colored_piece(Empress, Color.BLACK): "\uFF4D",
        _colored_piece(King, Color.WHITE): "\u265A",
        _colored_piece(King, Color.BLACK): "\u2564",
        _colored_piece(Knight, Color.WHITE): "\u265E",
        _colored_piece(Knight, Color.BLACK): "\u2658",
        _colored_piece(Nightrider, Color.WHITE): "\uFF33",
        _colored_piece(Nightrider, Color.BLACK): "\uFF53",
        _colored_piece(Pawn, Color.WHITE): "\u265F",
        _colored_piece(Pawn, Color.BLACK): "\u2659",
        _colored_piece(Piece, Color.NEUTRAL): "\u3000",
        _colored_piece(Princess, Color.WHITE): "\uFF23",
        _colored_piece(Princess, Color.BLACK): "\uFF43",
        _colored_piece(Queen, Color.WHITE): "\u265B",
        _colored_piece(Queen, Color.BLACK): "\u2655",
        _colored_piece(Rook, Color.WHITE): "\u265C",
        _colored_piece(Rook, Color.BLACK): "\u2657",
    },
    settings.CharSet.FULL: {
        _colored_piece(Amazon, Color.WHITE): "\U0001FA51",
        _colored_piece(Amazon, Color.BLACK): "\U0001FA4E",
        _colored_piece(Bishop, Color.NEUTRAL): "\U0001FA03",
        _colored_piece(Bishop, Color.WHITE): "\u265D",
        _colored_piece(Bishop, Color.BLACK): "\u2657",
        _colored_piece(Empress, Color.WHITE): "\U0001FA52",
        _colored_piece(Empress, Color.BLACK): "\U0001FA4F",
        _colored_piece(King, Color.NEUTRAL): "\U0001FA00",
        _colored_piece(King, Color.WHITE): "\u265A",
        _colored_piece(King, Color.BLACK): "\u2654",
        _colored_piece(Knight, Color.NEUTRAL): "\U0001FA04",
        _colored_piece(Knight, Color.WHITE): "\u265E",
        _colored_piece(Knight, Color.BLACK): "\u2658",
        _colored_piece(Nightrider, Color.NEUTRAL): "\U0001FA2E",
        _colored_piece(Nightrider, Color.WHITE): "\U0001FA28",
        _colored_piece(Nightrider, Color.BLACK): "\U0001FA22",
        _colored_piece(Pawn, Color.NEUTRAL): "\U0001FA05",
        _colored_piece(Pawn, Color.WHITE): "\u265F",
        _colored_piece(Pawn, Color.BLACK): "\u2659",
        _colored_piece(Piece, Color.NEUTRAL): "\u3000",
        _colored_piece(Princess, Color.WHITE): "\U0001FA53",
        _colored_piece(Princess, Color.BLACK): "\U0001FA50",
        _colored_piece(Queen, Color.NEUTRAL): "\U0001FA01",
        _colored_piece(Queen, Color.WHITE): "\u265B",
        _colored_piece(Queen, Color.BLACK): "\u2655",
        _colored_piece(Rook, Color.NEUTRAL): "\U0001FA02",
        _colored_piece(Rook, Color.WHITE): "\u265C",
        _colored_piece(Rook, Color.BLACK): "\u2657",
    },
}
"""Standard piece symbol set for dark mode. Index once with the character set before using."""
STANDARD_PIECE_SYMBOLS: Final[
    dict[settings.CharSet, dict[frozenset[type | Color], str]]
] = {
    settings.CharSet.ASCII: {
        _colored_piece(Amazon, Color.WHITE): "A",
        _colored_piece(Amazon, Color.BLACK): "a",
        _colored_piece(Bishop, Color.WHITE): "B",
        _colored_piece(Bishop, Color.BLACK): "b",
        _colored_piece(Empress, Color.WHITE): "M",
        _colored_piece(Empress, Color.BLACK): "m",
        _colored_piece(King, Color.WHITE): "K",
        _colored_piece(King, Color.BLACK): "k",
        _colored_piece(Knight, Color.WHITE): "N",
        _colored_piece(Knight, Color.BLACK): "n",
        _colored_piece(Nightrider, Color.WHITE): "S",
        _colored_piece(Nightrider, Color.BLACK): "s",
        _colored_piece(Pawn, Color.WHITE): "P",
        _colored_piece(Pawn, Color.BLACK): "p",
        _colored_piece(Piece, Color.NEUTRAL): " ",
        _colored_piece(Princess, Color.WHITE): "C",
        _colored_piece(Princess, Color.BLACK): "c",
        _colored_piece(Queen, Color.WHITE): "Q",
        _colored_piece(Queen, Color.BLACK): "q",
        _colored_piece(Rook, Color.WHITE): "R",
        _colored_piece(Rook, Color.BLACK): "r",
    },
    settings.CharSet.BMP: {
        _colored_piece(Amazon, Color.WHITE): "\uFF21",
        _colored_piece(Amazon, Color.BLACK): "\uFF41",
        _colored_piece(Bishop, Color.WHITE): "\u2657",
        _colored_piece(Bishop, Color.BLACK): "\u265D",
        _colored_piece(Empress, Color.WHITE): "\uFF2D",
        _colored_piece(Empress, Color.BLACK): "\uFF4D",
        _colored_piece(King, Color.WHITE): "\u2564",
        _colored_piece(King, Color.BLACK): "\u265A",
        _colored_piece(Knight, Color.WHITE): "\u2658",
        _colored_piece(Knight, Color.BLACK): "\u265E",
        _colored_piece(Nightrider, Color.WHITE): "\uFF33",
        _colored_piece(Nightrider, Color.BLACK): "\uFF53",
        _colored_piece(Pawn, Color.WHITE): "\u2659",
        _colored_piece(Pawn, Color.BLACK): "\u265F",
        _colored_piece(Piece, Color.NEUTRAL): "\u3000",
        _colored_piece(Princess, Color.WHITE): "\uFF23",
        _colored_piece(Princess, Color.BLACK): "\uFF43",
        _colored_piece(Queen, Color.WHITE): "\u2655",
        _colored_piece(Queen, Color.BLACK): "\u2655",
        _colored_piece(Rook, Color.WHITE): "\u2657",
        _colored_piece(Rook, Color.BLACK): "\u265C",
    },
    settings.CharSet.FULL: {
        _colored_piece(Amazon, Color.WHITE): "\U0001FA4E",
        _colored_piece(Amazon, Color.BLACK): "\U0001FA51",
        _colored_piece(Bishop, Color.NEUTRAL): "\U0001FA03",
        _colored_piece(Bishop, Color.WHITE): "\u2657",
        _colored_piece(Bishop, Color.BLACK): "\u265D",
        _colored_piece(Empress, Color.WHITE): "\U0001FA4F",
        _colored_piece(Empress, Color.BLACK): "\U0001FA52",
        _colored_piece(King, Color.NEUTRAL): "\U0001FA00",
        _colored_piece(King, Color.WHITE): "\u2654",
        _colored_piece(King, Color.BLACK): "\u265A",
        _colored_piece(Knight, Color.NEUTRAL): "\U0001FA04",
        _colored_piece(Knight, Color.WHITE): "\u2658",
        _colored_piece(Knight, Color.BLACK): "\u265E",
        _colored_piece(Nightrider, Color.NEUTRAL): "\U0001FA2E",
        _colored_piece(Nightrider, Color.WHITE): "\U0001FA22",
        _colored_piece(Nightrider, Color.BLACK): "\U0001FA28",
        _colored_piece(Pawn, Color.NEUTRAL): "\U0001FA05",
        _colored_piece(Pawn, Color.WHITE): "\u2659",
        _colored_piece(Pawn, Color.BLACK): "\u265F",
        _colored_piece(Piece, Color.NEUTRAL): "\u3000",
        _colored_piece(Princess, Color.WHITE): "\U0001FA50",
        _colored_piece(Princess, Color.BLACK): "\U0001FA53",
        _colored_piece(Queen, Color.NEUTRAL): "\U0001FA01",
        _colored_piece(Queen, Color.WHITE): "\u2655",
        _colored_piece(Queen, Color.BLACK): "\u265B",
        _colored_piece(Rook, Color.NEUTRAL): "\U0001FA02",
        _colored_piece(Rook, Color.WHITE): "\u2657",
        _colored_piece(Rook, Color.BLACK): "\u265C",
    },
}
"""Standard piece symbol set to be used with the render method of Boards. Index once with the character set before using."""
STANDARD_PIECE_TABLE: Final[dict[str, type]] = {
    "A": Amazon,
    "B": Bishop,
    "C": Princess,
    "K": King,
    "N": Knight,
    "M": Empress,
    "P": Pawn,
    "Q": Queen,
    "R": Rook,
    "S": Nightrider,
    "-": Piece,
}
"""Standard piece table to be used with the Board constructor."""

del _colored_piece
