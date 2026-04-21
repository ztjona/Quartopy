from .board import Board
from ..models.Bot import BotAI
from .piece import Piece
from ..utils.logger import logger

from os import path, makedirs
from datetime import datetime
import csv
from colorama import Fore, Back


logger.debug(f"{__name__} importado correctamente")


class QuartoGame:

    def __init__(self, player1: BotAI, player2: BotAI, mode_2x2: bool = False):
        self.MAX_TRIES = 16  # todos los intentos posibles
        self.TIE = "Tie"
        self.selected_piece: Piece | int = 0
        self.game_board = Board("Game Board", False, 4, 4)
        self.storage_board = Board("Storage Board", True, 2, 8)
        self.turn = True  # True for player 1, False for player 2
        self.pick = True  # True for picking phase, False for placing phase
        self.move_history: list[dict[str, str]] = []
        self.mode_2x2 = mode_2x2

        # Configuración de jugadores
        self.player1 = player1
        self.player2 = player2

        self.player_won: bool = False
        self.match_result: str = self.TIE
        self.valid_moves = []
        self.winner_pos: str = self.TIE

    def get_current_player(self):
        return self.player1 if self.turn else self.player2

    def get_next_player(self):
        return self.player2 if self.turn else self.player1

    @property
    def player_turn(self):
        return "Player 1" if self.turn else "Player 2"

    def play_turn(self):
        current_player = self.get_current_player()

        if self.pick:  # Selección de pieza
            valid_selection = False
            for n_tries in range(self.MAX_TRIES):
                selected_piece: Piece = current_player.select(self, n_tries)

                if coord := self.storage_board.find_piece(selected_piece):
                    _r_storage, _c_storage = coord  # en storage_board
                    valid_selection = True
                    break
                logger.debug(
                    f"Intento {n_tries + 1}: Seleccionando pieza {selected_piece}"
                )

            if not valid_selection:
                raise ValueError(f"Invalid selection after {self.MAX_TRIES} tries")

            self.storage_board.remove_piece(_r_storage, _c_storage)
            self.selected_piece = selected_piece

            move_info = {
                "player_name": current_player.name,
                "player_pos": self.player_turn,
                "action": "selected",
                "piece": self.selected_piece.__repr__(verbose=True),
                "piece_index": self.selected_piece.index(),
                # "position": None,
                # "position_index": -1,
                "attempt": n_tries + 1,
                # "board": "",
            }
            self.move_history.append(move_info)

        else:  # Colocación de pieza
            valid_placement = False
            piece: Piece = self.selected_piece  # type: ignore
            assert isinstance(
                piece, Piece
            ), "Error, la lógica debería dar un tipo pieza"
            assert (
                piece not in self.game_board
            ), "Error, la pieza ya está en el tablero de juego"

            for n_tries in range(self.MAX_TRIES):
                row, col = current_player.place_piece(self, piece, n_tries)

                if self.game_board.is_empty(row, col):
                    valid_placement = True
                    break
                logger.debug(
                    f"Intento {n_tries + 1}: Colocando pieza en ({row}, {col})"
                )

            if not valid_placement:
                raise ValueError(f"Invalid selection after {self.MAX_TRIES} tries")

            self.game_board.put_piece(piece, row, col)

            move_info = {
                "player_name": current_player.name,
                "player_pos": self.player_turn,
                "action": "placed",
                # "piece": piece.__repr__(verbose=False),
                # "piece_index": piece.index(),
                "position": (row, col),
                "position_index": self.game_board.pos2index(row, col),
                "attempt": n_tries + 1,
                "board_after": self.game_board.serialize(),
            }
            self.move_history.append(move_info)

            # Verificar ganador
            if self.game_board.check_win(mode_2x2=self.mode_2x2):
                self.match_result = current_player.name
                self.winner_pos = self.player_turn
                self.player_won = True

            elif self.game_board.is_full():
                self.match_result = self.TIE
                self.winner_pos = self.TIE

            # self.selected_piece = 0

    def select_and_remove_piece(self, piece: Piece):
        """Finds a piece on the storage board, removes it, and sets it as the selected piece."""
        if coord := self.storage_board.find_piece(piece):
            r, c = coord
            self.storage_board.remove_piece(r, c)
            self.selected_piece = piece
            return True
        else:
            logger.error(f"Attempted to select piece {piece} not found in storage.")
            return False

    def cambiar_turno(self):
        """Cambia el turno y la fase del juego"""
        # Cambiar turno
        if self.pick:
            self.turn = not self.turn
        self.pick = not self.pick


    def export_history_to_csv(
        self, output_folder: str = "./partidas_guardadas/", match_number: int = 1, winner: str = "Tie"
    ):
        """Exporta el historial a un CSV con nombre que incluye match, fecha y hora"""
        # Crear directorio si no existe
        makedirs(output_folder, exist_ok=True)

        # Generar nombre de archivo con formato: MatchX_YYYY-MM-DD_HH-MM-SS.csv
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f"{current_time}_match{match_number:03d}.csv"

        filepath = path.join(output_folder, filename)

        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Movimiento",
                    "Jugador",
                    "Acción",
                    "Pieza",
                    "Pieza Index",
                    "Posición",
                    "Posición Index",
                    "Intento",
                    "Tablero",
                ]
            )

            # Escribir movimientos
            for i, move in enumerate(self.move_history, start=1):
                piece = move.get("piece", "N/A")
                piece_index = move.get("piece_index", "N/A")
                position = move.get("position", "N/A")
                position_index = move.get("position_index", "N/A")
                board = move.get("board_after", "N/A")
                writer.writerow(
                    [
                        i,
                        move["player_name"],
                        move["action"],
                        piece,
                        piece_index,
                        position,
                        position_index,
                        move["attempt"],
                        board,
                    ]
                )
            
            writer.writerow([])
            writer.writerow(["Ganador", winner])

        return filepath

    def display_boards(self, exclude_footer: bool = False):
        """Muestra ambos tableros con formato mejorado"""

        current_player = self.get_current_player()

        action = "SELECCIONA PIEZA" if self.pick else "=" * 40 + "\nCOLOCA PIEZA"
        print(f"\n({self.player_turn}) [{current_player.name}] {action}", end="")

        if self.pick:
            # Tablero de almacenamiento
            back = Back.YELLOW
            color = Fore.BLACK
            print(f" ->{back}{color}({self.selected_piece})")
            print("Piezas en almacenamiento:")
            self.storage_board.print_board(self.selected_piece)
        else:
            # Tablero de juego principal
            print("\nTablero de juego:")
            self.game_board.print_board(self.selected_piece)

        # Pieza seleccionada
        if self.selected_piece:
            pass
        # Movimientos válidos
        if not self.pick and hasattr(self, "valid_moves") and self.valid_moves:
            pass
        if exclude_footer:
            return

    def display_end(self):
        """Muestra el resultado final de la partida"""
        print("\n" + "=" * 40)
        if self.player_won:
            winner = self.get_current_player()
            print(
                f"{Fore.GREEN}¡{self.player_turn} [{winner.name}] ha ganado la partida!{Fore.RESET}"
            )
        else:
            print(f"{Fore.YELLOW}¡La partida ha terminado en empate!{Fore.RESET}")
        print("=" * 40 + "\n")

    @property
    def to_dict(self):
        """Converts the object to a dictionary including only data required for training."""
        return {
            "move_history": self.move_history,
            "Player 1": self.player1.name,
            "Player 2": self.player2.name,
            "result": self.winner_pos,
            "winner": self.match_result,
        }
