import chess

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3.2,
    chess.BISHOP: 3.3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}


MOBILITY_SCORES = {
    chess.KNIGHT: 0.03,
    chess.BISHOP: 0.03,
    chess.ROOK: 0.02,
    chess.QUEEN: 0.01
}

MATE_SCORE = 1e5



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



def find_best_move(board: chess.Board, depth: int) -> chess.Move|None:
    computer_side = board.turn
    best_move = next(iter(board.legal_moves), None)
    best_score = -float('inf')

    for move in board.legal_moves:
        board.push(move)
        eval_score = minimax(board, depth-1, computer_side, alpha = best_score)
        board.pop()

        if eval_score > best_score:
            best_move = move
            best_score = eval_score

    return best_move





def minimax(
    board: chess.Board, 
    depth: int, 
    computer_side: chess.Color,
    alpha: float = -float('inf'),
    beta: float = float('inf')
) -> float:  
    if depth == 0 or board.is_game_over():
        # we always reurn the heuristic evaluation from the computer's POV.
        return evaluate_board_position(board, computer_side, curr_search_depth=depth)

    # the computer will always try to maximize its score, its opponent will always try to minimize the computer's score
    is_maximizing_side = (board.turn == computer_side)

    # computer's turn: we try to maximize the score
    if is_maximizing_side:
        maxEval = -float('inf')

        for move in board.legal_moves:
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