from enum import Enum
from enum import auto as enum_gen
from itertools import product as all_pairs
from typing import Final, Optional, Sequence, SupportsIndex

from lib import settings


class Color(Enum):
    NEUTRAL = enum_gen()
    WHITE = enum_gen()
    BLACK = enum_gen()

    def next(self):
        if self == Color.NEUTRAL:
            raise ValueError("Color NEUTRAL has no next color")
        return {Color.WHITE: Color.BLACK, Color.BLACK: Color.WHITE}[self]

    def __str__(self) -> str:
        return {Color.NEUTRAL: "Neutral", Color.WHITE: "White", Color.BLACK: "Black"}[
            self
        ]


PLAYER_COLORS: Final[frozenset[Color]] = frozenset({Color.WHITE, Color.BLACK})

from lib import board


class Piece:
    def __init__(
        self, position: board.Coordinate, color: Color, board_ref: board.Board
    ) -> None:
        if not isinstance(position, board.Coordinate):
            raise TypeError(
                "position must be of type Coordinate (not "
                + type(position).__name__
                + ")"
            )
        elif not isinstance(color, Color):
            raise TypeError(
                "color must be of type Color (not " + type(color).__name__ + ")"
            )
        elif not isinstance(board_ref, board.Board):
            raise TypeError(
                "board_ref must be of type Board (not " + type(board_ref).__name__ + ")"
            )
        self.pos: board.Coordinate = position
        self.color: Final[Color] = color
        self.board: board.Board = board_ref

    def attacked_by(self) -> frozenset:
        "Returns the set of all enemy pieces that can attack this piece."
        attackers: set[Piece] = set()
        for rank, file in all_pairs(range(self.board.ranks), range(self.board.files)):
            piece_of_interest = self.board.piece_array[board.Coordinate((file, rank))]
            if (
                self.color != piece_of_interest.color
                and self.pos in piece_of_interest.moves()
            ):
                attackers.add(piece_of_interest)
        return frozenset(attackers)

    def __eq__(self, other) -> bool:
        return (
            self.color == other.color if type(self) == type(other) else NotImplemented
        )

    def move(self, dest: board.Coordinate, promotion: Optional[type] = None):
        "Moves the piece to the given destination, and returns the piece that was captured, if any."
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must be a piece class if specified (not "
                + type(promotion).__name__
                + ")"
            )
        elif dest.file > self.board.files or dest.rank > self.board.ranks:
            raise IndexError("dest must be inside self.board")
        self.board.en_passant = None
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        try:
            captured_piece: Optional[Piece] = self.board[dest]
        except KeyError:
            captured_piece = None
            self.board.halfmove_clock += 1
        else:
            self.board.halfmove_clock = 0
        del self.board[self.pos]
        if promotion is None:
            self.pos = dest
            self.board[dest] = self
        else:
            self.board[dest] = promotion(dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[board.Coordinate]:
        "Returns the set of all spaces that the piece can move to, excluding rules about check or self-capture."
        return frozenset()

    def __repr__(self) -> str:
        return type(self).__name__ + repr((self.pos, self.color, self.board))


def leap(piece: Piece, step: Sequence[SupportsIndex]) -> frozenset[board.Coordinate]:
    "Returns the location of a leap from the piece's position with an offset given if it is a legal position."
    if not isinstance(piece, Piece):
        raise TypeError(
            "piece must be of type Piece (not " + type(piece).__name__ + ")"
        )
    try:
        test_pos: board.Coordinate = piece.pos + step
        if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
            raise IndexError
        return frozenset({test_pos})
    except IndexError:
        return frozenset()


def ride(piece: Piece, step: Sequence[SupportsIndex]) -> frozenset[board.Coordinate]:
    "Returns a line of empty spaces from the piece's position to the next occupied square or the edge of the board, using the step size given."
    if not isinstance(piece, Piece):
        raise TypeError(
            "piece must be of type Piece (not " + type(piece).__name__ + ")"
        )
    test_pos: board.Coordinate = piece.pos
    positions: set[board.Coordinate] = set()
    while True:
        try:
            test_pos += step
            if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
                raise IndexError
        except IndexError:
            return frozenset(positions)
        positions.add(test_pos)
        if test_pos in piece.board:
            return frozenset(positions)


def sym_leap(
    piece: Piece, step: Sequence[SupportsIndex]
) -> frozenset[board.Coordinate]:
    "Similar to the standard leap() function, but includes all possible reflections and rotations of the step value."
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


def sym_ride(
    piece: Piece, step: Sequence[SupportsIndex]
) -> frozenset[board.Coordinate]:
    "Similar to the standard ride() function, but includes all possible reflections and rotations of the step value."
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
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Bishop(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 1))


class Empress(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_leap(self, (2, 1))


class King(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_leap(self, (1, 0)) | sym_leap(self, (1, 1))


class Knight(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_leap(self, (2, 1))


class Nightrider(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (2, 1))


class Pawn(Piece):
    def move(
        self, dest: board.Coordinate, promotion: Optional[type] = None
    ) -> Optional[Piece]:
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must of type Piece or NoneType (not "
                + type(promotion).__name__
                + ")"
            )
        self.board.halfmove_clock = 0
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        if dest == self.board.en_passant:
            capture_location: Final[board.Coordinate] = dest + (
                0,
                -1 if self.color == Color.WHITE else 1,
            )
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
                dest + (0, -1 if self.color == Color.WHITE else 1)
                if abs(self.pos.rank - dest.rank) == 2
                else None
            )
        del self.board[self.pos]
        if promotion is None:
            self.pos = dest
            self.board[dest] = self
        else:
            self.board[dest] = promotion(dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[board.Coordinate]:
        legal_moves: set[board.Coordinate] = set()
        test_pos: board.Coordinate
        match self.color:
            case Color.WHITE:
                try:
                    test_pos = self.pos + (0, 1)
                    if test_pos.rank >= self.board.ranks:
                        raise IndexError
                except IndexError:
                    return frozenset()
                if test_pos not in self.board:
                    legal_moves.add(test_pos)
                    if self.pos.rank == self.board.pawn_ranks[Color.WHITE]:
                        try:
                            test_pos += (0, 1)
                            if test_pos.rank >= self.board.ranks:
                                raise IndexError
                        except IndexError:
                            pass
                        else:
                            if test_pos not in self.board:
                                legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (-1, 1)
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board:
                        legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (1, 1)
                    if test_pos.file >= self.board.files:
                        raise IndexError
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board:
                        legal_moves.add(test_pos)
            case Color.BLACK:
                try:
                    test_pos = self.pos + (0, -1)
                except IndexError:
                    return frozenset()
                if test_pos not in self.board:
                    legal_moves.add(test_pos)
                    if self.pos.rank == self.board.pawn_ranks[Color.BLACK]:
                        try:
                            test_pos += (0, -1)
                        except IndexError:
                            pass
                        else:
                            if test_pos not in self.board:
                                legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (-1, -1)
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board:
                        legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (1, -1)
                    if test_pos.file >= self.board.files:
                        raise IndexError
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board:
                        legal_moves.add(test_pos)
        return frozenset(legal_moves)


class Princess(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Queen(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1))


class Rook(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0))


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
STANDARD_PIECE_SYMBOLS: Final[dict[settings.CharSet, dict[type, dict[Color, str]]]] = {
    settings.CharSet.ASCII: {
        Amazon: {Color.WHITE: "A", Color.BLACK: "a"},
        Bishop: {Color.WHITE: "B", Color.BLACK: "b"},
        Empress: {Color.WHITE: "M", Color.BLACK: "m"},
        King: {Color.WHITE: "K", Color.BLACK: "k"},
        Knight: {Color.WHITE: "N", Color.BLACK: "n"},
        Nightrider: {Color.WHITE: "S", Color.BLACK: "s"},
        Pawn: {Color.WHITE: "P", Color.BLACK: "p"},
        Piece: {Color.NEUTRAL: " "},
        Princess: {Color.WHITE: "C", Color.BLACK: "c"},
        Queen: {Color.WHITE: "Q", Color.BLACK: "q"},
        Rook: {Color.WHITE: "R", Color.BLACK: "r"},
    },
    settings.CharSet.EXTENDED: {
        Amazon: {Color.WHITE: "\uFF21", Color.BLACK: "\uFF41"},
        Bishop: {Color.WHITE: "\u2657", Color.BLACK: "\u265D"},
        Empress: {Color.WHITE: "\uFF2D", Color.BLACK: "\uFF2D"},
        King: {Color.WHITE: "\u2654", Color.BLACK: "\u265A"},
        Knight: {Color.WHITE: "\u2658", Color.BLACK: "\u265E"},
        Nightrider: {Color.WHITE: "\uFF33", Color.BLACK: "\uFF53"},
        Pawn: {Color.WHITE: "\u2659", Color.BLACK: "\u265F"},
        Piece: {Color.NEUTRAL: "\u3000"},
        Princess: {Color.WHITE: "\uFF23", Color.BLACK: "\uFF43"},
        Queen: {Color.WHITE: "\u2655", Color.BLACK: "\u265B"},
        Rook: {Color.WHITE: "\u2657", Color.BLACK: "\u265C"},
    },
    settings.CharSet.FULL: {
        Amazon: {Color.WHITE: "\U0001FA4E", Color.BLACK: "\U0001FA51"},
        Bishop: {
            Color.NEUTRAL: "\U0001FA03",
            Color.WHITE: "\u2657",
            Color.BLACK: "\u265D",
        },
        Empress: {Color.WHITE: "\U0001FA4F", Color.BLACK: "\U0001FA52"},
        King: {
            Color.NEUTRAL: "\U0001FA00",
            Color.WHITE: "\u2654",
            Color.BLACK: "\u265A",
        },
        Knight: {
            Color.NEUTRAL: "\U0001FA04",
            Color.WHITE: "\u2658",
            Color.BLACK: "\u265E",
        },
        Nightrider: {
            Color.NEUTRAL: "\U0001FA2E",
            Color.WHITE: "\U0001FA22",
            Color.BLACK: "\U0001FA20",
        },
        Pawn: {
            Color.NEUTRAL: "\U0001FA05",
            Color.WHITE: "\u2659",
            Color.BLACK: "\u265F",
        },
        Piece: {Color.NEUTRAL: "\u3000"},
        Princess: {Color.WHITE: "\U0001FA50", Color.BLACK: "\U0001FA53"},
        Queen: {
            Color.NEUTRAL: "\U0001FA01",
            Color.WHITE: "\u2655",
            Color.BLACK: "\u265B",
        },
        Rook: {
            Color.NEUTRAL: "\U0001FA02",
            Color.WHITE: "\u2657",
            Color.BLACK: "\u265C",
        },
    },
}
