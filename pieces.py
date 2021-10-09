from typing import Final, Optional, Sequence, SupportsIndex

import board

# These values are placeholders that should be defined in the variant structure once it is created.
# !!! DO NOT LEAVE THESE HERE !!!
WHITE_PAWN_RANK: Final[int] = 1
BLACK_PAWN_RANK: Final[int] = 6


class Piece:
    def __init__(
        self, position: board.Coordinate, color: board.Color, board_ref: board.Board
    ):
        if not isinstance(position, board.Coordinate):
            raise TypeError(
                "position must be of type Coordinate (not "
                + type(position).__name__ + ")"
            )
        elif not isinstance(color, board.Color):
            raise TypeError(
                "color must be of type Color (not " +
                type(color).__name__ + ")"
            )
        elif not isinstance(board_ref, board.Board):
            raise TypeError(
                "board_ref must be of type Board (not " +
                type(board_ref).__name__ + ")"
            )
        self.pos: board.Coordinate = position
        self.color: Final[board.Color] = color
        self.board: board.Board = board_ref

    def move(self, dest: board.Coordinate, promotion: Optional[type] = None):
        "Moves the piece to the given destination, and returns the piece that was captured, if any."
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must be a piece class if specified (not " + type(promotion).__name__ + ")")
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
            self.board.piece_array[dest] = promotion(
                dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[board.Coordinate]:
        "Returns the set of all spaces that the piece can move to, excluding rules about check or self-capture."
        return frozenset()


def leap(piece: Piece, step: Sequence[SupportsIndex]) -> frozenset[board.Coordinate]:
    "Returns the location of a leap from the piece's position with an offset given if it is a legal position."
    if not isinstance(piece, Piece):
        raise TypeError(
            "piece must be of type Piece or of a type derived from Piece (not "
            + type(piece).__name__
            + ")"
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
            "piece must be of type Piece or of a type derived from Piece (not "
            + type(piece).__name__
            + ")"
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
        if test_pos in piece.board.piece_array:
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
    def move(self, dest: board.Coordinate, promotion: Optional[type] = None) -> Optional[Piece]:
        if not (promotion is None or issubclass(promotion, Piece)):
            raise TypeError(
                "promotion must be a piece class if specified (not " + type(promotion).__name__ + ")")
        self.board.en_passant = dest + \
            (0, -1 if self.color == board.Color.WHITE else 1) if abs(
                self.pos.rank - dest.rank) == 2 else None
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
            self.board.piece_array[dest] = promotion(
                dest, self.color, self.board)
        return captured_piece

    def moves(self) -> frozenset[board.Coordinate]:
        legal_moves: set[board.Coordinate] = set()
        test_pos: board.Coordinate
        match self.color:
            case board.Color.WHITE:
                try:
                    test_pos = self.pos + (0, 1)
                    if test_pos.rank >= self.board.ranks:
                        raise IndexError
                except IndexError:
                    return frozenset()
                if test_pos not in self.board.piece_array:
                    legal_moves.add(test_pos)
                    if self.pos.rank == WHITE_PAWN_RANK:
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
            case board.Color.BLACK:
                try:
                    test_pos = self.pos + (0, -1)
                except IndexError:
                    return frozenset()
                if test_pos not in self.board.piece_array:
                    legal_moves.add(test_pos)
                    if self.pos.rank == BLACK_PAWN_RANK:
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
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 1)) | sym_leap(self, (2, 1))


class Queen(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0)) | sym_ride(self, (1, 1))


class Rook(Piece):
    def moves(self) -> frozenset[board.Coordinate]:
        return sym_ride(self, (1, 0))