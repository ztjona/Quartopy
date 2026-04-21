from ..utils import logger
from ..models import load_bot_class
from .quarto_game import QuartoGame
from ..models import BotAI

import time
import os
from colorama import Fore, Back, Style
from os import path
from tqdm.auto import tqdm

from typing import Any
from collections import defaultdict

builtin_bot_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../bot/")
)


def go_quarto(
    matches: int,
    player1_file: str,
    player2_file: str,
    delay: float = 0,
    params_p1: dict = {},
    params_p2: dict = {},
    verbose: bool = True,
    folder_bots: str = "bot/",
    builtin_bots: bool = False,
    mode_2x2: bool = True,
):
    """Inicia un torneo de Quarto entre dos bots.
    Args:
        matches (int): Número de partidas a jugar.
        player1_path (str): Nombre del script del bot jugador 1 (sin extensión py), debe tener una clase ``Quarto_bot``.
        player2_path (str): Nombre del script del bot jugador 2 (sin extensión py), debe tener una clase ``Quarto_bot``.
        params_p1 (dict): Parámetros adicionales para el bot jugador 1.
        params_p2 (dict): Parámetros adicionales para el bot jugador 2.
        delay (float): Retardo entre movimientos en segundos.
        verbose (bool): Si True, muestra salida detallada de las partidas.
        folder_bots (str): Directorio donde se encuentran los scripts de los bots, default "bot/".
        builtin_bots (bool): Si True, usa bots integrados en lugar de scripts externos.
        match_dir (str): Directorio donde se guardarán las partidas, default "./partidas_guardadas/".
    Returns:
        dict: Resultados del torneo con victorias de cada jugador y empates.
    """

    logger.info(
        f"Iniciando torneo de Quarto con {matches} partidas entre {player1_file} y {player2_file}"
    )
    if builtin_bots:
        logger.info(f"Usando bots integrados: {player1_file} y {player2_file}")
        folder_bots = builtin_bot_folder
    else:
        logger.info(
            f"Usando bots desde scripts: {player1_file} y {player2_file} en la carpeta {folder_bots}"
        )
    
    # --- Player 1
    player1_class = load_bot_class(path.join(folder_bots, f"{player1_file}.py"))
    # Add model path if CNN bot
    if player1_file == "CNN_bot":
        params_p1['model_path'] = "quartopy/CHECKPOINTS/LOSS_APPROACHs_1212-2_only_select/20251212_2206-LOSS_APPROACHs_1212-2_only_select_E_1034.pt"
    player1 = player1_class(**params_p1)

    # --- Player 2
    player2_class = load_bot_class(path.join(folder_bots, f"{player2_file}.py"))
    # Add model path if CNN bot
    if player2_file == "CNN_bot":
        params_p2['model_path'] = "quartopy/CHECKPOINTS/LOSS_APPROACHs_1212-2_only_select/20251212_2206-LOSS_APPROACHs_1212-2_only_select_E_1034.pt"
    player2 = player2_class(**params_p2)

    results = play_games(
        matches=matches,
        player1=player1,
        player2=player2,
        delay=delay,
        verbose=verbose,
        mode_2x2=mode_2x2,
    )
    return results


def play_games(
    matches: int,
    player1: BotAI,
    player2: BotAI,
    delay: float = 0,
    verbose: bool = True,
    PROGRESS_MESSAGE: str = "Playing matches...",
    save_match: bool = True,
    mode_2x2: bool = True,
):
    """Juega un torneo de Quarto entre dos jugadores.
    Args:
        * matches (int): Número de partidas a jugar.
        * player1 (BotAI): Instancia del bot jugador 1.
        * player2 (BotAI): Instancia del bot jugador 2.
        * delay (float): Retardo entre movimientos en segundos.
        * verbose (bool): Si True, muestra salida detallada de las partidas.
        * PROGRESS_MESSAGE (str): Mensaje a mostrar en la barra de progreso.
        * save_match (bool): Si True, guarda el historial de cada partida en CSV.
                    NOTA: Legacy code, ya no se puede usar en entrenamiento.
        * mode_2x2 (bool): Si True, activa el modo de victoria 2x2.
    Returns:
        * matches_data (list): Lista de diccionarios con resultados de cada partida.
        * win_rate (dict): Diccionario con conteo de victorias por jugador y empates.
    """

    # counter of wins and ties
    win_rate: dict[str, int] = defaultdict(lambda: 0)

    # list by match
    matches_data: list[dict[str, Any]] = []

    for match in tqdm(
        range(1, matches + 1),
        desc=PROGRESS_MESSAGE,
        mininterval=0.3,
        miniters=1,
        position=0,
        leave=False,
    ):

        game = QuartoGame(player1=player1, player2=player2, mode_2x2=mode_2x2)
        # -------- PLAYING
        while not game.player_won and not game.game_board.is_full():
            game.play_turn()
            if verbose:
                game.display_boards()

            if delay > 0:
                time.sleep(delay)
            game.cambiar_turno()
        if verbose:
            game.display_end()
        # Aftermath
        if save_match:
            # Exportar historial con número de match
            game.export_history_to_csv(match_number=match)

        win_rate[game.winner_pos] += 1
        matches_data.append(game.to_dict)

    return matches_data, win_rate
