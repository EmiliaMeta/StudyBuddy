import random

from PyQt6.QtWidgets import QProgressBar, QGridLayout, QWidget
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt6.QtGui import QPainter, QColor


# ---------- PROGRESS BARS ----------

def style_bar(bar, color1, color2):
    bar.setStyleSheet(f"""
    QProgressBar {{
        border-radius: 6px;
        background-color: #e6e6e6;
        text-align: center;
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {color1},
            stop:1 {color2}
        );
        border-radius: 4px;
    }}
    """)


def create_progress_bars():
    bars = {
        "it_program": QProgressBar(),
        "completed":  QProgressBar(),
        "matnat":     QProgressBar(),
        "it_block":   QProgressBar()
    }

    bars["it_program"].setMaximum(180)
    bars["completed"].setMaximum(180)
    bars["matnat"].setMaximum(15)
    bars["it_block"].setMaximum(21)

    style_bar(bars["it_program"], "#3b82f6", "#1d4ed8")
    style_bar(bars["completed"],  "#4ade80", "#16a34a")
    style_bar(bars["matnat"],     "#8e90d0", "#6569cf")
    style_bar(bars["it_block"],   "#e585d5", "#e35ccd")

    layout = QGridLayout()
    layout.addWidget(bars["it_program"], 0, 0)
    layout.addWidget(bars["completed"],  1, 0)
    layout.addWidget(bars["matnat"],     0, 1)
    layout.addWidget(bars["it_block"],   1, 1)
    layout.setHorizontalSpacing(15)
    layout.setVerticalSpacing(6)

    for bar in bars.values():
        bar.setFixedHeight(26)

    return {"bars": bars, "layout": layout}


def animate_bar_success(bar):
    """Flash the bar green briefly on completion."""
    original = bar.styleSheet()
    flash = original + "QProgressBar::chunk { background: #22c55e; }"
    bar.setStyleSheet(flash)
    QTimer.singleShot(600, lambda: bar.setStyleSheet(original))


# ---------- CONFETTI ----------

class ConfettiWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.particles = []

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)

        QTimer.singleShot(0, self._start)

    def _start(self):
        self.resize(self.parent().size())
        self.raise_()
        self.show()
        self.generate_particles()
        self.timer.start(16)  # ~60fps

    def generate_particles(self):
        self.particles = []
        shapes = ["rect", "circle", "line"]

        for _ in range(120):
            self.particles.append({
                "x":         random.uniform(0, self.width()),
                "y":         random.uniform(-80, -4),
                "vx":        random.uniform(-1.5, 1.5),
                "vy":        random.uniform(3, 7),
                "rotation":  random.uniform(0, 360),
                "rot_speed": random.uniform(-6, 6),
                "shape":     random.choice(shapes),
                "w":         random.randint(6, 14),
                "h":         random.randint(4, 10),
                "color":     QColor(
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255),
                    220
                )
            })

    def update_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.08  # gravity
            p["rotation"] += p["rot_speed"]

        self.update()

        if all(p["y"] > self.height() for p in self.particles):
            self.timer.stop()
            self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for p in self.particles:
            painter.save()
            painter.translate(int(p["x"]), int(p["y"]))
            painter.rotate(p["rotation"])
            painter.setBrush(p["color"])
            painter.setPen(Qt.PenStyle.NoPen)

            w, h = int(p["w"]), int(p["h"])

            if p["shape"] == "circle":
                painter.drawEllipse(-w//2, -h//2, w, h)
            elif p["shape"] == "rect":
                painter.drawRect(-w//2, -h//2, w, h)
            else:
                painter.setPen(p["color"])
                painter.drawLine(-w//2, 0, w//2, 0)

            painter.restore()