from asyncio.log import logger
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QMessageBox, QPushButton, QGraphicsPixmapItem,
    QGraphicsItem, QGraphicsSimpleTextItem, QGraphicsTextItem, QGraphicsProxyWidget,
    QDialog, QCheckBox
)
from PyQt5.QtGui import QPen, QColor, QPixmap, QPainter, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # Importacion para el sonido
import sys 
import math
import os

from quartopy.game.board import Board
from quartopy.game.piece import Piece, Size, Coloration, Shape, Hole
from quartopy.bot.human import Quarto_bot as HumanBot
from quartopy.bot.random_bot import Quarto_bot as RandomBot
from quartopy.bot.minimax_bot import MinimaxBot
from quartopy.bot.CNN_bot import CNNBot
from quartopy.models.Bot import BotAI
from quartopy.game.quarto_game import QuartoGame

# ================================================================
# 🔷 Clase PieceItem (pieza movible con imagen)
# ================================================================
class PieceItem(QGraphicsPixmapItem):
    def __init__(self, piece: Piece, image_path: str, parent_board: QWidget): 
        super().__init__()
        self.piece = piece
        self.parent_board = parent_board 
        self.setPixmap(QPixmap(image_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsPixmapItem.ItemSendsScenePositionChanges, True)
        self.setCursor(Qt.OpenHandCursor)
        
        # Estado de la pieza
        self.is_in_container_3_or_4 = False
        self.is_on_board = False
        self.board_position = None  # (row, col) si está en el tablero
        self.original_container = None
        self.original_position = QPointF(0, 0)
        self.current_container = None

    def mousePressEvent(self, event):
        if self.parent_board.game_over:
            event.ignore()
            return

        # Solo permitir mover si es el turno del humano en la fase correcta
        if self.parent_board._get_current_player_type() != 'human':
            event.ignore()
            return

        game = self.parent_board.quarto_game

        # --- LÓGICA DE CLIC-PARA-SELECCIONAR (CON Y SIN CONFIRMACIÓN) ---
        if self.parent_board.human_action_phase == "PICK_TO_C4" and \
           not self.is_on_board and not self.is_in_container_3_or_4:
            
            # Resaltar la celda de la pieza
            self.parent_board.highlight_rect.setPos(self.pos())
            self.parent_board.highlight_rect.show()

            # Si la confirmación está habilitada, preguntar al usuario
            if self.parent_board.click_to_select_enabled:
                msg = QMessageBox()
                msg.setWindowFlags(Qt.FramelessWindowHint)
                msg.setText("¿Deseas seleccionar esta pieza para tu oponente?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)
                msg.setStyleSheet("""
    QMessageBox {
        background-color: #1a1a1a;
        color: white;
        min-width: 300px;
        border: 1px solid white;
    }
    
    QMessageBox QLabel {
        color: white;
        font-size: 14px;
    }
                            
QDialogButtonBox {
        qproperty-centerButtons: true;  /* Centrar botones horizontalmente */
    }
                            
    QMessageBox QPushButton {
        background-color: #FFC400;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: 2px solid #FFC400; 
    }
    
    QMessageBox QPushButton:hover {
        background-color: #FFD700;  /* Un poco más claro en hover */
        border: 2px solid #FFD700;
    }
    
    QMessageBox QPushButton:pressed {
        background-color: #E6B800;  /* Un poco más oscuro en pressed */
        border: 2px solid #E6B800;
    }
    
    QMessageBox QPushButton:focus {
        outline: none;  
        border: 2px solid white;  
    }
""")
                if msg.exec_() != QMessageBox.Yes: # User clicked No
                    self.parent_board.clear_piece_highlight() # Clear highlight if canceled
                    event.ignore()
                    return
            
            # Proceder con la selección (si no hay confirmación o si fue "Yes")
            self.parent_board.handle_piece_selection(self)
            event.accept()
            return

        # --- LÓGICA DE ARRASTRE Y SUELTE (EXISTENTE) ---
        if self.parent_board.human_action_phase == "PICK_TO_C4":
            if self.is_on_board:
                event.ignore()
                return
        elif self.parent_board.human_action_phase == "PLACE_FROM_C3":
            if not (self.piece == self.parent_board.selected_piece_for_c3 and 
                    self.parentItem() == self.parent_board.shared_piece_container):
                event.ignore()
                return
        
        if not self.is_in_container_3_or_4 and not self.is_on_board:
            self.original_container = self.parentItem()
            self.original_position = self.pos()
        elif self.is_in_container_3_or_4:
            self.current_container = self.parentItem()
        
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        
        # Si no es el turno del humano, ignorar
        if self.parent_board._get_current_player_type() != 'human':
            self.return_to_original()
            super().mouseReleaseEvent(event)
            return
            
        current_scene_pos = self.scenePos()
        container4_rect = self.parent_board.shared_piece_container.sceneBoundingRect()
        in_container4 = container4_rect.contains(current_scene_pos)
        closest_cell = self.parent_board.find_closest_cell(current_scene_pos)
        
        game = self.parent_board.quarto_game

        if self.parent_board.human_action_phase == "PICK_TO_C4":
            if in_container4: # Human is picking a piece for the opponent
                self.parent_board.handle_piece_selection(self)
            else:
                self.return_to_original()
        
        elif self.parent_board.human_action_phase == "PLACE_FROM_C3":
            if closest_cell is not None and self.piece == self.parent_board.selected_piece_for_c3:
                row, col, _ = closest_cell
                if self.parent_board.try_place_piece_on_board(self, row, col):
                    # La lógica de éxito ha sido movida a _handle_successful_placement
                    self.parent_board._handle_successful_placement(self, row, col)
                else:
                    self.return_to_original()
            else:
                self.return_to_original()
        
        else:
            self.return_to_original()
        
        super().mouseReleaseEvent(event)
    
    def return_to_original(self):
        """Regresa la pieza a su posición original"""
        self.parent_board.clear_piece_highlight()
        if self.is_on_board and self.board_position:
            # Si estaba en el tablero, mantenerla ahí
            row, col = self.board_position
            cell = self.parent_board.cells[row][col]
            self.setParentItem(cell)
            self.snap_to_cell(cell)
        elif self.is_in_container_3_or_4 and self.current_container:
            # Si estaba en container 3 o 4, mantenerla ahí
            self.setParentItem(self.current_container)
            self.place_in_container(self.current_container)
        elif self.original_container:
            # Regresar al contenedor original
            self.setParentItem(self.original_container)
            self.setPos(self.original_position)
            self.is_on_board = False
            self.is_in_container_3_or_4 = False
            self.current_container = self.original_container
    
    def remove_from_board(self):
        """Remueve la pieza del tablero lógico si estaba colocada"""
        if self.is_on_board and self.board_position:
            row, col = self.board_position
            self.parent_board.remove_piece_from_board(row, col)
            self.board_position = None
            self.is_on_board = False
    
    def place_in_container(self, container):
        """Coloca la pieza centrada en el contenedor especificado"""
        # Calcular posición centrada
        container_rect = container.boundingRect()
        piece_rect = self.boundingRect()
        
        center_x = (container_rect.width() - piece_rect.width()) / 2
        center_y = (container_rect.height() - piece_rect.height()) / 2 
        
        self.setParentItem(container)
        self.setPos(center_x, center_y)
        self.current_container = container

    def snap_to_cell(self, cell):
        """Ajusta la pieza a la celda especificada (centrada)"""
        cell_rect = cell.boundingRect()
        piece_rect = self.boundingRect()
        
        center_x = (cell_rect.width() - piece_rect.width()) / 2
        center_y = (cell_rect.height() - piece_rect.height()) / 2
        
        self.setParentItem(cell)
        self.setPos(center_x, center_y)
        self.current_container = None


# ================================================================
# 🔶 Clase Celda (Item individual clicable)
# ================================================================
class CellItem(QGraphicsRectItem):
    def __init__(self, row, col, parent_board, size=100):
        super().__init__()
        self.row = row
        self.col = col
        self.parent_board = parent_board
        self.piece_item = None  # Referencia a la pieza colocada

        # Tamaño de celda
        self.setRect(QRectF(0, 0, size, size))
        self.setPen(QPen(QColor("#A9A9A9"), 2))
        self.setBrush(QColor("#000000"))

        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        """Maneja el clic en una celda para colocar una pieza automáticamente."""
        # Comprobar si es un turno válido para esta acción
        if (self.parent_board.game_over or
            self.parent_board._get_current_player_type() != 'human' or
            self.parent_board.human_action_phase != "PLACE_FROM_C3"):
            super().mousePressEvent(event)
            return

        # Comprobar si la celda está vacía
        if self.piece_item is not None:
            super().mousePressEvent(event)
            return
        
        # Encontrar la pieza que se debe colocar (la que está en container3)
        piece_to_place = self.parent_board.selected_piece_for_c3
        piece_item_to_place = None
        for item in self.parent_board.piece_items:
            if item.piece == piece_to_place and item.parentItem() == self.parent_board.shared_piece_container:
                piece_item_to_place = item
                break
        
        if piece_item_to_place:
            # Intentar colocar la pieza en esta celda
            if self.parent_board.try_place_piece_on_board(piece_item_to_place, self.row, self.col):
                # Si tiene éxito, ejecutar la lógica post-colocación
                self.parent_board._handle_successful_placement(piece_item_to_place, self.row, self.col)
                event.accept()
                return
        
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        if self.piece_item is None:  # Solo resaltar si está vacía
            self.setBrush(QColor("#D3D3D3"))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.piece_item is None:  # Solo restaurar si está vacía
            self.setBrush(QColor("#000000"))
        super().hoverLeaveEvent(event)


# ================================================================
# 🔷 Clase Tablero de Juego (GameBoard)
# ================================================================
# ================================================================
# ?? Clase PauseDialog (Men� de pausa)
# ================================================================
class PauseDialog(QDialog):
    def __init__(self, parent_board):
        super().__init__(parent_board)
        self.parent_board = parent_board
        self.resize(400, 250) # Increased height
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        #BORDE VENTANA COLOR GRIS
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20) # Reduced margins

        # Título
        title_label = QLabel("PAUSA")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #FFD700; padding: 10px;") # Added padding
        self.layout.addWidget(title_label)

        # Checkbox para confirmación de selección
        self.checkbox = QCheckBox("Habilitar confirmacion de seleccion")
        self.checkbox.setStyleSheet("color: white;")
        self.checkbox.setChecked(self.parent_board.click_to_select_enabled)
        self.layout.addWidget(self.checkbox)
        self.checkbox.setStyleSheet("""
    QCheckBox {
        color: white;
    }
    QCheckBox::indicator {
        background: #1a1a1a;
        width: 18px;
        height: 18px;
        border-radius: 1px;
    }
    QCheckBox::indicator:checked {
        background-color: #FFC400;
        border: 2px solid #FFC400;
        color: black;
    }
""")
        
        # Nuevo Checkbox para habilitar/deshabilitar sonido
        self.sound_checkbox = QCheckBox("Habilitar sonido")
        self.sound_checkbox.setStyleSheet("color: white;")
        self.sound_checkbox.setChecked(self.parent_board.sound_enabled) # Initialize with current state
        self.layout.addWidget(self.sound_checkbox)
        self.sound_checkbox.setStyleSheet("""
    QCheckBox {
        color: white;
    }
    QCheckBox::indicator {
        background: #1a1a1a;
        width: 18px;
        height: 18px;
        border-radius: 3px;
    }
    QCheckBox::indicator:checked {
        background-color: #FFC400;
        border: 2px solid #FFC400;
        color: black;
    }
""")
        
        # Button Box
        button_layout = QHBoxLayout()
        self.btn_continue = QPushButton("Continuar")
        self.btn_continue.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_continue.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: black;
                border: 2px solid #FFC400;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #FFC400;
                border: 2px solid #FFB300;
            }
            QPushButton:pressed {
                background-color: #FFB300;
            }
        """)
        self.btn_main_menu = QPushButton("Volver al menu principal")
        self.btn_main_menu.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_main_menu.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: black;
                border: 2px solid #FFC400;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #FFC400;
                border: 2px solid #FFB300;
            }
            QPushButton:pressed {
                background-color: #FFB300;
            }
        """)
        
        button_layout.addWidget(self.btn_continue)
        button_layout.addWidget(self.btn_main_menu)
        
        self.layout.addLayout(button_layout)
        
        # Connections
        self.btn_continue.clicked.connect(self.accept)
        self.btn_main_menu.clicked.connect(self.go_to_main_menu)
        
    def go_to_main_menu(self):
        self.parent_board.go_back_to_menu()
        self.reject()


class GameBoard(QWidget):
    back_to_menu_signal = pyqtSignal()
    def __init__(
        self, 
        parent=None, 
        player1_config: dict = None, 
        player2_config: dict = None,
        player1_name: str = "Jugador 1",
        player2_name: str = "Jugador 2", 
        mode_2x2: bool = False
    ):
        super().__init__(parent)
        self.player1_config = player1_config if player1_config is not None else {'type': 'human', 'display_name': 'Humano'}
        self.player2_config = player2_config if player2_config is not None else {'type': 'random_bot', 'display_name': 'Bot Aleatorio'}
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.match_number = 1

        # Inicializar reproductor de sonido
        self.place_piece_sound = QMediaPlayer()
        self.sound_enabled = True # Controla si el sonido está habilitado
        sound_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sounds", "piece_move.mp3"))
        self.place_piece_sound.setMedia(QMediaContent(QUrl.fromLocalFile(sound_file_path)))
        self.place_piece_sound.error.connect(self.handle_media_player_error)

        print(f"Debug: Sound file path: {sound_file_path}")
        print(f"Debug: Sound file exists: {os.path.exists(sound_file_path)}")
        print(f"Debug: QMediaPlayer state: {self.place_piece_sound.state()}")

        # --- Main Vertical Layout ---
        main_v_layout = QVBoxLayout(self)
        self.setLayout(main_v_layout)
        self.setStyleSheet("background-color: black;")

        # --- Title Label ---
        title_label = QLabel("QUARTO")
        title_label.setStyleSheet("background-color: white; font-size: 16pt; font-weight: bold; color: black;")
        title_label.setAlignment(Qt.AlignCenter)
        main_v_layout.addWidget(title_label)

        # --- QGraphicsView ---
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setAlignment(Qt.AlignCenter) # Center the content within the view
        self.view.setStyleSheet("background-color: #0F0A07 ; border: none;")
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_v_layout.addWidget(self.view, 1) # Add with stretch factor

        # --- Botón de Pausa (como Proxy Widget en la Escena) ---
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid white;
                padding: 10px;
                font-size: 12pt;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(50, 50, 50, 200);
            }
        """
        self.btn_options = QPushButton('Opciones')
        self.btn_options.setStyleSheet(button_style)
        self.btn_options.setFixedSize(180, 50)
        self.btn_options.clicked.connect(self.show_pause_menu)

        self.btn_exit = QPushButton('Salir')
        self.btn_exit.setStyleSheet(button_style)
        self.btn_exit.setFixedSize(180, 50)
        self.btn_exit.clicked.connect(self.go_back_to_menu)
        
        proxy_exit = QGraphicsProxyWidget()
        proxy_exit.setWidget(self.btn_exit)
        proxy_exit.setPos(250, 520)
        self.scene.addItem(proxy_exit)

        proxy_options = QGraphicsProxyWidget()
        proxy_options.setWidget(self.btn_options)
        proxy_options.setPos(50, 520) # Posición centrada donde estaban los otros botones
        self.scene.addItem(proxy_options)

        self.btn_restart = QPushButton('Jugar de nuevo')
        self.btn_restart.setStyleSheet(button_style)
        self.btn_restart.setFixedSize(180, 50)
        self.btn_restart.clicked.connect(self.confirm_restart_game)

        proxy_restart = QGraphicsProxyWidget()
        proxy_restart.setWidget(self.btn_restart)
        proxy_restart.setPos(560, 520) # Posición al lado de los otros botones
        self.scene.addItem(proxy_restart)

        # --- Tablero (QGraphicsItems within scene) ---
        self.cells = []
        self.create_board_grid()

        # --- Contenedores de destino (3 y 4) y sus labels ---
        font = QFont("Arial", 11, QFont.Bold)
        
        # Contenedor compartido para la pieza a colocar
        self.shared_piece_container = self.create_simple_container(195, 100, 80, 80)

        # Contenedor de piezas disponibles (cuadrado 4x4)
        piece_area_size = 4 * 60 # 4 pieces of 60px
        self.all_pieces_container = self.create_container(115, 200, piece_area_size, piece_area_size, rotate=False)

        # --- Rectángulo de resaltado para piezas disponibles ---
        self.highlight_rect = QGraphicsRectItem(0, 0, 60, 60)
        self.highlight_rect.setBrush(QColor("white"))
        self.highlight_rect.setPen(QPen(Qt.NoPen))
        self.highlight_rect.setZValue(-1) # Detrás de las piezas
        self.highlight_rect.setParentItem(self.all_pieces_container)
        self.highlight_rect.hide()

        # --- Display de turno y Nametags (QGraphicsItems within scene) ---
        self.create_turn_display() # This creates QGraphicsItems in self.scene
        self.create_player_info_display() # Added: Display player info


        # --- Common game logic setup ---
        def create_player(p_config, p_name):
            p_type = p_config['type']
            if p_type == 'human':
                return HumanBot(name=p_name)
            elif p_type == 'custom_bot':
                actual_bot_class = p_config['bot_class'] # This is CNNBot
                model_class = p_config['model_class'] # This is QuartoCNN
                weights_path = p_config.get('weights_path') # This is the .pt file

                if weights_path:
                    return actual_bot_class(name=p_name, model_class=model_class, model_path=weights_path)
                else: # Fallback, though weights_path should always be there for custom_bot
                    return actual_bot_class(name=p_name, model_class=model_class)
            elif p_type == 'minimax_bot':
                return MinimaxBot(name=p_name)
            elif p_type == 'cnn_bot':
                return CNNBot(name=p_name)
            else:  # 'random_bot'
                return RandomBot(name=p_name)

        self.player1_instance = create_player(self.player1_config, self.player1_name)
        self.player2_instance = create_player(self.player2_config, self.player2_name)
            
        self.quarto_game = QuartoGame(
            player1=self.player1_instance, 
            player2=self.player2_instance, 
            mode_2x2=mode_2x2
        )
        self.logic_board = self.quarto_game.game_board

        # Estados del juego
        self.selected_piece_for_c3 = None
        self.human_action_phase = "IDLE" # Por defecto, en espera
        self.current_turn = "IDLE"  # IDLE, HUMAN, BOT, GAME_OVER
        self.game_over = False
        self.click_to_select_enabled = True # Controla la nueva funcionalidad

        # Determinar el estado inicial del juego basado en el tipo de jugador 1
        if self.player1_config['type'] == 'human':
            self.human_action_phase = "PICK_TO_C4"
            self.current_turn = "HUMAN"
        else: # player1_type is a bot
            self.current_turn = "BOT"

        # --- Crear TODAS las piezas ---
        self.create_all_pieces()
        
        # Ajustar vista de la escena para ver todo
        self.scene.setSceneRect(0, 0, 1000, 700) # This needs to encompass all the QGraphicsItems

        # Radio de atracción a las celdas
        self.snap_distance = 60
        
        # Inicializar display de turno
        self.update_turn_display()

        # Si el jugador 1 es un bot, iniciar su turno automáticamente
        if self.current_turn == "BOT":
            QTimer.singleShot(500, self.handle_bot_turn)



    def show_pause_menu(self):
        dialog = PauseDialog(self)
        dialog.exec_()
        self.click_to_select_enabled = dialog.checkbox.isChecked()
        self.sound_enabled = dialog.sound_checkbox.isChecked()

    def highlight_winning_line(self, winning_coords):
        """Pinta las celdas de la línea ganadora."""
        for row, col in winning_coords:
            if 0 <= row < 4 and 0 <= col < 4:
                self.cells[row][col].setBrush(QColor("#FFFFFF")) 

    def end_game(self, winner_name=None):
        """Maneja el fin del juego con una ventana más ancha y elegante."""
        self.game_over = True
        self.current_turn = "GAME_OVER"
        self.update_turn_display()

        # Guardar la partida
        self.quarto_game.export_history_to_csv(match_number=self.match_number, winner=winner_name or "Tie")
        self.match_number += 1

        msg = QMessageBox(self)
        
        # Estilo visual: Negro puro, texto blanco y ancho expandido
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #000000;
                min-width: 500px; /* Aquí controlas el ancho de la ventana */
                border: 1px solid #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 20px;
                font-weight: bold;
                padding-left: 50px; /* Espacio extra a los lados para que respire */
                padding-right: 50px;
                padding-top: 20px;
                padding-bottom: 20px;
            }
            QPushButton {
                background-color: #000000;
                color: white;
                border: 2px solid #FFFFFF;
                padding: 10px 40px;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
                margin-right: 20px;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                color: #000000;
            }
            """
        )

        if winner_name:
            msg.setWindowFlags(Qt.FramelessWindowHint)
            msg.setText(f"🏆 ¡FELICIDADES! 🏆\n\nEl jugador {winner_name.upper()} ha ganado la partida.")
        elif self.logic_board.is_full():
            msg.setWindowTitle("¡Empate!")
            msg.setText("🤝 EMPATE\n\nEl tablero está lleno.")
        else:
            msg.setWindowTitle("Aviso")
            msg.setText("PARTIDA FINALIZADA")

        # Eliminamos el icono predeterminado para que el texto ocupe todo el ancho
        msg.setIcon(QMessageBox.NoIcon)
        
        msg.exec_()

    def clear_piece_highlight(self):
        """Oculta el rectángulo de resaltado de las piezas."""
        self.highlight_rect.hide()

    def go_back_to_menu(self):
        self.reset_board()
        self.match_number = 1
        self.back_to_menu_signal.emit()

    def _get_current_player_type(self) -> str:
        """Retorna el tipo del jugador actual ('human', 'random_bot', or 'minimax_bot')."""
        if self.quarto_game.turn: # Player 1
            return self.player1_config['type']
        else: # Player 2
            return self.player2_config['type']

    def handle_piece_selection(self, piece_item):
        """
        Maneja la lógica de cuando un humano selecciona una pieza para el oponente,
        tanto por clic como por arrastre.
        """
        self.clear_piece_highlight()
        game = self.quarto_game
        
        if piece_item.is_on_board:
            piece_item.return_to_original()
            return

        # Limpiar container4 si ya hay una pieza seleccionada
        if game.selected_piece:
            for item in self.piece_items:
                if item.piece == game.selected_piece and item.parentItem() == self.shared_piece_container:
                    item.return_to_original()
                    item.is_in_container_3_or_4 = False
                    break

        # Colocar la nueva pieza visualmente en container4
        piece_item.place_in_container(self.shared_piece_container)
        piece_item.is_in_container_3_or_4 = True
        piece_item.is_on_board = False
        piece_item.current_container = self.shared_piece_container

        # Actualizar el juego lógico
        game.select_and_remove_piece(piece_item.piece)

        move_info = {
            "player_name": game.get_current_player().name,
            "player_pos": game.player_turn,
            "action": "selected",
            "piece": piece_item.piece.__repr__(verbose=True),
            "piece_index": piece_item.piece.index(),
            "attempt": 1,
        }
        game.move_history.append(move_info)

        game.cambiar_turno() # Cambia a fase de colocación para el siguiente jugador

        # Determinar quién juega ahora
        next_player_type = self._get_current_player_type()
        if next_player_type == 'human':
            self.human_action_phase = "PLACE_FROM_C3"
            self.selected_piece_for_c3 = piece_item.piece
            self.current_turn = "HUMAN"
            self.update_turn_display()
        else: # bot
            self.human_action_phase = "IDLE"
            self.current_turn = "BOT"
            self.update_turn_display()
            QTimer.singleShot(500, self.handle_bot_turn)

    def create_turn_display(self):
        """Crea los displays de información de turno y acción."""
        font_title = QFont("Arial", 12, QFont.Bold)
        font_player = QFont("Arial", 14, QFont.Bold)
        
        # --- Display de Acción ---
        self.action_display_bg = QGraphicsRectItem(0, 0, 300, 90) # Tamaño reducido
        self.action_display_bg.setPen(QPen(QColor("#FFD700"), 2))
        self.action_display_bg.setBrush(QColor(0, 0, 0, 200))
        self.action_display_bg.setPos(495, 50) # Reposicionado y centrado
        self.scene.addItem(self.action_display_bg)

        self.action_text = QGraphicsTextItem("", self.action_display_bg)
        self.action_text.setDefaultTextColor(QColor("white"))
        self.action_text.setFont(font_title)
        # Centrar el texto dentro del rectángulo
        self.action_text.setTextWidth(300)
        self.action_text.setPos(0, 10) # Ajustar posición vertical
        
        # --- Nametags de Jugadores ---
        self.player1_tag = QGraphicsSimpleTextItem("")
        self.player1_tag.setFont(font_player)
        self.player1_tag.setPos(40, 50) 
        self.scene.addItem(self.player1_tag)

        self.player2_tag = QGraphicsSimpleTextItem("")
        self.player2_tag.setFont(font_player)
        self.player2_tag.setPos(250, 50) 
        self.scene.addItem(self.player2_tag)

    def create_player_info_display(self):
        """Crea un display estático con la información de los jugadores."""
        p1_display = self.player1_config['display_name']
        p2_display = self.player2_config['display_name']

        info_text = f"Jugador 1: {p1_display}\nJugador 2: {p2_display}"

        player_info_label = QLabel(info_text)
        style = """
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid #FFD700;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
            }
        """
        player_info_label.setStyleSheet(style)

        proxy_info = QGraphicsProxyWidget()
        proxy_info.setWidget(player_info_label)
        proxy_info.setPos(10, 10)
        self.scene.addItem(proxy_info)

    def update_turn_display(self):
        """Actualiza el display del turno y de la acción según el estado actual."""
        current_player_logic = self.quarto_game.get_current_player()
        
        if current_player_logic is self.quarto_game.player1:
            p_current_name = self.player1_name
            p_next_name = self.player2_name
        else:
            p_current_name = self.player2_name
            p_next_name = self.player1_name

        # Actualizar display de ACCIÓN
        action_string = ""
        if self.current_turn == "GAME_OVER":
            action_string = "Partida Terminada<br>"
        elif self.quarto_game.pick: # Fase de seleccionar pieza
            action_string = f"Turno de: {p_current_name}<br><br>Selecciona una pieza para {p_next_name}"
        else: # Fase de colocar pieza
            action_string = f"Turno de: {p_current_name}<br><br>Coloca la pieza en el tablero"
        
        # Centrar el texto en el nuevo contenedor
        self.action_text.setHtml(f"<div style='text-align: center; width: 380px;'>{action_string}</div>")

        self.scene.update()

    # ================================================================
    def find_closest_cell(self, scene_pos: QPointF):
        """Encuentra la celda más cercana a la posición dada
        Returns: (row, col, cell) o None si está muy lejos"""
        min_distance = float('inf')
        closest_cell = None
        closest_row = None
        closest_col = None
        
        for row in range(4):
            for col in range(4):
                cell = self.cells[row][col]
                cell_center = cell.sceneBoundingRect().center()
                
                # Calcular distancia euclidiana
                dx = scene_pos.x() - cell_center.x()
                dy = scene_pos.y() - cell_center.y()
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_cell = cell
                    closest_row = row
                    closest_col = col
        
        # Solo retornar si está dentro del radio de atracción
        if min_distance <= self.snap_distance:
            return (closest_row, closest_col, closest_cell)
        return None

    def try_place_piece_on_board(self, piece_item: PieceItem, row: int, col: int) -> bool:
        """Intenta colocar una pieza en el tablero
        Returns: True si se colocó exitosamente, False si la celda está ocupada"""
        
        # Verificar si la celda está vacía
        if not self.logic_board.is_empty(row, col):
            return False
        
        cell = self.cells[row][col]
        
        # Si ya había una pieza en esta celda (no debería pasar), rechazar
        if cell.piece_item is not None:
            return False
        
        # Si esta pieza ya estaba en otra celda, limpiar la anterior
        if piece_item.is_on_board and piece_item.board_position:
            old_row, old_col = piece_item.board_position
            self.remove_piece_from_board(old_row, old_col)
        
        # Colocar la pieza en el tablero lógico
        self.logic_board.put_piece(piece_item.piece, row, col)
        
        # Colocar la pieza visualmente
        piece_item.snap_to_cell(cell)
        cell.piece_item = piece_item
        
        cell.setBrush(QColor("#808080"))
        
        return True

    def remove_piece_from_board(self, row: int, col: int):
        """Remueve una pieza del tablero (lógico y visual)"""
        if 0 <= row < 4 and 0 <= col < 4:
            # Limpiar tablero lógico
            if not self.logic_board.is_empty(row, col):
                self.logic_board.board[row][col] = 0
            
            # Limpiar celda visual
            cell = self.cells[row][col]
            if cell.piece_item:
                cell.piece_item.board_position = None
                cell.piece_item.is_on_board = False
                cell.piece_item.current_container = None
                cell.piece_item = None
            cell.setBrush(QColor("#000000"))

    def _handle_successful_placement(self, piece_item, row, col):
        """Lógica centralizada que se ejecuta después de colocar una pieza con éxito."""
        if self.sound_enabled: # Reproducir sonido solo si está habilitado
            self.place_piece_sound.play() 
        game = self.quarto_game
        piece_item.is_on_board = True
        piece_item.is_in_container_3_or_4 = False
        piece_item.board_position = (row, col)

        move_info = {
            "player_name": game.get_current_player().name,
            "player_pos": game.player_turn,
            "action": "placed",
            "position": (row, col),
            "position_index": game.game_board.pos2index(row, col),
            "attempt": 1,
            "board_after": game.game_board.serialize(),
        }
        game.move_history.append(move_info)

        # Limpiar container3 si la pieza vino de allí
        if piece_item.parentItem() == self.shared_piece_container:
            for p_item in self.piece_items:
                if p_item.piece == piece_item.piece and p_item.parentItem() == self.shared_piece_container:
                    p_item.return_to_original()
                    p_item.is_in_container_3_or_4 = False
                    break
        
        # Verificar si el juego terminó
        has_won, winning_line = self.logic_board.check_win(self.quarto_game.mode_2x2)
        if has_won:
            winner = self.quarto_game.get_current_player()
            if winning_line:
                self.highlight_winning_line(winning_line)
            self.end_game(winner.name)
            return
        
        # Preparar para siguiente ronda
        self.selected_piece_for_c3 = None
        game.selected_piece = 0

        # Verificar si el juego terminó (empate)
        if self.logic_board.is_full():
            self.end_game()
            return
        
        # Cambiar el turno lógico del juego para la fase de selección
        game.cambiar_turno()
        
        # Determinar quién juega ahora
        next_player_type = self._get_current_player_type()
        if next_player_type == 'human':
            self.human_action_phase = "PICK_TO_C4"
            self.current_turn = "HUMAN"
            self.update_turn_display()
        else:
            self.human_action_phase = "IDLE"
            self.current_turn = "BOT"
            self.update_turn_display()
            QTimer.singleShot(500, self.handle_bot_turn)

    # ================================================================
    def get_available_pieces(self):
        """Obtiene todas las piezas disponibles (no en tablero ni en container3/4)"""
        available_pieces = []
        for p_item in self.piece_items:
            if not p_item.is_on_board and not p_item.is_in_container_3_or_4:
                available_pieces.append(p_item.piece)
        return available_pieces

    def create_simple_container(self, x, y, w, h):
        """Crea un contenedor simple sin rotación"""
        container = QGraphicsRectItem(0, 0, w, h)
        container.setPen(QPen(QColor("#A9A9A9"), 3))
        container.setBrush(QColor(0, 0, 0, 180))
        container.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        container.setPos(x, y)
        self.scene.addItem(container)
        return container

    def create_container(self, x, y, w, h, rotate=False, label=""):
        """Crea un contenedor con opción de rotación"""
        container = QGraphicsRectItem(0, 0, w, h)
        container.setPen(QPen(QColor("#A9A9A9"), 2))
        container.setBrush(QColor(0, 0, 0, 180))
        container.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        container.setPos(x, y)
        self.scene.addItem(container)
        
        if rotate: # Only apply rotation if rotate is True
            container.setRotation(90)

        # Líneas de cuadrícula
        for i in range(5): # 5 vertical lines for 4 columns
            line = self.scene.addLine(i * (w/4), 0, i * (w/4), h, QPen(QColor("#A9A9A9"), 1))
            line.setParentItem(container)
        for j in range(5): # 5 horizontal lines for 4 rows
            line = self.scene.addLine(0, j * (h/4), w, j * (h/4), QPen(QColor("#A9A9A9"), 1))
            line.setParentItem(container)
                
        return container

    # ================================================================
    def create_all_pieces(self):
        """Crea las 16 piezas completas del juego Quarto en una cuadrícula 4x4."""
        pieces_data = [
            (Piece(Size.TALL,  Coloration.BLACK, Shape.CIRCLE, Hole.WITHOUT), "./quartopy/gui/assets/images/bc0.png"),
            (Piece(Size.TALL,  Coloration.BLACK, Shape.CIRCLE, Hole.WITH),    "./quartopy/gui/assets/images/bc1.png"),
            (Piece(Size.LITTLE, Coloration.BLACK, Shape.CIRCLE, Hole.WITHOUT), "./quartopy/gui/assets/images/bc2.png"),
            (Piece(Size.LITTLE, Coloration.BLACK, Shape.CIRCLE, Hole.WITH),    "./quartopy/gui/assets/images/bc3.png"),
            (Piece(Size.TALL,  Coloration.BLACK, Shape.SQUARE, Hole.WITHOUT), "./quartopy/gui/assets/images/bs0.png"),
            (Piece(Size.TALL,  Coloration.BLACK, Shape.SQUARE, Hole.WITH),    "./quartopy/gui/assets/images/bs1.png"),
            (Piece(Size.LITTLE, Coloration.BLACK, Shape.SQUARE, Hole.WITHOUT), "./quartopy/gui/assets/images/bs2.png"),
            (Piece(Size.LITTLE, Coloration.BLACK, Shape.SQUARE, Hole.WITH),    "./quartopy/gui/assets/images/bs3.png"),
            (Piece(Size.TALL,  Coloration.WHITE, Shape.CIRCLE, Hole.WITHOUT), "./quartopy/gui/assets/images/gc0.png"),
            (Piece(Size.TALL,  Coloration.WHITE, Shape.CIRCLE, Hole.WITH),    "./quartopy/gui/assets/images/gc1.png"),
            (Piece(Size.LITTLE, Coloration.WHITE, Shape.CIRCLE, Hole.WITHOUT), "./quartopy/gui/assets/images/gc2.png"),
            (Piece(Size.LITTLE, Coloration.WHITE, Shape.CIRCLE, Hole.WITH),    "./quartopy/gui/assets/images/gc3.png"),
            (Piece(Size.TALL,  Coloration.WHITE, Shape.SQUARE, Hole.WITHOUT), "./quartopy/gui/assets/images/gs0.png"),
            (Piece(Size.TALL,  Coloration.WHITE, Shape.SQUARE, Hole.WITH),    "./quartopy/gui/assets/images/gs1.png"),
            (Piece(Size.LITTLE, Coloration.WHITE, Shape.SQUARE, Hole.WITHOUT), "./quartopy/gui/assets/images/gs2.png"),
            (Piece(Size.LITTLE, Coloration.WHITE, Shape.SQUARE, Hole.WITH),    "./quartopy/gui/assets/images/gs3.png"),
        ]
        
        self.piece_items = []
        piece_size = 60
        for i, (piece, image_path) in enumerate(pieces_data):
            row = i // 4
            col = i % 4
            x = col * piece_size
            y = row * piece_size
            
            piece_item = PieceItem(piece, image_path, self)
            piece_item.setPos(x, y)
            piece_item.setParentItem(self.all_pieces_container) # Use the new single container
            
            # Inicializar estado original
            piece_item.original_container = self.all_pieces_container
            piece_item.original_position = QPointF(x, y)
            piece_item.current_container = self.all_pieces_container
            
            self.piece_items.append(piece_item)

    # ================================================================
    def create_board_grid(self):
        """Crea la cuadrícula principal del tablero 4x4 en la parte derecha."""
        cell_size = 85  # Tablero más pequeño
        spacing = 5
        start_x = 470  # Movido más a la izquierda
        start_y = 150

        # Fondo opcional para el tablero
        board_bg_size = 4 * (cell_size + spacing) + spacing
        board_bg = QGraphicsRectItem(start_x - spacing*2, start_y - spacing*2, board_bg_size, board_bg_size)
        board_bg.setBrush(QColor(0,0,0,150))
        board_bg.setPen(QPen(Qt.NoPen)) # Eliminar el borde del fondo
        self.scene.addItem(board_bg)

        for row in range(4):
            row_cells = []
            for col in range(4):
                cell = CellItem(row, col, self, size=cell_size) # Pasar el nuevo tamaño
                x = start_x + col * (cell_size + spacing)
                y = start_y + row * (cell_size + spacing)
                cell.setPos(x, y)
                self.scene.addItem(cell)
                row_cells.append(cell)
            self.cells.append(row_cells)

    # ================================================================
    def update_cell_visual(self, row, col):
        cell = self.cells[row][col]
        cell.setBrush(QColor("#808080"))

    def reset_board(self):
        # Limpiar tablero lógico
        self.quarto_game = QuartoGame(
            player1=self.player1_instance, 
            player2=self.player2_instance,
            mode_2x2=self.quarto_game.mode_2x2 # Mantener el modo 2x2 original
        )
        self.logic_board = self.quarto_game.game_board
        
        # Limpiar celdas visuales
        for row in self.cells:
            for cell in row:
                cell.setBrush(QColor("#000000"))
                cell.piece_item = None
        
        # Regresar todas las piezas a sus contenedores originales
        for piece_item in self.piece_items:
            if piece_item.original_container:
                piece_item.setParentItem(piece_item.original_container)
                piece_item.setPos(piece_item.original_position)
                piece_item.is_on_board = False
                piece_item.is_in_container_3_or_4 = False
                piece_item.board_position = None
                piece_item.current_container = piece_item.original_container
        
        # Reiniciar fases
        self.game_over = False
        self.human_action_phase = "IDLE" # Por defecto, en espera
        self.selected_piece_for_c3 = None
        self.current_turn = "IDLE"  # IDLE, HUMAN, BOT, GAME_OVER

        # Determinar el estado inicial del juego basado en el tipo de jugador 1
        if self.player1_config['type'] == 'human':
            self.human_action_phase = "PICK_TO_C4"
            self.current_turn = "HUMAN"
        else: # player1_type is a bot
            self.current_turn = "BOT"
        
        self.update_turn_display()
        
        # Si el jugador 1 es un bot, iniciar su turno automáticamente
        if self.current_turn == "BOT":
            QTimer.singleShot(500, self.handle_bot_turn)

    def confirm_restart_game(self):
        msg = QMessageBox()
        msg.setWindowFlags(Qt.FramelessWindowHint)
        msg.setText("¿Estás seguro de que quieres reiniciar la partida?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet("""
    QMessageBox {
        background-color: #1a1a1a;
        color: white;
        min-width: 300px;
        border: 1px solid white;
    }
    
    QMessageBox QLabel {
        color: white;
        font-size: 14px;
    }
                            
QDialogButtonBox {
        qproperty-centerButtons: true;
    }
                            
    QMessageBox QPushButton {
        background-color: #FFC400;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: 2px solid #FFC400; 
    }
    
    QMessageBox QPushButton:hover {
        background-color: #FFD700;
        border: 2px solid #FFD700;
    }
    
    QMessageBox QPushButton:pressed {
        background-color: #E6B800;
        border: 2px solid #E6B800;
    }
    
    QMessageBox QPushButton:focus {
        outline: none;  
        border: 2px solid white;  
    }
""")
        ret = msg.exec_()
        if ret == QMessageBox.Yes:
            self.restart_game()

    def restart_game(self):
        self.reset_board()
        self.match_number = 1
        self.update_turn_display()

    def handle_bot_turn(self):
        """Maneja el turno completo del bot"""
        if self.game_over:
            return
        print(f"[DEBUG] handle_bot_turn called - current_turn: {self.current_turn}")
        
        if self.current_turn != "BOT":
            print(f"[DEBUG] Not bot's turn, current_turn: {self.current_turn}")
            return
            
        self.update_turn_display()  # Actualizar display
        QTimer.singleShot(300, self._execute_bot_turn)
    
    def _execute_bot_turn(self):
        """Ejecuta la lógica del turno del bot, manejando ambas fases (selección y colocación)."""
        print(f"[DEBUG] _execute_bot_turn - quarto_game.pick: {self.quarto_game.pick}")
        
        game = self.quarto_game
        current_player = game.get_current_player()
        
        print(f"[DEBUG] Current player type: {type(current_player)}")
        
        # Determine if it's the current player's turn to pick or place
        if game.pick: # Bot needs to select a piece
            self._bot_select_piece_for_opponent()
        else: # Bot needs to place a piece
            self._bot_place_piece()
    
    def _bot_place_piece(self):
        """El bot coloca una pieza en el tablero"""
        print("[DEBUG] _bot_place_piece")
        
        game = self.quarto_game
        piece_to_place = game.selected_piece # La pieza ya está seleccionada en la lógica del juego
        
        # Encontrar el PieceItem correspondiente
        piece_item_to_place = None
        for p_item in self.piece_items:
            # La pieza a colocar es la que está en game.selected_piece y que no está en el tablero principal
            if (p_item.piece == piece_to_place and not p_item.is_on_board):
                piece_item_to_place = p_item
                break        
        if not piece_item_to_place:
            print(f"[ERROR] No PieceItem found for selected piece: {piece_to_place}")
            self.end_game() # Manejar este caso de error
            return

        # Bot coloca la pieza en el tablero
        print(f"[DEBUG] Bot placing piece: {piece_to_place}")
        row, col = game.get_current_player().place_piece(game, piece_to_place)
        print(f"[DEBUG] Bot placed at: ({row}, {col})")
        
        if self.try_place_piece_on_board(piece_item_to_place, row, col):
            piece_item_to_place.is_on_board = True
            piece_item_to_place.is_in_container_3_or_4 = False
            piece_item_to_place.board_position = (row, col)
            piece_item_to_place.current_container = None

            move_info = {
                "player_name": game.get_current_player().name,
                "player_pos": game.player_turn,
                "action": "placed",
                "position": (row, col),
                "position_index": game.game_board.pos2index(row, col),
                "attempt": 1,
                "board_after": game.game_board.serialize(),
            }
            game.move_history.append(move_info)
            
            # Limpiar container3 si la pieza estaba allí
            if piece_item_to_place.parentItem() == self.shared_piece_container:
                piece_item_to_place.setParentItem(None) # Quitar de container3
            
            # Verificar si hay victoria
            has_won, winning_line = self.logic_board.check_win(self.quarto_game.mode_2x2)
            if has_won:
                winner = game.get_current_player()
                print(f"[DEBUG] Bot {winner.name} won!")
                if winning_line:
                    self.highlight_winning_line(winning_line)
                self.end_game(winner.name)
                return
            
            # Resetear la pieza seleccionada en la lógica del juego
            game.selected_piece = 0 # O None, depende de cómo lo maneje QuartoGame

            # Verificar si quedan piezas disponibles
            available_pieces = self.get_available_pieces()
            print(f"[DEBUG] Available pieces: {len(available_pieces)}")
            
            if not available_pieces and not self.logic_board.check_win(self.quarto_game.mode_2x2)[0]:

                print("[DEBUG] No more pieces available!")
                self.end_game()
                return
            
            # Cambiar el turno lógico del juego para la fase de selección del próximo jugador
            game.cambiar_turno() # Ahora el siguiente jugador debe seleccionar una pieza
            
            # Determinar quién juega ahora
            next_player_type = self._get_current_player_type()
            
            if next_player_type == 'human':
                self.human_action_phase = "PICK_TO_C4"
                self.current_turn = "HUMAN"
                self.update_turn_display()
                self.update()
                print(f"[DEBUG] Next is human to pick: {self.human_action_phase}")
            else: # next_player_type is a bot
                self.human_action_phase = "IDLE" # No hay acción humana directa
                self.current_turn = "BOT"
                self.update_turn_display()
                QTimer.singleShot(500, self.handle_bot_turn)
                print(f"[DEBUG] Next is bot to pick: {self.current_turn}")
        else:
            print("[DEBUG] Bot failed to place piece")
            # Podríamos implementar reintentos o un manejo de error más robusto aquí
            self.end_game() # Fallback en caso de que el bot elija una posición inválida
    

    
    def _bot_select_piece_for_opponent(self):
        """El bot selecciona una pieza para el oponente y la coloca en container3"""
        print("[DEBUG] _bot_select_piece_for_opponent")
        
        game = self.quarto_game
        current_bot = game.get_current_player()
        
        # Bot selecciona una pieza
        selected_piece_logic = current_bot.select(game)
        
        # Actualizar el juego lógico
        if not game.select_and_remove_piece(selected_piece_logic):
            # Si la pieza seleccionada por el bot no se encuentra (error de lógica del bot), terminar el juego.
            print(f"[ERROR] Bot selected an invalid piece that is not in storage: {selected_piece_logic}")
            self.end_game()
            return

        move_info = {
            "player_name": current_bot.name,
            "player_pos": game.player_turn,
            "action": "selected",
            "piece": selected_piece_logic.__repr__(verbose=True),
            "piece_index": selected_piece_logic.index(),
            "attempt": 1,
        }
        game.move_history.append(move_info)
        
        game.cambiar_turno() # Cambia a fase de colocación para el siguiente jugador

        # Encontrar el PieceItem correspondiente para moverlo a container3
        piece_item_to_move = None
        for p_item in self.piece_items:
            if p_item.piece == selected_piece_logic and not p_item.is_on_board and not p_item.is_in_container_3_or_4:
                piece_item_to_move = p_item
                break
        
        if piece_item_to_move:
            # Mover la pieza visualmente a container3
            piece_item_to_move.place_in_container(self.shared_piece_container)
            piece_item_to_in_container_3_or_4 = True
            piece_item_to_move.is_on_board = False
            piece_item_to_move.current_container = self.shared_piece_container
            
            self.selected_piece_for_c3 = selected_piece_logic # Usado por el humano para saber qué pieza colocar
            
            # Determinar quién juega ahora (el oponente)
            next_player_type = self._get_current_player_type()
            
            if next_player_type == 'human':
                self.human_action_phase = "PLACE_FROM_C3"
                self.current_turn = "HUMAN"
                self.update_turn_display()
                self.update()
                print(f"[DEBUG] Next is human to place: {self.human_action_phase}")
            else: # next_player_type is a bot
                self.human_action_phase = "IDLE" # No hay acción humana directa
                self.current_turn = "BOT"
                self.update_turn_display()
                QTimer.singleShot(500, self.handle_bot_turn)
                print(f"[DEBUG] Next is bot to place: {self.current_turn}")
        else:
            print(f"[ERROR] Could not find PieceItem for selected piece: {selected_piece_logic}")
            # Esto no debería pasar si get_current_player().select() devuelve una pieza válida
            # que está en el storage_board y no en el game_board.
            self.end_game() # Considerar terminar o manejar el error de otra forma

    def create_player_info_display(self):
        """Crea un display estático con la información de los jugadores."""
        p1_display = self.player1_config['display_name']
        p2_display = self.player2_config['display_name']

        info_text = f"Jugador 1: {p1_display}\nJugador 2: {p2_display}"

        player_info_label = QLabel(info_text)
        style = """
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid #FFD700;
                border-radius: 8px;
                padding: 10px;
                font-size: 10pt;
            }
        """
        player_info_label.setStyleSheet(style)

        proxy_info = QGraphicsProxyWidget()
        proxy_info.setWidget(player_info_label)
        proxy_info.setPos(10, 600)
        self.scene.addItem(proxy_info)

    def handle_media_player_error(self, error):
        print(f"Error en QMediaPlayer: {error} - {self.place_piece_sound.errorString()}")






