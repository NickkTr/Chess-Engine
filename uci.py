import sys
import chess
from engine import find_best_move, load_engine_settings


def parse_setoption(tokens: list[str], engine_settings: dict) -> None:
    if "name" not in tokens or "value" not in tokens:
        return

    name_idx = tokens.index("name") + 1
    val_idx = tokens.index("value")
    opt_name = " ".join(tokens[name_idx:val_idx]).lower()
    opt_val = " ".join(tokens[val_idx + 1 :]).strip()

    if opt_name == "non deterministic moves":
        engine_settings["non_deterministic_moves"] = opt_val.lower() == "true"

    elif opt_name == "temperature beta":
        try:
            val = float(opt_val)
            engine_settings["temperature_beta"] = max(2.0, min(20.0, val))
        except ValueError:
            print(f"info string Invalid Temperature_Beta '{opt_val}', keeping {engine_settings['temperature_beta']}", flush=True)

    elif opt_name == "score margin":
        try:
            val = float(opt_val)
            engine_settings["score_margin"] = max(0.0, val)
        except ValueError:
            print(f"info string Invalid Score_Margin '{opt_val}', keeping {engine_settings['score_margin']}", flush=True)

    elif opt_name == "verbose":
        engine_settings["verbose"] = opt_val.lower() == "true"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    board = chess.Board()
    engine_settings = load_engine_settings()

    for raw_line in sys.stdin:
        tokens = raw_line.strip().split()
        if not tokens:
            continue

        cmd = tokens[0]

        if cmd == "uci":
            print("id name MyPythonEngine")
            print("id author YourName")
            print(f"option name Non Deterministic Moves type check default {str(engine_settings['non_deterministic_moves']).lower()}")
            print(f"option name Temperature Beta type string default {engine_settings['temperature_beta']}")
            print(f"option name Score Margin type string default {engine_settings['score_margin']}")
            print(f"option name Verbose type check default {str(engine_settings['verbose']).lower()}")
            print("uciok", flush=True)

        elif cmd == "setoption":
            parse_setoption(tokens, engine_settings)
            print(f"info string configs: {engine_settings}")
            sys.stdout.flush()

        elif cmd == "isready":
            print("readyok", flush=True)

        elif cmd == "ucinewgame":
            board.reset()

        elif cmd == "position":
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
            depth = int(tokens[tokens.index("depth") + 1]) if "depth" in tokens else 4
            best_move = find_best_move(board, depth=depth, settings=engine_settings)
            move_str = best_move.uci() if best_move else "0000"
            print(f"bestmove {move_str}", flush=True)

        elif cmd == "quit":
            break


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()