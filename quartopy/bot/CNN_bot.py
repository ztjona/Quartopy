# -*- coding: utf-8 -*-

"""
CNN_bot - Bot based in CNN to play Quarto
"""

"""
Python 3
26 / 05 / 2025
@author: z_tjona

"I find that I don't understand things unless I try to program them."
-Donald E. Knuth
"""

from quartopy.models.CNN_uncoupled import QuartoCNN

from quartopy import BotAI, Piece, QuartoGame

from utils.logger import logger
import numpy as np
import torch
import torch.nn as nn # Added for type hinting nn.Module
import os
from tensordict import TensorDict

logger.debug("Loading CNN_bot...")


class CNNBot(BotAI):
    @property
    def name(self) -> str:
        if hasattr(self, "_name"): # Check for _name attribute
            return self._name
        elif hasattr(self, "model_path") and self.model_path:
            return f"CNN_bot|{os.path.basename(self.model_path)}"
        elif hasattr(self, "model_name") and self.model_name:
            return f"CNN_bot|{self.model_name}"
        else:
            return "CNN_bot|random_weights"

    def __init__(
        self,
        name: str = "CNN_bot", # Added name argument
        *,
        model_path: str | None = None,
        model: nn.Module | None = None, # Changed type hint
        model_class: type = QuartoCNN, # Changed type hint
        deterministic: bool = True,
        temperature: float = 0.1,
    ):
        """
        Initializes the CNN bot.
        ## Parameters
        ``name``: str
            Name of the bot. Defaults to "CNN_bot".
        ``model_path``: str | None
            Path to the pre-trained model. If None and ``model`` is None, random weights are loaded.

        ``model``: nn.Module | None
            An instance of a model derived from nn.Module. If provided, it will be used instead of loading from a file.
            Cannot be used together with ``model_path``.

        ``model_class``: type
            The model class to instantiate when loading from ``model_path``.
            Defaults to QuartoCNN if not provided.
            Only used when ``model_path`` is provided.

        ``deterministic``: bool
            If True, the model will select the most probable action. Default is True.

        ``temperature``: float
            Controls the randomness of the selection. Higher values lead to more exploration.
            Only applicable if ``DETERMINISTIC`` is False. Default is 0.1.

        ## Attributes
        ``DETERMINISTIC``: bool
            If True, the model will select the most probable action.
        ``TEMPERATURE``: float
            Controls the randomness of the selection. Higher values lead to more exploration. Only applicable if ``DETERMINISTIC`` is False.
        """
        super().__init__(name=name) # Pass name to super
        self._name = name # Store name
        logger.debug(f"CNN_bot initialized with name: {self._name}")

        # Validate input parameters
        assert not (
            model_path is not None and model is not None
        ), "Cannot provide both ``model_path`` and ``model`` instance. Choose one."

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') # Define device here

        if model_path:
            # Use provided model_class
            logger.debug(
                f"Loading model from {model_path} using {model_class.__name__}"
            )
            # Assuming model_class (QuartoCNN) has a .from_file() method
            self.model = model_class.from_file(model_path, device=self.device) # Pass device to from_file
            self.model_path = model_path # Store full path
            self.model_name = os.path.basename(model_path)


        elif model:
            assert isinstance(
                model, nn.Module
            ), "Provided model must be a derived class of ``nn.Module``." # Changed type check

            self.model = model
            # Removed self.model_name = model.name as nn.Module doesn't have a name property by default
            logger.debug(f"Using provided model instance {type(self.model).__name__}")
            self.model_name = type(self.model).__name__

        else:
            logger.debug("Loading model with random weights")
            self.model = model_class()
            self.model_name = "random_weights"


        # Move model to appropriate device
        self.model.to(self.device) # Use self.device
        logger.debug(f"Model loaded successfully on device: {self.device}")

        self._recalculate = True  # Recalculate the model on each turn
        self.selected_piece: Piece
        self.board_position: tuple[int, int]
        # If True, the model will select the most probable action
        self.DETERMINISTIC: bool = deterministic

        # Controls the randomness of the selection. Higher values lead to more exploration.
        # Only applicable if ``DETERMINISTIC`` is False.
        self.TEMPERATURE: float = temperature

    # ####################################################################
    def calculate(
        self,
        game: QuartoGame,
        ith_try: int = 0,
    ):
        """Calculates the move for the bot based on the current board state and selected piece.
        ## Parameters
        ``game``: QuartoGame
            The current game instance.
        ``ith_try``: int
            The index of the current attempt to select or place a piece.
        ## Returns

        """
        if self._recalculate:
            board_matrix = game.game_board.encode()
            if isinstance(game.selected_piece, Piece):
                piece_onehot = game.selected_piece.vectorize_onehot()
                piece_onehot = piece_onehot.reshape(1, -1)  # Reshape to (1, 16)
            else:
                piece_onehot = np.zeros((1, 16), dtype=float)

            # Create tensors and move to model's device
            board_tensor = torch.from_numpy(board_matrix).float().to(self.device) # Use self.device
            piece_tensor = torch.from_numpy(piece_onehot).float().to(self.device) # Use self.device

            self.board_pos_onehot_cached, self.select_piece_onehot_cached = (
                self.model.predict(
                    board_tensor,
                    piece_tensor,
                    TEMPERATURE=self.TEMPERATURE,
                    DETERMINISTIC=self.DETERMINISTIC,
                )
            )
            batch_size = self.board_pos_onehot_cached.shape[0]
            assert batch_size == 1, f"Expected batch size of 1, got {batch_size}."

            self._recalculate = False  # Do not recalculate until the next turn

        # load from cached values
        # 0 for batch size is 1
        _idx_piece: int = self.select_piece_onehot_cached[0, ith_try].item()  # type: ignore
        selected_piece = Piece.from_index(_idx_piece)

        _idx_board_pos: int = self.board_pos_onehot_cached[0, ith_try].item()  # type: ignore
        board_position = game.game_board.get_position_index(_idx_board_pos)

        return board_position, selected_piece

    def select(
        self,
        game: QuartoGame,
        ith_option: int = 0,
        *args,
        **kwargs,
    ) -> Piece:
        """Selects a piece for the other player."""

        for i in range(16): # Iterate through all possible options
            _, selected_piece = self.calculate(game, i)
            if game.storage_board.find_piece(selected_piece):
                return selected_piece
        
        logger.error("CNNBot could not find an available piece to select.")
        raise RuntimeError("CNNBot could not find an available piece to select.")

    def place_piece(
        self,
        game: QuartoGame,
        piece: Piece,
        ith_option: int = 0,
        *args,
        **kwargs,
    ) -> tuple[int, int]:
        """Places the selected piece on the game board at a random valid position."""
        if ith_option == 0:
            self._recalculate = True
        
        for i in range(16):  # Iterate through all possible options
            board_position, _ = self.calculate(game, i)
            row, col = board_position
            if game.game_board.is_empty(row, col):
                return board_position
        
        raise RuntimeError("CNNBot could not find a valid move.")

    def evaluate(self, exp_batch: TensorDict) -> tuple[torch.Tensor, torch.Tensor]:
        """Evaluates a batch of experiences and returns the Q-values for the taken actions.
        This is useful for tracking how action-values evolve during training.

        ## Parameters
        ``exp_batch``: TensorDict
            Batch of experiences containing:
            - state_board: Board states (batch_size, 16, 4, 4)
            - state_piece: Piece states (batch_size, 16)
            - action_place: Placement actions taken (batch_size,). -1 for first move.
            - action_sel: Selection actions taken (batch_size,). -1 for terminal states.

        ## Returns
        ``q_place``: torch.Tensor
            Q-values for the placement actions taken (batch_size,)
        ``q_select``: torch.Tensor
            Q-values for the selection actions taken (batch_size,)

        ## Note
        Terminal states (winning moves) have action_sel=-1, which will cause
        incorrect indexing. The caller should handle this appropriately.
        """
        state_board: torch.Tensor = exp_batch["state_board"]
        state_piece: torch.Tensor = exp_batch["state_piece"]
        action_place = exp_batch["action_place"].to(torch.int64)
        action_sel = exp_batch["action_sel"].to(torch.int64)

        # Get Q-values for all actions
        self.model.eval()
        with torch.no_grad():
            # Move tensors to model device
            state_board = state_board.to(self.device)
            state_piece = state_piece.to(self.device)
            qav_board, qav_piece = self.model.forward(state_board, state_piece)

        # Extract Q-values for the actual actions taken
        batch_indices = torch.arange(state_board.shape[0])
        q_place = qav_board[batch_indices, action_place]
        q_select = qav_piece[batch_indices, action_sel]

        return q_place, q_select
