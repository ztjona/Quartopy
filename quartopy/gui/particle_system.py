import random
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QBrush, QRadialGradient

class Particle:
    def __init__(self, max_width, max_height):
        self.max_w = max_width
        self.max_h = max_height
        
        # Nacimiento: En una franja estrecha cerca de la esquina superior derecha
        offset = random.uniform(-100, 100)
        self.position = QPointF(max_width + 50, -50 + offset)
        
        # Velocidad: Movimiento "arrastrado" (más rápido en X que en Y para que crucen)
        self.vx = random.uniform(-4.0, -7.0)
        self.vy = random.uniform(3.0, 5.0)
        
        self.size = random.uniform(5, 15)
        self.color = QColor(255, 215, 0, random.randint(100, 200)) # Dorado
        self.lifespan = 300  # Vida larga para que lleguen al otro lado
        self.age = 0

    def update(self):
        # Efecto de arrastre
        self.position.setX(self.position.x() + self.vx)
        self.position.setY(self.position.y() + self.vy)
        self.age += 1
        
        # Desvanecimiento al final de su vida
        if self.age > 200:
            alpha = self.color.alpha()
            if alpha > 2: self.color.setAlpha(alpha - 2)

    def is_dead(self):
        return self.age >= self.lifespan or self.position.x() < -100 or self.position.y() > self.max_h + 100

class ParticleSystem:
    def __init__(self, parent_widget, max_particles=60):
        self.parent_widget = parent_widget
        self.particles = []
        self.max_particles = max_particles
        
        self.particle_timer = QTimer(parent_widget)
        self.particle_timer.timeout.connect(self._update_and_repaint)
        # El timer se iniciará/detendrá externamente

    def _update_and_repaint(self):
        self.update_particles()
        self.parent_widget.update() # Solicita un repintado del widget padre

    def update_particles(self):
        if len(self.particles) < self.max_particles:
            self.particles.append(Particle(self.parent_widget.width(), self.parent_widget.height()))

        for particle in list(self.particles):
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)

    def draw_particles(self, painter):
        for p in self.particles:
            gradient = QRadialGradient(p.position, p.size)
            gradient.setColorAt(0, p.color)
            gradient.setColorAt(1, QColor(255, 215, 0, 0)) # Desvanecimiento
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p.position, p.size, p.size)

    def start(self):
        if not self.particle_timer.isActive():
            self.particle_timer.start(20) # Actualizar cada 20 ms

    def stop(self):
        if self.particle_timer.isActive():
            self.particle_timer.stop()
