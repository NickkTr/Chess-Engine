import chess
import numpy as np

def get_board_square(board_x: int, board_y: int) -> chess.Square:
    """
    Given two indices between 0 and 7 representing the coordinates on the board.
    The origin of the board is assumed to be on the bottom left (looking as white). 
    x grows moving towards the right, y grows moving towards the top.
    """
    # board_y = 7 - board_y
    row_letter = ord('a') + board_x
    row_letter = chr(row_letter)

    square = chess.parse_square(row_letter + str(board_y + 1))

    return square



def get_square_coords(square_num: chess.Square) -> tuple[int, int]:
    """ Given a chess square, this function returns its coordinates """
    x_coord = square_num % 8
    y_coord = square_num // 8
    return x_coord, y_coord


def softmax(x: np.ndarray, beta: float = 1.0) -> np.ndarray:
    max_logit = np.max(x)
    normalized_logits = x - max_logit
    z = np.exp(beta * normalized_logits)
    return z / np.sum(z)