from itertools import product as all_pairs
from typing import Final, Optional, Sequence, SupportsIndex

import lib.board
import lib.settings


class Piece:
    def __init__(
        self, position: lib.board.Coordinate, color: lib.board.Color, board_ref: lib.board.Board
    ) -> None:
        if not isinstance(position, lib.board.Coordinate):
            raise TypeError(
                "position must be of type Coordinate (not "
                + type(position).__name__
                + ")"
            )
        elif not isinstance(color, lib.board.Color):
            raise TypeError(
                "color must be of type Color (not " + type(color).__name__ + ")"
            )
        elif not isinstance(board_ref, lib.board.Board):
            raise TypeError(
                "board_ref must be of type Board (not " + type(board_ref).__name__ + ")"
            )
        self.pos: lib.board.Coordinate = position
        self.color: Final[lib.board.Color] = color
        self.board: lib.board.Board = board_ref

    def attacked_by(self) -> frozenset:
        "Returns the set of all enemy pieces that can attack this piece."
        attackers: set[Piece] = set()
        for rank, file in all_pairs(range(self.board.ranks), range(self.board.files)):
            piece_of_interest = self.board.piece_array[lib.board.Coordinate((file, rank))]
            if self.color != piece_of_interest.color and self.pos in piece_of_interest.moves():
                attackers.add(piece_of_interest)
        return frozenset(attackers)

    def move(self, dest: lib.board.Coordinate, promotion: Optional[type] = None):
        "Moves the piece to the given destination, and returns the piece that was captured, if any."
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must be a piece class if specified (not "
                + type(promotion).__name__
                + ")"
            )
        self.board.en_passant = None
        self.board.halfmove_clock += 1
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        try:
            captured_piece: Optional[Piece] = self.board.piece_array[dest]
        except KeyError:
            captured_piece = None
        del self.board.piece_array[self.pos]
        if promotion is None:
            self.pos = dest
            self.board.piece_array[dest] = self
        else:
            self.board.piece_array[dest] = promotion(dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[lib.board.Coordinate]:
        "Returns the set of all spaces that the piece can move to, excluding rules about check or self-capture."
        return frozenset()


def leap(piece: Piece, step: Sequence[SupportsIndex]) -> frozenset[lib.board.Coordinate]:
    "Returns the location of a leap from the piece's position with an offset given if it is a legal position."
    if not isinstance(piece, Piece):
        raise TypeError(
            "piece must be of type Piece (not "
            + type(piece).__name__
            + ")"
        )
    try:
        test_pos: lib.board.Coordinate = piece.pos + step
        if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
            raise IndexError
        return frozenset({test_pos})
    except IndexError:
        return frozenset()


def ride(piece: Piece, step: Sequence[SupportsIndex]) -> frozenset[lib.board.Coordinate]:
    "Returns a line of empty spaces from the piece's position to the next occupied square or the edge of the board, using the step size given."
    if not isinstance(piece, Piece):
        raise TypeError(
            "piece must be of type Piece (not "
            + type(piece).__name__
            + ")"
        )
    test_pos: lib.board.Coordinate = piece.pos
    positions: set[lib.board.Coordinate] = set()
    while True:
        try:
            test_pos += step
            if test_pos.file >= piece.board.files or test_pos.rank >= piece.board.ranks:
                raise IndexError
        except IndexError:
            return frozenset(positions)
        positions.add(test_pos)
        if test_pos in piece.board.piece_array:
            return frozenset(positions)


def sym_leap(
    piece: Piece, step: Sequence[SupportsIndex]
) -> frozenset[lib.board.Coordinate]:
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
) -> frozenset[lib.board.Coordinate]:
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
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Bishop(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (1, 1))


class Empress(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_leap(self, (2, 1))


class King(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_leap(self, (1, 0)) | sym_leap(self, (1, 1))


class Knight(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_leap(self, (2, 1))


class Nightrider(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (2, 1))


class Pawn(Piece):
    def move(
        self, dest: lib.board.Coordinate, promotion: Optional[type] = None
    ) -> Optional[Piece]:
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must of type Piece or NoneType (not "
                + type(promotion).__name__
                + ")"
            )
        self.board.halfmove_clock += 1
        self.board.turn = self.board.turn.next()
        self.board.fullmove_clock += self.board.turn == self.board.first_player
        if dest == self.board.en_passant:
            capture_location: Final[lib.board.Coordinate] = dest + (
                0,
                -1 if self.color == lib.board.Color.WHITE else 1,
            )
            try:
                captured_piece: Optional[Piece] = self.board.piece_array[
                    capture_location
                ]
                del self.board.piece_array[capture_location]
            except KeyError:
                captured_piece = None
        else:
            try:
                captured_piece: Optional[Piece] = self.board.piece_array[dest]
            except KeyError:
                captured_piece = None
            self.board.en_passant = (
                dest + (0, -1 if self.color == lib.board.Color.WHITE else 1)
                if abs(self.pos.rank - dest.rank) == 2
                else None
            )
        del self.board.piece_array[self.pos]
        if promotion is None:
            self.pos = dest
            self.board.piece_array[dest] = self
        else:
            self.board.piece_array[dest] = promotion(dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[lib.board.Coordinate]:
        legal_moves: set[lib.board.Coordinate] = set()
        test_pos: lib.board.Coordinate
        match self.color:
            case lib.board.Color.WHITE:
                try:
                    test_pos = self.pos + (0, 1)
                    if test_pos.rank >= self.board.ranks:
                        raise IndexError
                except IndexError:
                    return frozenset()
                if test_pos not in self.board.piece_array:
                    legal_moves.add(test_pos)
                    if self.pos.rank == self.board.pawn_ranks[lib.board.Color.WHITE]:
                        try:
                            test_pos += (0, 1)
                            if test_pos.rank >= self.board.ranks:
                                raise IndexError
                        except IndexError:
                            pass
                        else:
                            if test_pos not in self.board.piece_array:
                                legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (-1, 1)
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board.piece_array:
                        legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (1, 1)
                    if test_pos.file >= self.board.files:
                        raise IndexError
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board.piece_array:
                        legal_moves.add(test_pos)
            case lib.board.Color.BLACK:
                try:
                    test_pos = self.pos + (0, -1)
                except IndexError:
                    return frozenset()
                if test_pos not in self.board.piece_array:
                    legal_moves.add(test_pos)
                    if self.pos.rank == self.board.pawn_ranks[lib.board.Color.BLACK]:
                        try:
                            test_pos += (0, -1)
                        except IndexError:
                            pass
                        else:
                            if test_pos not in self.board.piece_array:
                                legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (-1, -1)
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board.piece_array:
                        legal_moves.add(test_pos)
                try:
                    test_pos = self.pos + (1, -1)
                    if test_pos.file >= self.board.files:
                        raise IndexError
                except IndexError:
                    pass
                else:
                    if test_pos == self.board.en_passant or test_pos in self.board.piece_array:
                        legal_moves.add(test_pos)
        return frozenset(legal_moves)


class Princess(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Queen(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1))


class Rook(Piece):
    def moves(self) -> frozenset[lib.board.Coordinate]:
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
STANDARD_PIECE_SYMBOLS: Final[
    dict[lib.settings.CharSet, dict[type, dict[lib.board.Color, str]]]
] = {
    lib.settings.CharSet.ASCII: {
        Amazon: {lib.board.Color.WHITE: "A", lib.board.Color.BLACK: "a"},
        Bishop: {lib.board.Color.WHITE: "B", lib.board.Color.BLACK: "b"},
        Empress: {lib.board.Color.WHITE: "M", lib.board.Color.BLACK: "m"},
        King: {lib.board.Color.WHITE: "K", lib.board.Color.BLACK: "k"},
        Knight: {lib.board.Color.WHITE: "N", lib.board.Color.BLACK: "n"},
        Nightrider: {lib.board.Color.WHITE: "S", lib.board.Color.BLACK: "s"},
        Pawn: {lib.board.Color.WHITE: "P", lib.board.Color.BLACK: "p"},
        Piece: {lib.board.Color.NEUTRAL: " "},
        Princess: {lib.board.Color.WHITE: "C", lib.board.Color.BLACK: "c"},
        Queen: {lib.board.Color.WHITE: "Q", lib.board.Color.BLACK: "q"},
        Rook: {lib.board.Color.WHITE: "R", lib.board.Color.BLACK: "r"},
    },
    lib.settings.CharSet.EXTENDED: {
        Amazon: {lib.board.Color.WHITE: "\uFF21", lib.board.Color.BLACK: "\uFF41"},
        Bishop: {lib.board.Color.WHITE: "\u2657", lib.board.Color.BLACK: "\u265D"},
        Empress: {lib.board.Color.WHITE: "\uFF2D", lib.board.Color.BLACK: "\uFF2D"},
        King: {lib.board.Color.WHITE: "\u2654", lib.board.Color.BLACK: "\u265A"},
        Knight: {lib.board.Color.WHITE: "\u2658", lib.board.Color.BLACK: "\u265E"},
        Nightrider: {lib.board.Color.WHITE: "\uFF33", lib.board.Color.BLACK: "\uFF53"},
        Pawn: {lib.board.Color.WHITE: "\u2659", lib.board.Color.BLACK: "\u265F"},
        Piece: {lib.board.Color.NEUTRAL: "\u3000"},
        Princess: {lib.board.Color.WHITE: "\uFF23", lib.board.Color.BLACK: "\uFF43"},
        Queen: {lib.board.Color.WHITE: "\u2655", lib.board.Color.BLACK: "\u265B"},
        Rook: {lib.board.Color.WHITE: "\u2657", lib.board.Color.BLACK: "\u265C"},
    },
    lib.settings.CharSet.FULL: {
        Amazon: {lib.board.Color.WHITE: "\U0001FA4E", lib.board.Color.BLACK: "\U0001FA51"},
        Bishop: {
            lib.board.Color.NEUTRAL: "\U0001FA03",
            lib.board.Color.WHITE: "\u2657",
            lib.board.Color.BLACK: "\u265D",
        },
        Empress: {lib.board.Color.WHITE: "\U0001FA4F", lib.board.Color.BLACK: "\U0001FA52"},
        King: {
            lib.board.Color.NEUTRAL: "\U0001FA00",
            lib.board.Color.WHITE: "\u2654",
            lib.board.Color.BLACK: "\u265A",
        },
        Knight: {
            lib.board.Color.NEUTRAL: "\U0001FA04",
            lib.board.Color.WHITE: "\u2658",
            lib.board.Color.BLACK: "\u265E",
        },
        Nightrider: {
            lib.board.Color.NEUTRAL: "\U0001FA2E",
            lib.board.Color.WHITE: "\U0001FA22",
            lib.board.Color.BLACK: "\U0001FA20",
        },
        Pawn: {
            lib.board.Color.NEUTRAL: "\U0001FA05",
            lib.board.Color.WHITE: "\u2659",
            lib.board.Color.BLACK: "\u265F",
        },
        Piece: {lib.board.Color.NEUTRAL: "\u3000"},
        Princess: {lib.board.Color.WHITE: "\U0001FA50", lib.board.Color.BLACK: "\U0001FA53"},
        Queen: {
            lib.board.Color.NEUTRAL: "\U0001FA01",
            lib.board.Color.WHITE: "\u2655",
            lib.board.Color.BLACK: "\u265B",
        },
        Rook: {
            lib.board.Color.NEUTRAL: "\U0001FA02",
            lib.board.Color.WHITE: "\u2657",
            lib.board.Color.BLACK: "\u265C",
        },
    },
}
