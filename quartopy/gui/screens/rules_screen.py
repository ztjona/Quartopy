import sys
import random
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGridLayout, QSpacerItem
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QRadialGradient, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF, pyqtSignal

# --- CLASE DE PARTÍCULAS ---
class Particle:
    def __init__(self, max_width, max_height):
        self.max_w = max_width
        self.max_h = max_height
        offset = random.uniform(-100, 100)
        self.position = QPointF(max_width + 50, -50 + offset)
        self.vx = random.uniform(-4.0, -7.0)
        self.vy = random.uniform(3.0, 5.0)
        self.size = random.uniform(5, 15)
        self.color = QColor(255, 215, 0, random.randint(100, 200))
        self.lifespan = 300
        self.age = 0

    def update(self):
        self.position.setX(self.position.x() + self.vx)
        self.position.setY(self.position.y() + self.vy)
        self.age += 1
        if self.age > 200:
            alpha = self.color.alpha()
            if alpha > 2: self.color.setAlpha(max(0, alpha - 2))

    def is_dead(self):
        return self.age >= self.lifespan or self.position.x() < -100

class RulesScreen(QWidget):
    back_to_menu_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guía Suprema de Quarto")
        self.showFullScreen()

        # Colores Estéticos
        self.azul_oscuro = "#0C0E1D"
        self.dorado = "#C9C60B"
        self.blanco = "#ffffff"
        self.azul_panel = "rgba(255, 255, 255, 15)" # Blanco ultra traslúcido para elegancia

        # Sistema de Partículas
        self.particles = []
        self.particle_timer = QTimer(self)
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(20)

        self.setup_ui()

    def setup_ui(self):
        # Layout principal con márgenes generosos
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(40)

        # --- HEADER ---
        title_label = QLabel("REGLAS DE QUARTO")
        title_label.setFont(QFont("Georgia", 50, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.dorado}; background: transparent; letter-spacing: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # --- CONTENEDOR DE COLUMNAS ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(50)

        # IZQUIERDA: Bloques de Información (Texto)
        info_column = QVBoxLayout()
        info_column.setSpacing(20)
        
        self.crear_bloque_texto(info_column, "EL OBJETIVO", 
                               "Debes alinear 4 piezas que compartan al menos una característica común en una línea horizontal, vertical o diagonal.")
        
        self.crear_bloque_texto(info_column, "DINÁMICA ÚNICA", 
                               "¡Tú no eliges tu pieza! Tu oponente selecciona la pieza que debes colocar en el tablero.")
        
        self.crear_bloque_texto(info_column, "CARACTERÍSTICAS", 
                               "• Color: Claro / Oscuro\n\n• Altura: Alta / Baja\n\n• Forma: Redonda / Cuadrada\n\n• Cima: Hueca / Plana")

        info_column.addStretch() # Empuja el botón hacia abajo
        
        self.btn_close = QPushButton("VOLVER AL MENÚ")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setFixedHeight(60)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                color: {self.dorado}; 
                border: 2px solid {self.dorado};
                font-size: 14pt; font-weight: bold; border-radius: 30px;
            }}
            QPushButton:hover {{ 
                background-color: {self.dorado}; 
                color: {self.azul_oscuro}; 
            }}
        """)
        self.btn_close.clicked.connect(self.back_to_menu_signal.emit) 
        info_column.addWidget(self.btn_close)
        
        content_layout.addLayout(info_column, 2) # Proporción 2

        # DERECHA: Galería de Victorias (Imágenes)
        grid_container = QFrame()
        # Fondo oscuro sutil sin bordes amarillos exteriores
        grid_container.setStyleSheet("background-color: rgba(0,0,0,80); border-radius: 20px;")
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(30, 30, 30, 30)
        grid_layout.setSpacing(25)

        self.insertar_imagen(grid_layout, 0, 0, "VERTICAL", "quartopy/gui/assets/images/wc_vertical.jpeg")
        self.insertar_imagen(grid_layout, 0, 1, "HORIZONTAL", "quartopy/gui/assets/images/wc_horizontal.jpeg")
        self.insertar_imagen(grid_layout, 1, 0, "DIAGONAL", "quartopy/gui/assets/images/wc_diagonal.jpeg")
        self.insertar_imagen(grid_layout, 1, 1, "CUADRADO (2x2)", "quartopy/gui/assets/images/wc_2x2.jpeg")
        
        content_layout.addWidget(grid_container, 3) # Proporción 3 (más ancha para imágenes)

        main_layout.addLayout(content_layout)

    def crear_bloque_texto(self, layout, titulo, contenido):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.azul_panel}; 
                border-left: 4px solid {self.dorado}; 
                border-radius: 5px;
            }}
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(20, 15, 20, 15)
        
        t = QLabel(titulo.upper())
        t.setStyleSheet(f"color: {self.dorado}; font-weight: bold; font-size: 13pt; border: none; background: transparent;")
        
        c = QLabel(contenido)
        c.setWordWrap(True)
        c.setStyleSheet("color: white; font-size: 11pt; border: none; background: transparent; line-height: 150%;")
        
        vbox.addWidget(t)
        vbox.addWidget(c)
        layout.addWidget(frame)

    def insertar_imagen(self, layout, row, col, titulo, ruta_relativa):
        container = QVBoxLayout()
        container.setSpacing(10)
        
        t = QLabel(titulo)
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("color: rgba(255,255,255,180); font-weight: bold; font-size: 10pt; background: transparent;")

        img_label = QLabel()
        img_label.setFixedSize(220, 220) # Aumentado el tamaño
        img_label.setAlignment(Qt.AlignCenter)
        # Eliminado el borde amarillo, ahora solo un fondo negro limpio o borde gris muy sutil
        img_label.setStyleSheet("border-radius: 10px; background: #000; border: 1px solid rgba(255,255,255,30);")

        base_path = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.abspath(ruta_relativa)
        if not os.path.exists(abs_path):
            abs_path = os.path.normpath(os.path.join(base_path, "..", "..", "..", ruta_relativa))

        if os.path.exists(abs_path):
            pix = QPixmap(abs_path)
            img_label.setPixmap(pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText("Imagen\nno encontrada")
            img_label.setStyleSheet("color: #444; font-size: 8pt; border: 1px dashed #444; border-radius: 10px;")

        container.addWidget(t)
        container.addWidget(img_label, alignment=Qt.AlignCenter)
        layout.addLayout(container, row, col)

    def update_particles(self):
        if len(self.particles) < 50:
            self.particles.append(Particle(self.width(), self.height()))
        for p in list(self.particles):
            p.update()
            if p.is_dead(): self.particles.remove(p)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.azul_oscuro))
        for p in self.particles:
            grad = QRadialGradient(p.position, p.size)
            grad.setColorAt(0, p.color)
            grad.setColorAt(1, QColor(255, 215, 0, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p.position, p.size, p.size)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RulesScreen()
    window.show()
    sys.exit(app.exec_())