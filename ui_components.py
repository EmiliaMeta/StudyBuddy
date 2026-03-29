import random

from PyQt6.QtWidgets import QProgressBar, QGridLayout, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt6.QtGui import QPainter, QColor


# ---------- SIMULATE BANNER ----------

class SimulateBanner(QWidget):
    def __init__(self, on_exit, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
        QWidget {
            background: #f59e0b;
            border-radius: 0px;
        }
        QLabel {
            background: transparent;
            color: #1c1917;
            font-weight: bold;
            font-size: 15px;
        }
        QPushButton {
            background: #1c1917;
            color: #f59e0b;
            border: none;
            padding: 4px 14px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #44403c;
        }
        """)
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)

        icon = QLabel("⚠ SIMULERINGSLÄGE — ändringar sparas inte")
        layout.addWidget(icon)
        layout.addStretch()

        exit_btn = QPushButton("Avsluta simulering")
        exit_btn.clicked.connect(on_exit)
        layout.addWidget(exit_btn)


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



# ---------- SIMULATE PANEL ----------

class SimulatePanel(QFrame):
    """Snabbval-panel som visas i simulate-läge istället för kalender."""

    def __init__(self, planner, parent=None):
        super().__init__(parent)
        self.planner = planner

        self.setStyleSheet("""
        QFrame {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #fef3c7, stop:1 #fde68a
            );
            border-radius: 10px;
            padding: 4px;
        }
        QLabel {
            background: transparent;
            font-weight: bold;
            font-size: 15px;
            color: #1c1917;
        }
        QPushButton {
            background: #f59e0b;
            color: #1c1917;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background: #d97706; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Snabbval")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:17px; font-weight:bold; background:transparent;")
        layout.addWidget(title)

        layout.addWidget(self._divider())
        layout.addWidget(QLabel("Ej avklarade kurser:"))

        btn_grade = QPushButton("Sätt betyg A på alla")
        btn_grade.clicked.connect(self._set_all_grade_a)
        layout.addWidget(btn_grade)

        btn_hp = QPushButton("Sätt max HP på alla")
        btn_hp.clicked.connect(self._set_all_max_hp)
        layout.addWidget(btn_hp)

        btn_both = QPushButton("Betyg A + max HP på alla")
        btn_both.clicked.connect(self._set_all_grade_a_and_hp)
        layout.addWidget(btn_both)

        layout.addWidget(self._divider())

        btn_reset = QPushButton("↺  Återställ simulering")
        btn_reset.setStyleSheet("""
        QPushButton {
            background: #dc2626;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background: #b91c1c; }
        """)
        btn_reset.clicked.connect(self.planner.reset_simulate)
        layout.addWidget(btn_reset)

        layout.addStretch()

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #d97706; max-height: 1px;")
        return line

    def _not_completed(self):
        return [
            c for c in self.planner.courses
            if c.status in ("planned", "in progress", "failed")
        ]

    def _not_completed_gradable(self):
        return [
            c for c in self._not_completed()
            if not c.pass_fail
        ]

    def _set_all_grade_a(self):
        for c in self._not_completed_gradable():
            c.grade = "A"
        self.planner.refresh_ui()

    def _set_all_max_hp(self):
        for c in self._not_completed():
            c.hp_done = c.hp_total
            c.status = "completed"
        self.planner.refresh_ui()

    def _set_all_grade_a_and_hp(self):
        for c in self._not_completed():
            c.hp_done = c.hp_total
            c.status = "completed"
            if not c.pass_fail:
                c.grade = "A"
        self.planner.refresh_ui()

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