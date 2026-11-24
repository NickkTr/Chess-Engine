import chess
import chess.svg

board = chess.Board()
piece_map = board.piece_map()

piece_positions = [ ((x+1)%8 + 1, (x+1)//8) for x in piece_map.keys() ]
piece_types = list(piece_map.values())

# push_san -> push from move string notation
# is_checkmate()
# is_stalemate()
# is_insufficient_material()
# outcome() -> Termination.CHECKMATE

# .turn -> chess.WHITE or chess.BLACK

# Nf3 = chess.Move.from_uci("g1f3")
# board.push(Nf3)  # Make the move
# board.pop()  # Unmake the last move
# is_check() -> this applies to the current side
# board.is_attacked_by(chess.WHITE, chess.E8)
