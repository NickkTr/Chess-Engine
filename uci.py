import sys
import chess
from engine import find_best_move


def main():
    board = chess.Board()

    for raw_line in sys.stdin:
        tokens = raw_line.strip().split()
        if not tokens:
            continue

        cmd = tokens[0]

        if cmd == "uci":
            print("id name MyPythonBot")
            print("id author You")
            print("uciok", flush=True)

        elif cmd == "isready":
            print("readyok", flush=True)

        elif cmd == "ucinewgame":
            board.reset()

        elif cmd == "position":
            # handle "position startpos moves e2e4 e7e5" or "position fen <fen> moves ..."
            if "moves" in tokens:
                moves_idx = tokens.index("moves")
                pos_tokens = tokens[1:moves_idx]
                moves = tokens[moves_idx + 1 :]
            else:
                pos_tokens = tokens[1:]
                moves = []

            if pos_tokens[0] == "startpos":
                board.reset()
            elif pos_tokens[0] == "fen":
                board.set_fen(" ".join(pos_tokens[1:]))

            for uci_move in moves:
                board.push_uci(uci_move)

        elif cmd == "go":
            # parse optional "depth N" command, fallback to 4
            depth = 4
            if "depth" in tokens:
                depth = int(tokens[tokens.index("depth") + 1])

            best_move = find_best_move(board, depth=depth)
            move_str = best_move.uci() if best_move else "0000"
            print(f"bestmove {move_str}", flush=True)

        elif cmd == "quit":
            break


if __name__ == "__main__":
    main()