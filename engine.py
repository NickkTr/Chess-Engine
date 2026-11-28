import chess
import chess.polyglot
import numpy as np
from utils import softmax
import json
import os
import sys

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3.2,
    chess.BISHOP: 3.3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 10,
}


MOBILITY_SCORES = {
    chess.KNIGHT: 0.03,
    chess.BISHOP: 0.03,
    chess.ROOK: 0.02,
    chess.QUEEN: 0.01
}

MATE_SCORE = 1e5

BOOK_PATH = "openings/baron30.bin"

DEFAULT_SETTINGS = {
    'non_deterministic_moves': False,
    'temperature_beta': 2.0,
    'score_margin': 0.25,
    'verbose': True
}


BASE_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

CONFIG_PATH = os.path.join(BASE_DIR, "settings.json")


def load_engine_settings():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as fp:
            settings = json.load(fp)
    else:
        settings = {}
        print("info string Settings file not found, using defaults instead")

    # set default values if they aren't present in the array
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)

    return settings



def get_book_move(board: chess.Board, book_path: str = BOOK_PATH) -> chess.Move | None:
    try:
        with chess.polyglot.open_reader(book_path) as reader:
            # picks a move probabilistically based on its book weight (frequency/winrate)
            entry = reader.weighted_choice(board)
            return entry.move
    except (IndexError, FileNotFoundError):
        # IndexError means the current position is not in the book (out of theory)
        return None



def _side_activity_and_hanging_score(board: chess.Board, side: chess.Color) -> int:
    enemy = not side
    enemy_pawn_attacks = chess.SquareSet()
    for p_sq in board.pieces(chess.PAWN, enemy):
        enemy_pawn_attacks |= board.attacks(p_sq)

    total_score = 0

    # attacked squares not controlled by enemy pawns
    for piece_type, weight in MOBILITY_SCORES.items():
        for sq in board.pieces(piece_type, side):
            controlled = board.attacks(sq) & ~enemy_pawn_attacks
            total_score += len(controlled) * weight


    # hanging pieces check (attacked by enemy, no pieces defending)
    hanging_pieces_value_factor = 0.2
    for piece_type in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        piece_val = PIECE_VALUES[piece_type]
 
        for sq in board.pieces(piece_type, side):
            if board.is_attacked_by(enemy, sq) and not board.is_attacked_by(side, sq):
                total_score -= piece_val * hanging_pieces_value_factor

    return total_score


def evaluate_board_position(board: chess.Board, positive_side: chess.Color, curr_search_depth: int = 0):
    """
    Evaluate a chess position from the perspective of positive_side.
    Returns a large positive or negative score for checkmate.
    Checkmate scores favor faster wins and therefore include curr_search_depth.
    Stalemate and insufficient-material positions return a neutral score.
    Otherwise, the score is based on the material difference on the board.
    Each side's piece counts are weighted by the values in PIECE_VALUES.
    A positive result favors positive_side, and a negative result favors it less.
    Kings have a value of zero because the game result is handled separately.
    This function does not consider positional or mobility factors.
    """
    if board.is_checkmate():
        own_side_won = (board.turn != positive_side)

        # if two paths both give mate, without curr_search_depth minimax would rank them equally.
        # by giving a slightly lower score to checkmates that take more moves, we make sure that the bot will
        # always look for the mate as soon as possible
        return MATE_SCORE+curr_search_depth if own_side_won else -(MATE_SCORE + curr_search_depth)

    if board.is_stalemate() or board.is_insufficient_material():
        return 0


    # material count with bitboards
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        own_count = len(board.pieces(piece_type, positive_side))
        opp_count = len(board.pieces(piece_type, not positive_side))
        score += (own_count - opp_count) * value

    score += _side_activity_and_hanging_score(board, positive_side)
    score -= _side_activity_and_hanging_score(board, not positive_side)

    return score


# most valuable victim, least valuable attacker based sorting of the moves
def mvv_lva_score(board: chess.Board, move: chess.Move):
    move_score = 0

    if board.is_capture(move):
        attacker_type = board.piece_at(move.from_square).piece_type
        victim_type = board.piece_at(move.to_square).piece_type if not board.is_en_passant(move) else chess.PAWN

        move_score += 10 * PIECE_VALUES[victim_type] - PIECE_VALUES[attacker_type]

    if move.promotion is not None:
        move_score += PIECE_VALUES[move.promotion]

    return move_score


def find_best_move(
    board: chess.Board, 
    depth: int,
    settings: dict = DEFAULT_SETTINGS,
) -> chess.Move|None:
    book_move = get_book_move(board)
    if book_move is not None:
        if settings['verbose']:
            print("info string Responded with book move", flush=True)   
        return book_move

    # if we always want to pick the best move, we need to remove the relaxation on alpha beta pruning
    score_margin = settings['score_margin'] if settings['non_deterministic_moves'] else 0

    computer_side = board.turn
    legal_moves = sorted(board.legal_moves, key=lambda move: mvv_lva_score(board, move), reverse=True)
    best_move = None
    best_score = -float('inf')

    moves = list(legal_moves)
    move_scores = np.full((len(moves),), -np.inf, dtype=np.float32)

    for idx, move in enumerate(legal_moves):
        board.push(move)
        eval_score = minimax(board, depth-1, computer_side, alpha = best_score - score_margin)
        board.pop()

        move_scores[idx] = eval_score

        if eval_score > best_score:
            best_score = eval_score
            best_move = move

    # skip the move selections step if the settings always require the best move 
    if not settings['non_deterministic_moves']:
        return best_move

    # last indices correspond to the top moves
    threshold = best_score - score_margin if np.isfinite(best_score) else -np.inf
    kept_mask = move_scores >= threshold

    kept_moves = [move for move, keep in zip(moves, kept_mask) if keep]
    kept_scores = move_scores[kept_mask]

    probs = softmax(kept_scores, beta=settings['temperature_beta'])
    selected_idx = int(np.random.choice(len(kept_moves), p=probs))
    selected_move = kept_moves[selected_idx]

    if settings['verbose']:
        print(
            f"info string kept: {len(kept_moves)}\n"
            f"info string scores: {np.round(kept_scores, 2)}\n"
            f"info string probs: {np.round(probs, 2)}\n",
            f"info string picked best move: {kept_scores[selected_idx] == best_score}\n",
            flush=True,
        )

    return selected_move






def minimax(
    board: chess.Board, 
    depth: int, 
    computer_side: chess.Color,
    alpha: float = -float('inf'),
    beta: float = float('inf')
) -> float:  

    if board.is_repetition(2):
        return 0
    
    if depth == 0 or board.is_game_over():
        # we always reurn the heuristic evaluation from the computer's POV.
        return evaluate_board_position(board, computer_side, curr_search_depth=depth)

    # the computer will always try to maximize its score, its opponent will always try to minimize the computer's score
    is_maximizing_side = (board.turn == computer_side)

    # computer's turn: we try to maximize the score
    if is_maximizing_side:
        maxEval = -float('inf')
        legal_moves = board.legal_moves if depth == 1 else sorted(board.legal_moves, key=lambda move: mvv_lva_score(board, move), reverse=True)

        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth-1, computer_side, alpha, beta)
            board.pop()

            maxEval = max(maxEval, eval)

            alpha = max(alpha, eval)
            if beta <= alpha:
                break

        return maxEval

    # not the computer's turn, the opponent will try to minimize the computer's score
    else:
        minEval = float('inf')

        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth-1, computer_side, alpha, beta)
            board.pop()
            
            minEval = min(minEval, eval)
            
            beta = min(beta, eval)
            if beta <= alpha:
                break

        return minEval