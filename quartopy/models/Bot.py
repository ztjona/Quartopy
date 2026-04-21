# -*- coding: utf-8 -*-
from ..game.piece import Piece

from abc import ABC, abstractmethod


class BotAI(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def select(self, game: "QuartoGame", ith_option: int, *args, **kwargs) -> Piece:  # type: ignore
        """Selecciona una pieza para el otro jugador.
        ## Parameters
        ``game``: QuartoGame
        ``ith_option``: int iésima opción preferida
        """
        pass

    @abstractmethod
    def place_piece(
        self, game: "QuartoGame", piece: Piece, ith_option: int, *args, **kwargs  # type: ignore
    ) -> tuple[int, int]:
        """Coloca la ``piece`` en el tablero.
        ## Parameters
        ``game``: QuartoGame
        ``piece``: Piece
        ``ith_option``: int iésima opción preferida
        ## Return
        ``row``: int
        ``col``: int
        """
        pass
