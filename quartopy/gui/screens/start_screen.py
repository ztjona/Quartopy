import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QGraphicsColorizeEffect, QApplication
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QRadialGradient
from ..particle_system import ParticleSystem # Importar el sistema de partículas compartido

class StartScreen(QWidget):
    def __init__(self, parent=None, particle_system=None):
        super().__init__(parent)
        self.setWindowTitle('Quarto - Inicio')
        self.resize(1000, 700)
        
        self.background_color = QColor("#0C0E1D")
        self.particle_system = particle_system

        # --- TÍTULO ANIMADO (Blanco <-> Amarillo lento) ---
        self.full_text = "QUARTO"
        self.current_text = ""
        
        self.title_label = QLabel("", self)
        self.title_label.setFont(QFont("Georgia", 110, QFont.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.glow_effect = QGraphicsColorizeEffect(self)
        self.glow_effect.setColor(QColor(255, 255, 0))
        self.title_label.setGraphicsEffect(self.glow_effect)

        # Animación de resplandor
        self.glow_anim = QPropertyAnimation(self.glow_effect, b"strength")
        self.glow_anim.setDuration(4000)
        self.glow_anim.setStartValue(0.0)
        self.glow_anim.setEndValue(1.0)  
        self.glow_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.start()

        self.typewriter_timer = QTimer(self)
        self.typewriter_timer.timeout.connect(self.update_text)
        self.char_index = 0
        self.typewriter_timer.start(180)

        # --- INTERFAZ ---
        self.subtitle_label = QLabel("DESAFÍA TU MENTE", self)
        self.subtitle_label.setStyleSheet("font-size: 16pt; color: rgba(255, 255, 255, 120); letter-spacing: 10px;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.btn_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid white;
                padding: 15px;
                font-size: 14pt;
                border-radius: 10px;
                min-width: 280px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
            }
        """

        self.start_button = QPushButton('Comenzar a Jugar', self)
        self.start_button.setStyleSheet(self.btn_style)
        self.exit_button = QPushButton('Salir', self)
        self.exit_button.setStyleSheet(self.btn_style)

        layout = QVBoxLayout(self)
        layout.addStretch(2)
        layout.addWidget(self.title_label, 0, Qt.AlignCenter)
        layout.addWidget(self.subtitle_label, 0, Qt.AlignCenter)
        layout.addSpacing(60)
        layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        layout.addWidget(self.exit_button, 0, Qt.AlignCenter)
        layout.addStretch(1)

    def update_text(self):
        if self.char_index < len(self.full_text):
            self.current_text += self.full_text[self.char_index]
            self.title_label.setText(self.current_text)
            self.char_index += 1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo sólido azul profundo
        painter.fillRect(self.rect(), self.background_color)

        # Dibujar partículas con brillo radial
        if self.particle_system:
            self.particle_system.draw_particles(painter)
        
        super().paintEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self.particle_system:
            self.particle_system.start()
        self.update()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.particle_system:
            self.particle_system.stop()