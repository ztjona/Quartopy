from .piece import Piece
from .piece import Coloration, Shape, Size, Hole

import numpy as np
from colorama import Fore, Style, Back

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class Board:
    def __init__(self, name: str, storage: bool, rows, cols):
        self.name = name
        self.storage = storage  # Cuando True crea un board con las piezas disponibles
        self.board: list[list[Piece | int]] = [
            [0 for _ in range(cols)] for _ in range(rows)
        ]
        self.rows: int = rows
        self.cols: int = cols
        self.last_move: tuple[int, int] | None = None  # (row, col) of last move

        if self.storage:
            self.__init_pieces()

    def __init_pieces(self):
        """Crea un board con todas las piezas posibles"""
        row = 0
        for si in Size:
            col = 0
            for c in Coloration:
                for sh in Shape:
                    for h in Hole:
                        self.board[row][col] = Piece(si, c, sh, h)
                        col += 1
            row += 1

    def get_piece(self, row, col) -> Piece:
        """Retorna la pieza en la posición (row, col) del tablero.
        Se asume que la posición es válida.
        Debe retornar Piece"""
        assert isinstance(
            self.board[row][col], Piece
        ), "No se puede hacer get_piece en una posición vacía"
        return self.board[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        """Retorna True si la posición (row, col) está vacía (0)"""
        return self.board[row][col] == 0

    def find_piece(self, piece: Piece) -> tuple[int, int] | None:
        """Busca una pieza en el tablero y retorna su posición (row, col)
        Si no la encuentra, retorna None"""
        if isinstance(piece, Piece):
            for row in range(self.rows):
                for col in range(self.cols):
                    if self.board[row][col] == piece:
                        return row, col
            return None
        else:
            raise ValueError("El item debe ser una pieza")

    def remove_piece(self, row: int, col: int):
        """Elimina una pieza del tablero.
        Solo es válido cuando ``storage`` = True"""
        assert (
            self.storage
        ), "Solo se puede eliminar piezas de un tablero de tipo storage"

        assert isinstance(self.board[row][col], Piece), "El item debe ser una pieza"

        self.board[row][col] = 0

    def put_piece(self, piece: Piece | int, row, col):
        # Solo asignar si es una Pieza o 0 (vacío)
        if isinstance(piece, Piece):  # or piece == 0:
            self.board[row][col] = piece
            self.last_move = (row, col)
        else:
            raise ValueError("Solo se pueden colocar objetos Piece o 0 (vacío)")

    def check_win(self, mode_2x2: bool = False) -> bool:
        """Returns True if there is a winning condition on the board.
        False otherwise.
        A winning condition is met when there is a row, column, or diagonal
        where all pieces share at least one common attribute (size, coloration,
        shape, or hole).
        It only analyzes around the last placed piece.
        It assumes previous position was not winning.
        # Parameters
        * mode_2x2 (bool): If True, checks for 2x2 square winning condition.
            Default is False.
        """
        assert self.last_move is not None, "last_position should not be None here"

        row, col = self.last_move

        # Check the row of the last placed piece
        if self.__is_winning_line(self.board[row]):
            return True

        # Check the column of the last placed piece
        column_pieces = [self.board[r][col] for r in range(self.rows)]
        if self.__is_winning_line(column_pieces):
            return True

        # Check main diagonal if the piece is on it
        if row == col:
            main_diagonal_pieces = [self.board[i][i] for i in range(self.rows)]
            if self.__is_winning_line(main_diagonal_pieces):
                return True

        # Check anti-diagonal if the piece is on it
        if row + col == self.cols - 1:
            anti_diagonal_pieces = [
                self.board[i][self.cols - 1 - i] for i in range(self.rows)
            ]
            if self.__is_winning_line(anti_diagonal_pieces):
                return True

        # Check squares
        if mode_2x2:
            # Se evalúan las 4 posibles posiciones del cuadrado 2x2
            # Cada square está conformado por las posiciones
            # (r-1, c-1)   (r-1, c)
            # (r  ,   c)   (r  , c)
            # r itera de [row, row+1]
            # c itera de [col, col+1]

            for r in range(row, row + 2):
                for c in range(col, col + 2):
                    # check square only if it fits in the board
                    if r - 1 < 0 or c - 1 < 0:
                        continue
                    if r >= self.rows or c >= self.cols:
                        continue

                    square_pieces = [
                        self.board[r - 1][c - 1],
                        self.board[r - 1][c],
                        self.board[r][c - 1],
                        self.board[r][c],
                    ]
                    if self.__is_winning_line(square_pieces):
                        return True
        return False

    def is_full(self):
        for row in range(self.rows):
            if 0 in self.board[row]:
                return False
        return True

    def __is_winning_line(self, pieces):
        if 0 in pieces:
            return False
        p = pieces[0]
        ho, si, sh, co = True, True, True, True
        for piece in pieces:
            ho = p.hole == piece.hole and ho
            si = p.size == piece.size and si
            sh = p.shape == piece.shape and sh
            co = p.coloration == piece.coloration and co
        return ho or si or sh or co

    def __check_all_lines(self):
        # Check rows
        for row in range(self.rows):
            if not (0 in self.board[row]):
                if self.__is_winning_line(self.board[row]):
                    return True

        # Check columns
        for col in range(self.cols):
            pieces = []
            for row in range(self.rows):
                pieces.append(self.board[row][col])
            if not (0 in pieces):
                if self.__is_winning_line(pieces):
                    return True

        # Check diagonals (only if square board)
        if self.cols == self.rows:
            pieces = []
            pieces2 = []
            for col in range(self.cols):
                pieces.append(self.board[col][col])
                pieces2.append(self.board[col][self.cols - col - 1])
            if not (0 in pieces):
                if self.__is_winning_line(pieces):
                    return True
            if not (0 in pieces2):
                if self.__is_winning_line(pieces2):
                    return True
        return False

    def get_valid_pieces(self):
        moves: list[Piece] = []
        for row in range(self.rows):
            for col in range(self.cols):
                piece = self.board[row][col]
                if self.storage:
                    if piece != 0:
                        # Piezas que están en storage
                        moves.append(piece)  # type: ignore
                else:
                    if piece == 0:
                        # Espacios vacíos
                        pass
        return moves

    def get_valid_moves(self):
        moves: list[tuple[int, int]] = []
        for row in range(self.rows):
            for col in range(self.cols):
                piece = self.board[row][col]
                if self.storage:
                    if piece != 0:
                        # Piezas que están en storage
                        moves.append((row, col))
                else:
                    if piece == 0:
                        # Espacios vacíos
                        moves.append((row, col))
        return moves

    def __repr__(self):
        s = f"{self.name}:\n"
        for x in range(self.rows):
            for y in range(self.cols):
                s += (
                    ((str(self.board[x][y]) + " "))
                    if self.board[x][y] != 0
                    else "---- "
                )
            s += "\n"
        return s

    ####################################################################
    def to_matrix(self):
        """Convierte el tablero en una matriz de dimensiones
        (batch=1, dims, rows, cols)
        """

        # dims (Tamaño, Color, Forma, Hueco)
        B = np.zeros((1, 4, self.rows, self.cols))
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]

                if isinstance(piece, Piece):
                    B[:, :, r, c] = piece.vectorize()
                # else:
                # continue

        return B

    # ##############################################################
    def __contains__(self, item: Piece):
        """Retorna True si el item es una pieza del tablero"""
        if isinstance(item, Piece):
            for row in range(self.rows):
                for col in range(self.cols):
                    if self.board[row][col] == item:
                        return True
            return False
        else:
            raise ValueError("El item debe ser una pieza")

    @staticmethod
    # ##############################################################
    def to_matrix_batch(boards: list["Board"]):
        """Convierte una lista de tableros en una matriz de dimensiones
        (batch, dims, rows, cols)

        Asume todos los tableros tienen el mismo tamaño.
        """
        B = np.zeros((len(boards), 4, boards[0].rows, boards[0].cols))
        for i, board in enumerate(boards):
            B[i, :, :, :] = board.to_matrix()
        return B

    def print_board(self, piece_highlight: Piece | int = 0):
        """Método auxiliar para imprimir un tablero con formato"""

        # Encabezado de columnas
        print("    " + "      ".join(str(i) for i in range(self.cols)))

        # Borde superior
        print("  ╔" + "╦".join(["══════"] * self.cols) + "╗")

        for row in range(self.rows):
            # Contenido de la fila
            row_str = f"{row} ║"
            for col in range(self.cols):
                piece = self.board[row][col]
                if isinstance(piece, Piece):
                    if piece == piece_highlight:
                        # Resaltar la pieza seleccionada
                        back = Back.YELLOW
                    else:
                        back = Back.RESET
                    color = (
                        Fore.RED if piece.coloration == Coloration.BLACK else Fore.BLUE
                    )
                    row_str += f" {back}{color}{piece}{Style.RESET_ALL} ║"
                else:
                    row_str += "      ║"
            print(row_str)

            # Borde entre filas
            if row < self.rows - 1:
                print("  ╠" + "╬".join(["══════"] * self.cols) + "╣")

        # Borde inferior
        print("  ╚" + "╩".join(["══════"] * self.cols) + "╝")

    # ####################################################################
    def serialize(self):
        """Convierte el tablero en una cadena de texto serializada de cadena de bits.
        ## Return
        str representación booleana del tablero.
        """

        return "".join(str(int(x)) for x in self.encode().flatten())

    @staticmethod
    # ####################################################################
    def deserialize(serialized: str, rows: int = 4, cols: int = 4):
        """Crea una matriz del tablero (1-16-4-4) a partir de una cadena de texto serializada de cadena de bits.
        ## Parameters
        ``serialized``: str representación booleana del tablero.
        ``rows``: int número de filas del tablero.
        ``cols``: int número de columnas del tablero.
        ## Return
        ``matrix``: np.array (1, 16, 4, 4) con one-hot encoded de las piezas del tablero de boolean.
        """
        if serialized == "0" or serialized == -1:
            # Si la cadena es "0", retorna una matriz vacía
            return np.zeros((16, rows, cols), dtype=np.float32)
        assert len(serialized) == rows * cols * 16, ValueError(
            f"Serialized string length {len(serialized)} does not match expected size {rows * cols * 16}"
        )
        v = np.array([list(map(int, serialized))], dtype=np.float32)
        matrix = v.reshape((16, rows, cols))

        return matrix

    # ####################################################################
    def encode(self):
        """Convierte el tablero en una matriz (1-16-4-4)
        ## Return
        ``matrix``: np.array (1, 16, 4, 4 con one-hot encoded de las piezas del tablero de boolean.

        """
        matrix = np.zeros((1, 16, self.rows, self.cols), dtype=bool)
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if isinstance(piece, Piece):
                    matrix[0, :, r, c] = piece.vectorize_onehot()
        return matrix

    # ####################################################################
    @staticmethod
    def serialized_2_board(
        serialized: str, name: str = "Deserialized", rows: int = 4, cols: int = 4
    ) -> "Board":
        """Convierte una cadena de texto serializada de cadena de bits en un tablero.
        ## Parameters
        ``serialized``: str representación booleana del tablero.
        ``name``: str nombre del tablero.
        ``rows``: int número de filas del tablero.
        ``cols``: int número de columnas del tablero.
        ## Return
        ``board``: Board con las piezas del tablero.
        """
        matrix = Board.deserialize(serialized, rows, cols)
        board = Board(name, storage=False, rows=rows, cols=cols)

        for r in range(rows):
            for c in range(cols):
                piece_vector = matrix[:, r, c]
                if np.any(piece_vector):
                    piece = Piece.from_onehot(piece_vector)
                    board.put_piece(piece, r, c)
        return board

    @staticmethod
    # ####################################################################
    def pos_index2vector(index: int, rows: int = 4, cols: int = 4) -> np.ndarray:
        """Convierte una posición en un vector one-hot encoded de tamaño (rows*cols, ).

        ## Parameters
        * ``index``: int índice lineal (0 a rows*cols-1).
        En caso de -1, retorna un vector vacío.
        * ``rows``: int número de filas del tablero
        * ``cols``: int número de columnas del tablero

        ## Return
        ``vector``: np.array (rows*cols, ) con one-hot encoded de la posición.
        """
        if index < -1 or index >= rows * cols:
            raise IndexError("Índice fuera de rango del tablero")

        vector = np.zeros((rows * cols,), dtype=np.float32)
        if index == -1:
            # Si el índice es -1, retorna un vector vacío
            return vector
        vector[index] = True
        return vector

    # ####################################################################
    @staticmethod
    def get_position_index(index: int, rows: int = 4, cols: int = 4) -> tuple[int, int]:
        """Convierte un índice lineal en una posición (row, col) del tablero.

        ## Parameters

        ``index``: int índice lineal (0 a rows*cols-1)
        ## Return

        ``(row, col)``: tuple de enteros con la posición en el tablero.
        """
        if index < 0 or index >= rows * cols:
            raise IndexError("Índice fuera de rango del tablero")
        row = index // cols
        col = index % cols

        return (row, col)

    # ####################################################################
    def pos2index(self, row: int, col: int) -> int:
        """Convierte una posición (row, col) en un índice lineal del tablero.
        ## Parameters

        ``row``: int fila del tablero
        ``col``: int columna del tablero
        ## Return

        ``index``: int índice lineal (0 a rows*cols-1)
        """
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            raise IndexError("Posición fuera de rango del tablero")

        index = row * self.cols + col
        return index

    def plot(self, title: str = "Board", ax=None, show: bool = True):
        """Método auxiliar para dibujar el tablero

        Parameters
        ----------
        title : str
            Título del tablero
        ax : matplotlib.axes.Axes, optional
            Eje donde dibujar. Si es None, crea una nueva figura.
        show : bool
            Si True, muestra la figura. Si False, solo retorna el eje.

        Returns
        -------
        ax : matplotlib.axes.Axes
            El eje con el tablero dibujado
        """
        # Create figure and axis if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
            created_fig = True
        else:
            created_fig = False

        # Set title
        ax.set_title(title, fontweight="bold")

        # Set axis limits and labels
        ax.set_xlim(-0.5, self.cols - 0.5)
        ax.set_ylim(-0.5, self.rows - 0.5)
        ax.set_xticks(range(self.cols))
        ax.set_yticks(range(self.rows))
        ax.set_xticklabels(range(self.cols))
        ax.set_yticklabels(range(self.rows))
        ax.invert_yaxis()  # Invert y-axis to match board orientation

        # Add grid
        ax.grid(True, linewidth=1.5, color="gray", alpha=0.3)

        # Plot pieces
        for r in range(self.rows):
            for c in range(self.cols):
                piece = self.board[r][c]
                if isinstance(piece, Piece):
                    # Determine color based on piece coloration
                    color = (
                        "black"
                        if piece.coloration == Coloration.BLACK
                        else "dodgerblue"
                    )

                    # Build text representation with proper case
                    # T=TALL (all uppercase), L=LITTLE (all lowercase)
                    # K=BLACK, W=WHITE
                    # R=CIRCLE (circle), Q=SQUARE (square)
                    # H=WITH_HOLE (underline), N=WITHOUT (no underline)

                    if piece.size == Size.TALL:
                        # TALL pieces: all uppercase
                        size_char = "o"
                        color_char = (
                            "K" if piece.coloration == Coloration.BLACK else "W"
                        )
                        shape_char = "R" if piece.shape == Shape.CIRCLE else "Q"
                        hole_char = "H" if piece.hole == Hole.WITH else "N"
                    else:
                        # LITTLE pieces: all lowercase
                        size_char = "x"
                        color_char = (
                            "k" if piece.coloration == Coloration.BLACK else "w"
                        )
                        shape_char = "r" if piece.shape == Shape.CIRCLE else "q"
                        hole_char = "h" if piece.hole == Hole.WITH else "n"

                    text = f"{size_char}"
                    # text = f"{size_char}{color_char}{shape_char}{hole_char}"

                    # Determine if underlined (has hole)
                    if piece.hole == Hole.WITH:
                        # Underlined text
                        text_obj = ax.text(
                            c,
                            r,
                            text,
                            fontsize=16,
                            fontweight="bold",
                            ha="center",
                            va="center",
                            color=color,
                            bbox=dict(
                                boxstyle="round,pad=0.0",
                                edgecolor="none",
                                facecolor="none",
                            ),
                            style="normal",
                            family="monospace",
                        )
                    else:
                        # Normal text
                        text_obj = ax.text(
                            c,
                            r,
                            text,
                            fontsize=16,
                            fontweight="bold",
                            ha="center",
                            va="center",
                            color=color,
                            family="monospace",
                        )

                    # Add circle or square around the text
                    fill_color = "lightgray" if piece.hole == Hole.WITH else "none"
                    if piece.shape == Shape.CIRCLE:
                        # Draw circle
                        circle = mpatches.Circle(
                            (c, r),
                            0.3,
                            fill=True,
                            facecolor=fill_color,
                            edgecolor=color,
                            linewidth=1.5,
                        )
                        ax.add_patch(circle)
                    else:  # SQUARE
                        # Draw square
                        square = mpatches.Rectangle(
                            (c - 0.25, r - 0.25),
                            0.5,
                            0.5,
                            fill=True,
                            facecolor=fill_color,
                            edgecolor=color,
                            linewidth=1.5,
                        )
                        ax.add_patch(square)

        # Set equal aspect ratio
        ax.set_aspect("equal")

        # Only apply tight_layout and show if we created the figure
        if created_fig:
            plt.tight_layout()
            if show:
                plt.show()

        return ax
