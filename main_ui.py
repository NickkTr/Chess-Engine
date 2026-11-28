import pygame
import chess
import sys
from board_ui import BoardUI
from engine import find_best_move
from concurrent.futures import Future, ProcessPoolExecutor

def load_resources(scr_size: tuple[int,int]):
    scr_w, _ = scr_size
    square_size = (scr_w / 8)
    piece_size_px = int(square_size)
 
    pieces_img = pygame.image.load("./images/chess_pieces.png")
    img_w = pieces_img.get_width()
    img_h = pieces_img.get_height()

    N_ROWS = 6
    N_COLS = 2

    piece_px_width = img_w // N_ROWS
    piece_px_height = img_h // N_COLS

    # dict mapping each piece to each properly scaled image of that piece
    pieces_imgs = {
        chess.WHITE: {},
        chess.BLACK: {}
    }

    pieces_order = [ chess.KING, chess.QUEEN, chess.BISHOP, chess.KNIGHT, chess.ROOK, chess.PAWN ]

    for i in range(2):
        is_white = (i==0)
        side = chess.WHITE if is_white else chess.BLACK

        for j in range(6):
            piece_img = pieces_img.subsurface(j * piece_px_width, i * piece_px_height, piece_px_width, piece_px_height)
            piece_img = pygame.transform.smoothscale(piece_img, (piece_size_px, piece_size_px))
            piece_type = pieces_order[j]
            
            pieces_imgs[side][piece_type] = piece_img

    return pieces_imgs





def main():
    W,H = 600, 600
    scr_size = (W,H)

    pieces_textures = load_resources(scr_size)

    pygame.init()
    win = pygame.display.set_mode(scr_size)
    surf = pygame.surface.Surface(scr_size)

    board_background = pygame.image.load("./images/board_background.png")
    board_background = pygame.transform.scale(board_background, scr_size)

    board = chess.Board()
    board_ui = BoardUI(board, pieces_textures, W, H, black_is_player=False)

    executor = ProcessPoolExecutor(max_workers=1)
    AI_COLOR = chess.BLACK
    ai_future: Future | None = None

    should_render = True
    
    clock = pygame.time.Clock()

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                board_ui.on_mouse_button_down(mouse_x, mouse_y, event.button)
                should_render = True

            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_x, mouse_y = event.pos
                board_ui.on_mouse_button_up(mouse_x, mouse_y, event.button)
                should_render = True

            elif event.type == pygame.MOUSEMOTION and board_ui.dragging:
                should_render = True


        # Get the move if the AI thread is done calculating it
        if not board.is_game_over() and board.turn == AI_COLOR:
            if ai_future is None:
                ai_future = executor.submit(find_best_move, board.copy(), depth=4)

            elif ai_future.done():
                best_move = ai_future.result()
                if best_move is not None:
                    board.push(best_move)
                    should_render = True

                ai_future = None

        if not should_render:
            continue
        
        surf.blit(board_background, (0,0))
        board_ui.render(surf)



        win.blit(surf, (0,0))
        pygame.display.flip()
        should_render = False
        clock.tick(60)



if __name__ == '__main__':
    main()