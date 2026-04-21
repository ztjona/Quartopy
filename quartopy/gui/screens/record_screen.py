import os
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt, pyqtSignal

class RecordScreen(QWidget):
    """Pantalla para mostrar los records de puntuación desde archivos CSV."""
    
    back_to_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.records_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'partidas_guardadas')
        self.setup_ui()
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 30, 50, 30)
        
        title_label = QLabel("TABLA DE PUNTUACIONES")
        title_label.setFont(QFont("Arial", 28, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #FFD700; padding: 15px;")
        layout.addWidget(title_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ganador", "Número de Movimientos"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #333333; color: #FFD700; font-weight: bold;
                font-size: 16px; padding: 15px; border: none;
                border-bottom: 2px solid #FFD700;
            }
        """)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a; border: 2px solid #FFD700;
                border-radius: 8px; gridline-color: #555555; font-size: 14px;
            }
            QTableWidget::item { padding: 12px; border-bottom: 1px solid #444444; }
        """)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        buttons_layout = QHBoxLayout()
        self.btn_back = QPushButton("Volver al Menú")
        self.btn_back.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_back.setFixedSize(200, 50)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FFD700; color: black; border: 2px solid #FFC400;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #FFC400; }
        """)
        self.btn_back.clicked.connect(self.back_to_menu.emit)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_back)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)

    def load_records(self):
        """
        Carga los datos desde los archivos CSV, encuentra la mejor partida de cada
        jugador y muestra los 10 mejores en una tabla.
        """
        if not os.path.exists(self.records_path):
            self.display_no_data()
            return

        files = [f for f in os.listdir(self.records_path) if f.endswith('.csv')]
        best_scores = {}

        for file_name in files:
            file_path = os.path.join(self.records_path, file_name)
            try:
                with open(file_path, 'r', newline='') as csvfile:
                    lines = list(csv.reader(csvfile))
                    lines = [line for line in lines if line] # Filtrar líneas vacías
                    
                    if len(lines) < 2:
                        continue
                    
                    last_line = lines[-1]
                    winner = "Empate" 
                    if last_line[0].lower() == 'ganador':
                        winner = last_line[1]

                    if winner == "Empate":
                        continue

                    try:
                        moves = int(lines[-2][0])
                        # Si el jugador ya tiene un récord, solo actualizar si es mejor (menos movimientos)
                        if winner not in best_scores or moves < best_scores[winner]:
                            best_scores[winner] = moves
                    except (ValueError, IndexError):
                        continue

            except Exception as e:
                print(f"Error al leer el archivo {file_name}: {e}")

        if not best_scores:
            self.display_no_data()
            return

        # Convertir el diccionario de mejores puntuaciones a una lista de diccionarios
        records_list = [{'winner': player, 'moves': score} for player, score in best_scores.items()]
        
        # Ordenar por número de movimientos (ascendente)
        sorted_records = sorted(records_list, key=lambda x: x['moves'])
        
        # Mostrar solo los 10 mejores
        top_10_records = sorted_records[:10]
        
        self.table.setRowCount(len(top_10_records))
        for i, record in enumerate(top_10_records):
            winner_item = QTableWidgetItem(record['winner'])
            moves_item = QTableWidgetItem(str(record['moves']))
            
            winner_item.setTextAlignment(Qt.AlignCenter)
            moves_item.setTextAlignment(Qt.AlignCenter)

            if i == 0: color = QColor("#FFD700")  # Oro
            elif i == 1: color = QColor("#C0C0C0")  # Plata
            elif i == 2: color = QColor("#CD7F32")  # Bronce
            else: color = QColor("white")
            
            winner_item.setForeground(QBrush(color))
            moves_item.setForeground(QBrush(color))
            
            self.table.setItem(i, 0, winner_item)
            self.table.setItem(i, 1, moves_item)

    def display_no_data(self):
        """Muestra un mensaje en la tabla cuando no hay datos."""
        self.table.setRowCount(1)
        self.table.setSpan(0, 0, 1, 2) # Unir las dos columnas
        no_data_item = QTableWidgetItem("No hay partidas guardadas para mostrar.")
        no_data_item.setTextAlignment(Qt.AlignCenter)
        no_data_item.setFont(QFont("Arial", 14))
        no_data_item.setForeground(QBrush(QColor("gray")))
        self.table.setItem(0, 0, no_data_item)

    def showEvent(self, event):
        """Se ejecuta cuando el widget se muestra. Recarga los datos."""
        super().showEvent(event)
        self.load_records()