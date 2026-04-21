import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QRadialGradient
from ..particle_system import ParticleSystem # Importar el sistema de partículas compartido

class MenuScreen(QWidget):
    def __init__(self, parent=None, particle_system=None):
        super().__init__(parent)
        self.setWindowTitle("Menú Principal")
        self.resize(1000, 700) # Tamaño coherente con el estilo anterior

        # Fondo azul profundo del código original
        self.background_color = QColor("#0C0E1D")
        self.particle_system = particle_system

        # --- TÍTULO ---
        self.title_label = QLabel("Menú Principal", self)
        self.title_label.setFont(QFont("Georgia", 40, QFont.Bold)) # Estilo elegante
        self.title_label.setStyleSheet("color : #FFD700; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)

        # --- ESTILO DE BOTONES (Mantenido y Refinado) ---
        btn_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid white;
                padding: 15px;
                font-size: 14pt;
                border-radius: 10px;
                min-width: 300px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
                border: 2px solid #FFD700;
            }
        """

        # Botones
        self.btn_play = QPushButton('Jugar', self)
        self.btn_play.setStyleSheet(btn_style)

        self.btn_record = QPushButton('Tabla de puntajes', self)
        self.btn_record.setStyleSheet(btn_style)

        self.btn_rules = QPushButton('Reglas del Juego', self)
        self.btn_rules.setStyleSheet(btn_style)

        self.btn_exit = QPushButton('Salir', self)
        self.btn_exit.setStyleSheet(btn_style)

        # Layout
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(self.title_label, 0, Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(self.btn_play, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.btn_record, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.btn_rules, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.btn_exit, 0, Qt.AlignCenter)
        layout.addStretch(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Dibujar el fondo azul sólido
        painter.fillRect(self.rect(), self.background_color)

        # 2. Dibujar las partículas doradas
        if self.particle_system:
            self.particle_system.draw_particles(painter)
        
        super().paintEvent(event)

    def showEvent(self, event):
        """Se llama cuando el widget se muestra."""
        super().showEvent(event)
        if self.particle_system:
            self.particle_system.start()
        self.update() # Asegurar un redibujado al mostrarse

    def hideEvent(self, event):
        """Se llama cuando el widget se oculta."""
        super().hideEvent(event)
        if self.particle_system:
            self.particle_system.stop()