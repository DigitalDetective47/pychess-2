import board
import pieces
import settings


def main():
    game_board = board.Board(board.CHESS_FEN, pieces.STANDARD_PIECE_TABLE)
    game_board.piece_array[board.Coordinate("e2")].move(board.Coordinate("e4"))
    print(game_board.piece_array[board.Coordinate("c2")].moves())
    print(
        game_board.render(
            pieces.STANDARD_PIECE_SYMBOLS[settings.CharSet.ASCII],
            board.STANDARD_CHECKERBOARD,
            board.Color.WHITE,
        )
    )
