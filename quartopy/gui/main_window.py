from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QWidget, QLabel
from quartopy.gui.screens.start_screen import StartScreen
from quartopy.gui.screens.menu_screen import MenuScreen
from quartopy.gui.screens.game_board import GameBoard
from quartopy.gui.screens.type_player import TypePlayerScreen
from quartopy.gui.screens.record_screen import RecordScreen
from quartopy.gui.screens.rules_screen import RulesScreen
from quartopy.gui.particle_system import ParticleSystem # Importar ParticleSystem

class MainWindow(QMainWindow):
    """
    La ventana principal de la aplicación. Actúa como un gestor de pilas (Stack)
    para cambiar entre diferentes pantallas (Inicio, Menú, Tablero).
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Juego Quarto')
        self.showFullScreen()
        
        # Crea el QStackedWidget que contendrá todas las pantallas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Inicializa el sistema de partículas compartido, usando self (MainWindow) como parent
        self.particle_system = ParticleSystem(parent_widget=self)

        # Inicializa las pantallas, pasando 'self' como parent y el sistema de partículas
        self.start_screen = StartScreen(parent=self, particle_system=self.particle_system)
        self.menu_screen = MenuScreen(parent=self, particle_system=self.particle_system)
        self.game_board = None # Se creará dinámicamente
        self.type_player = TypePlayerScreen(parent=self)
        self.record_screen = RecordScreen(parent=self)
        self.rules_screen = RulesScreen(parent=self) # Inicializar RulesScreen

        # Añade las pantallas al StackedWidget
        # Guardamos un índice para referenciar cada pantalla:
        self.stacked_widget.addWidget(self.start_screen) # Índice 0: Pantalla de Inicio
        self.stacked_widget.addWidget(self.menu_screen)  # Índice 1: Pantalla de Menú
        self.stacked_widget.addWidget(self.record_screen) # Añadido para la pantalla de records
        self.stacked_widget.addWidget(self.rules_screen) # Añadir RulesScreen
        self.stacked_widget.addWidget(self.type_player) # type_player también debe estar en el stack para gestionarlo

        # Conexiones: Conecta la señal de la pantalla de inicio a la función de navegación
        self.start_screen.start_button.clicked.connect(self.show_menu)
        self.start_screen.exit_button.clicked.connect(self.close)

        # Conexiones específicas de los botones del menú a los métodos de MainWindow
        self.menu_screen.btn_play.clicked.connect(self.show_type_player)
        self.menu_screen.btn_exit.clicked.connect(self.close) # Conexión directa a cerrar MainWindow
        self.menu_screen.btn_record.clicked.connect(self.show_record_screen)
        self.menu_screen.btn_rules.clicked.connect(self.show_rules_screen)

        # Conexiones de otras pantallas
        self.record_screen.back_to_menu.connect(self.show_menu)
        self.type_player.back_btn.clicked.connect(self.show_menu) # Volver al menú
        self.type_player.players_selected.connect(self.start_game_with_config)
        self.rules_screen.back_to_menu_signal.connect(self.show_menu) # Conexión de RulesScreen para volver al menú


        # Muestra la pantalla inicial al comenzar
        self.stacked_widget.setCurrentIndex(0) # Muestra la StartScreen
        

    def show_menu(self):
        """Muestra la pantalla del menú."""
        print("MainWindow: show_menu llamado.")
        self.stacked_widget.setCurrentWidget(self.menu_screen)
        
    def show_start(self):
        """Muestra la pantalla de inicio."""
        self.stacked_widget.setCurrentWidget(self.start_screen)

    def show_record_screen(self):
        """Muestra la pantalla de records."""
        self.stacked_widget.setCurrentWidget(self.record_screen)

    def show_rules_screen(self):
        """Muestra la pantalla de reglas."""
        print("MainWindow: show_rules_screen llamado.")
        self.stacked_widget.setCurrentWidget(self.rules_screen)

    def show_type_player(self):
        """Muestra la pantalla de selección de tipo de jugador."""
        self.stacked_widget.setCurrentWidget(self.type_player)

    def show_game(self):
        """Muestra la pantalla del tablero de juego."""
        # Este método necesitaría una lógica para el GameBoard una vez creado
        # self.stacked_widget.setCurrentIndex(2) # El índice podría variar
        pass
        # if self.game_board and hasattr(self.game_board, 'view'):
        #     # Desactiva la barra de desplazamiento horizontal
        #     self.game_board.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #     # Desactiva la barra de desplazamiento vertical
        #     self.game_board.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def start_game_with_config(self, config: dict):
        # self.type_player.close() # No es necesario cerrar, solo cambiar de widget
        
        """
        Crea una nueva instancia de GameBoard con la configuración de jugadores
        y modo 2x2 seleccionada, y la muestra.
        """
        player1_config_dict = config['player1_config']
        player2_config_dict = config['player2_config']
        player1_name = config['player1_name']
        player2_name = config['player2_name']
        mode_2x2 = config['mode_2x2']

        # Remover el GameBoard antiguo si existe
        if self.game_board:
            # Asegurarse de que el widget no sea None antes de intentar removerlo
            if self.stacked_widget.indexOf(self.game_board) != -1:
                self.stacked_widget.removeWidget(self.game_board)
            self.game_board.deleteLater() # Asegura que el objeto sea eliminado
        
        # Crear nueva instancia de GameBoard con la configuración
        self.game_board = GameBoard(
            parent=self, 
            player1_config=player1_config_dict, 
            player2_config=player2_config_dict,
            player1_name=player1_name,
            player2_name=player2_name,
            mode_2x2=mode_2x2
        )
        # Re-conectar la señal para volver al menú
        self.game_board.back_to_menu_signal.connect(self.show_menu)

        self.stacked_widget.addWidget(self.game_board)
        self.stacked_widget.setCurrentWidget(self.game_board) # Mostrar el nuevo GameBoard
        
        if self.game_board and hasattr(self.game_board, 'view'):
            self.game_board.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.game_board.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # El método closeMini1 ya no es necesario, se usa show_menu para volver
    def closeEvent(self, event):
        """Se llama cuando la ventana principal se está cerrando."""
        print("MainWindow: closeEvent llamado. La aplicación se está cerrando.")
        super().closeEvent(event)