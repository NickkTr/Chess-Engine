import chess
import pygame
from utils import get_board_square
from dataclasses import dataclass

@dataclass
class SelectedPiece:
    board_x: int
    board_y: int
    piece: chess.Piece


class BoardUI:

    def __init__(self, board: chess.Board, pieces_res: dict, W: int, H: int):
        self.board = board
        self.pieces_res = pieces_res

        self.W = W
        self.H = H

        self.square_w = W / 8
        self.square_h = H / 8

        # the piece we're dragging (if any)
        self.dragging = False
        self.selected_piece: SelectedPiece = None



    def render(self, surf: pygame.Surface):
        
        for i in range(8):
            for j in range(8):
                # on screen position
                pos_x = int(self.square_h * i)
                pos_y = int(self.square_w * (7-j))

                square = get_board_square(i, j)

                piece = self.board.piece_at(square)

                is_pieced_dragged = False           # whether the piece at the current position is being dragged
                if self.dragging and self.selected_piece is not None:
                    is_pieced_dragged = (self.selected_piece.board_x == i and self.selected_piece.board_y == j)

                if piece is None or is_pieced_dragged:
                    continue
                
                piece_img = self.pieces_res[piece.color][piece.piece_type]
                surf.blit(piece_img, (pos_x, pos_y))


        if self.selected_piece is not None and self.dragging:
            mx, my = pygame.mouse.get_pos()
            color = self.selected_piece.piece.color
            _type = self.selected_piece.piece.piece_type
            # print('white' if color == chess.WHITE else 'black')

            img = self.pieces_res[color][_type]
            surf.blit(img, (mx-self.square_w//2, my-self.square_h//2))        



    def on_mouse_button_down(self, mouse_x: int, mouse_y: int, button):

        # do nothing if it's not the left mouse button that's been pressed
        if not button != 3: 
            return

        board_x = int(mouse_x // self.square_w)
        board_y = 7-int(mouse_y // self.square_h)

        square = get_board_square(board_x, board_y)

        row_letter = ord('a') + board_x
        row_letter = chr(row_letter)
        print(row_letter + str(board_y + 1))

        piece = self.board.piece_at(square)
        if piece is not None:
            self.dragging = True
            self.selected_piece = SelectedPiece(board_x, board_y, piece)
            print(f"Selected piece: {piece} | color: {'white' if piece.color == chess.WHITE else 'black'}")
        
        


    def on_mouse_button_up(self, mouse_x: int, mouse_y: int, button):

        if button != 1:
            return

        if self.selected_piece is None:
            return

        board_x = int(mouse_x // self.square_w)
        board_y = 7-int(mouse_y // self.square_h)

        start_square = get_board_square(self.selected_piece.board_x, self.selected_piece.board_y)
        destination_square = get_board_square(board_x, board_y)

        move = chess.Move(start_square, destination_square)
        move_legal = self.board.is_legal(move)
        print(f"Move is legal: {move_legal}")

        if move_legal:
            self.board.push(move)
            self.selected_piece = None

        # TODO: move the piece from the original position to the one that was it dragged to
        self.dragging = False