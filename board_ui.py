import chess
import pygame
from utils import get_board_square, get_square_coords
from dataclasses import dataclass

@dataclass
class SelectedPiece:
    board_x: int
    board_y: int
    piece: chess.Piece
    possible_destinations: list[chess.Square]          # list of squares the piece can move to


class BoardUI:
    SQUARE_MARKER_SIZE_RATIO = 0.3
    MARKER_ALPHA = 0.3
    PROMOTION_PIECES = (
        chess.QUEEN,
        chess.ROOK,
        chess.BISHOP,
        chess.KNIGHT,
    )

    def __init__(
        self, 
        board: chess.Board, 
        pieces_res: dict, 
        W: int, 
        H: int,
        white_is_player: bool = True,
        black_is_player: bool = True
    ):
        self.board = board
        self.pieces_res = pieces_res

        self.W = W
        self.H = H

        self.square_w = W / 8
        self.square_h = H / 8

        # the piece we're dragging (if any)
        self.dragging = False
        self.selected_piece: SelectedPiece = None
        self.pending_promotion: chess.Move | None = None

        self.are_sides_players = {chess.WHITE: white_is_player, chess.BLACK: black_is_player}

        self.__create_square_marker_surface()


    def __create_square_marker_surface(self):
        marker_radius = int(self.square_w * BoardUI.SQUARE_MARKER_SIZE_RATIO / 2)
        marker_surf = pygame.Surface((marker_radius * 2, marker_radius * 2), pygame.SRCALPHA)

        alpha_255 = int(BoardUI.MARKER_ALPHA * 255)
        pygame.draw.circle(marker_surf, (0,0,0,alpha_255), (marker_radius, marker_radius), marker_radius)
        
        self.marker_radius = marker_radius
        self.marker_surf = marker_surf


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


        self.__render_dragged_piece(surf)
        self.__render_promotion_popup(surf)


    def __promotion_popup_rect(self) -> pygame.Rect:
        cell_width = int(self.square_w)
        cell_height = int(self.square_h)
        return pygame.Rect(
            (self.W - 2 * cell_width) // 2,
            (self.H - 2 * cell_height) // 2,
            2 * cell_width,
            2 * cell_height,
        )


    def __render_promotion_popup(self, surf: pygame.Surface):
        if self.pending_promotion is None:
            return

        popup_rect = self.__promotion_popup_rect()
        cell_width = popup_rect.width // 2
        cell_height = popup_rect.height // 2
        popup = pygame.Surface(popup_rect.size, pygame.SRCALPHA)
        popup.fill((35, 35, 35, 240))

        for index, piece_type in enumerate(self.PROMOTION_PIECES):
            column = index % 2
            row = index // 2
            cell_rect = pygame.Rect(
                column * cell_width,
                row * cell_height,
                cell_width,
                cell_height,
            )
            piece_img = self.pieces_res[self.board.turn][piece_type]
            popup.blit(piece_img, piece_img.get_rect(center=cell_rect.center))
            pygame.draw.rect(popup, (220, 220, 220), cell_rect, 1)

        surf.blit(popup, popup_rect)


    def __choose_promotion(self, mouse_x: int, mouse_y: int):
        if self.pending_promotion is None:
            return

        popup_rect = self.__promotion_popup_rect()
        if not popup_rect.collidepoint(mouse_x, mouse_y):
            return

        cell_width = popup_rect.width // 2
        cell_height = popup_rect.height // 2
        column = (mouse_x - popup_rect.left) // cell_width
        row = (mouse_y - popup_rect.top) // cell_height
        piece_type = self.PROMOTION_PIECES[row * 2 + column]
        move = chess.Move(
            self.pending_promotion.from_square,
            self.pending_promotion.to_square,
            promotion=piece_type,
        )

        if move in self.board.legal_moves:
            self.board.push(move)
            self.pending_promotion = None



    def __render_dragged_piece(self, surf: pygame.Surface):
        """ Renders the selected/dragged piece and the highlights for the possible destinations """
        if self.selected_piece is not None:
            # render slots in the available positions
            for destination in self.selected_piece.possible_destinations:
                i,j = get_square_coords(destination)

                # on screen position of the destination
                pos_x = int(self.square_h * (i + 0.5))
                pos_y = int(self.square_w * (7-j + 0.5))
                
                surf.blit(self.marker_surf, (pos_x-self.marker_radius, pos_y-self.marker_radius))


            if self.dragging:
                mx, my = pygame.mouse.get_pos()
                color = self.selected_piece.piece.color
                _type = self.selected_piece.piece.piece_type

                img = self.pieces_res[color][_type]
                surf.blit(img, (mx-self.square_w//2, my-self.square_h//2))        





    def on_mouse_button_down(self, mouse_x: int, mouse_y: int, button):

        if button != 1:
            return

        if self.pending_promotion is not None:
            self.__choose_promotion(mouse_x, mouse_y)
            return

        board_x = int(mouse_x // self.square_w)
        board_y = 7-int(mouse_y // self.square_h)

        if self.selected_piece is not None:
            if self.selected_piece.board_x == board_x and self.selected_piece.board_y == board_y:
                self.selected_piece = None
                return

        square = get_board_square(board_x, board_y)

        piece = self.board.piece_at(square)
        if piece is not None and self.are_sides_players[piece.color]:
            self.dragging = True

            possible_destinations = [
                move.to_square 
                for move in self.board.legal_moves 
                if move.from_square == square
            ]
            
            self.selected_piece = SelectedPiece(board_x, board_y, piece, possible_destinations)
        else:
            self.selected_piece = None
        


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
        legal_moves = list(self.board.legal_moves)

        promotion_move = next(
            (
                legal_move for legal_move in legal_moves
                if legal_move.from_square == start_square
                and legal_move.to_square == destination_square
                and legal_move.promotion is not None
            ),
            None,
        )
        if promotion_move is not None:
            self.pending_promotion = move
            self.selected_piece = None
            self.dragging = False
            return

        if move not in legal_moves and self.selected_piece.piece.piece_type == chess.KING:
            destination_piece = self.board.piece_at(destination_square)
            if destination_piece == chess.Piece(chess.ROOK, self.board.turn):
                is_kingside = chess.square_file(destination_square) > chess.square_file(start_square)
                move = next(
                    (
                        legal_move for legal_move in legal_moves
                        if self.board.is_castling(legal_move)
                        and self.board.is_kingside_castling(legal_move) == is_kingside
                        and destination_square == chess.square(
                            7 if is_kingside else 0,
                            chess.square_rank(start_square),
                        )
                    ),
                    move,
                )

        move_legal = self.board.is_legal(move)

        if move_legal:
            self.board.push(move)
            self.selected_piece = None

        self.dragging = False