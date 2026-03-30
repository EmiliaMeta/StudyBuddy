import random

from PyQt6.QtWidgets import (
    QProgressBar, QGridLayout, QWidget, QLabel, QHBoxLayout,
    QPushButton, QSpinBox, QFrame, QVBoxLayout, QSlider,
    QLineEdit, QCheckBox, QComboBox, QTabWidget, QTextEdit,
    QSizePolicy
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QFont


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

    bars["it_program"].setMaximum(1800)
    bars["completed"].setMaximum(1800)
    bars["matnat"].setMaximum(150)
    bars["it_block"].setMaximum(210)

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

        title = QLabel("⚡ Snabbval")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:17px; font-weight:bold; background:transparent;")
        layout.addWidget(title)

        # Veckor förbrukade
        weeks_row = QHBoxLayout()
        weeks_label = QLabel("Förbrukade veckor:")
        weeks_label.setStyleSheet("background:transparent; font-size:13px;")

        self.weeks_spin = QSpinBox()
        self.weeks_spin.setRange(0, 220)
        self.weeks_spin.setValue(planner.csn_weeks_used)
        self.weeks_spin.setSuffix(" v")
        self.weeks_spin.valueChanged.connect(self._on_weeks_changed)

        weeks_row.addWidget(weeks_label)
        weeks_row.addWidget(self.weeks_spin)
        layout.addLayout(weeks_row)

        layout.addWidget(self._divider())
        layout.addWidget(QLabel("Ej avklarade kurser:"))

        for grade in ["A", "B", "C", "D", "E"]:
            btn = QPushButton(f"🎓  Sätt betyg {grade} på alla")
            btn.clicked.connect(lambda checked, g=grade: self._set_all_grade(g))
            layout.addWidget(btn)

        btn_hp = QPushButton("✅  Sätt max HP på alla")
        btn_hp.clicked.connect(self._set_all_max_hp)
        layout.addWidget(btn_hp)

        btn_both = QPushButton("🚀  Betyg A + max HP på alla")
        btn_both.clicked.connect(self._set_all_grade_a_and_hp)
        layout.addWidget(btn_both)

        layout.addWidget(self._divider())

        btn_reset_hp = QPushButton("⬜  Nollställ alla HP + betyg")
        btn_reset_hp.setStyleSheet("""
        QPushButton {
            background: #7c3aed;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
        QPushButton:hover { background: #6d28d9; }
        """)
        btn_reset_hp.clicked.connect(self._reset_all_hp_and_grades)
        layout.addWidget(btn_reset_hp)

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

    def _on_weeks_changed(self, value):
        self.planner.csn_weeks_used = value
        self.planner.update_hp_labels()

    def _reset_all_hp_and_grades(self):
        for c in self.planner.courses:
            c.hp_done = 0
            c.grade = None
            if c.status not in ("planned", "failed"):
                c.status = "planned"
        self.planner.refresh_ui()

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

    def _set_all_grade(self, grade):
        for c in self._not_completed_gradable():
            c.grade = grade
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


# ---------- EDIT PANEL ----------

class EditPanel(QWidget):
    """Sidopanel som glider in från höger för att redigera en kurs."""

    PANEL_WIDTH = 340

    def __init__(self, planner, kth_db=None):
        super().__init__(planner)
        self.planner    = planner
        self.kth_db     = kth_db or {}
        self.course     = None
        self._anim      = None

        self.setFixedWidth(self.PANEL_WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            EditPanel {
                background: #F3B9C7;
                border-left: 2px solid #A45FA0;
            }
            QLabel { background: transparent; }
            QLineEdit, QTextEdit {
                background: white;
                border: 1px solid #D4A0C8;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background: #A45FA0;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7D4B7D; }
            QSlider::groove:horizontal {
                height: 6px;
                background: #D4A0C8;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #A45FA0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 18px; height: 18px;
                margin: -6px 0;
                background: white;
                border: 2px solid #A45FA0;
                border-radius: 9px;
            }
        """)

        self._build_ui()
        self.hide()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("Redigera kurs")
        self.title_label.setStyleSheet("font-size:16px; font-weight:bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #A45FA0;
                font-size:16px; border:none; padding:0; }
            QPushButton:hover { background: #EFCDD6; border-radius:14px; }
        """)
        close_btn.clicked.connect(self.slide_out)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(close_btn)
        outer.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #EFCDD6; padding: 6px 14px;
                border-radius: 6px; margin-right: 4px;
            }
            QTabBar::tab:selected { background: #A45FA0; color: white; }
        """)

        # --- TAB 1: Grundinfo ---
        basic = QWidget()
        basic.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(basic)
        bl.setSpacing(8)

        # Kod
        bl.addWidget(self._lbl("Kurskod"))
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("t.ex. DD1351")
        bl.addWidget(self.code_edit)

        # Namn
        bl.addWidget(self._lbl("Kursnamn"))
        self.name_edit = QLineEdit()
        bl.addWidget(self.name_edit)

        # HP (readonly om i DB)
        self.hp_label = QLabel("HP: 7.5")
        self.hp_label.setStyleSheet(
            "font-size:13px; color:#7D4B7D; background:transparent;")
        bl.addWidget(self.hp_label)

        # HP-slider
        bl.addWidget(self._lbl("Avklarade HP"))
        self.hp_row = QHBoxLayout()
        self.hp_slider = QSlider(Qt.Orientation.Horizontal)
        self.hp_slider.setMinimum(0)
        self.hp_slider.setMaximum(100)  # skalas mot hp_total
        self.hp_slider.valueChanged.connect(self._on_slider)
        self.hp_value_label = QLabel("0")
        self.hp_value_label.setFixedWidth(36)
        self.hp_value_label.setStyleSheet(
            "font-weight:bold; background:transparent;")
        self.hp_row.addWidget(self.hp_slider)
        self.hp_row.addWidget(self.hp_value_label)
        bl.addLayout(self.hp_row)

        # Betyg
        bl.addWidget(self._lbl("Betyg"))
        grade_row = QHBoxLayout()
        self.grade_btns = {}
        for g in ["", "A", "B", "C", "D", "E", "F"]:
            btn = QPushButton(g if g else "—")
            btn.setFixedSize(36, 36)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background:#EFCDD6; color:#4B1528;
                    border:none; border-radius:18px; font-weight:bold; font-size:12px; }
                QPushButton:checked { background:#A45FA0; color:white; }
                QPushButton:hover { background:#D4A0C8; }
            """)
            btn.clicked.connect(lambda _, gv=g: self._set_grade(gv))
            self.grade_btns[g] = btn
            grade_row.addWidget(btn)
        grade_row.addStretch()
        bl.addLayout(grade_row)

        # Pass/Fail + Source
        pf_src_row = QHBoxLayout()

        self.pf_check = QCheckBox("Pass/Fail")
        self.pf_check.toggled.connect(self._on_pf_toggled)
        pf_src_row.addWidget(self.pf_check)

        pf_src_row.addStretch()

        self.src_it_btn = QPushButton("IT")
        self.src_ext_btn = QPushButton("Extern")
        for btn in [self.src_it_btn, self.src_ext_btn]:
            btn.setCheckable(True)
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton { background:#EFCDD6; color:#4B1528;
                    border:none; border-radius:6px; padding:0 10px; font-size:12px; }
                QPushButton:checked { background:#A45FA0; color:white; }
            """)
        self.src_it_btn.clicked.connect(lambda: self._set_source("IT"))
        self.src_ext_btn.clicked.connect(lambda: self._set_source("external"))
        pf_src_row.addWidget(self.src_it_btn)
        pf_src_row.addWidget(self.src_ext_btn)
        bl.addLayout(pf_src_row)

        bl.addStretch()
        tabs.addTab(basic, "Grundinfo")

        # --- TAB 2: Detaljer ---
        details = QWidget()
        details.setStyleSheet("background: transparent;")
        dl = QVBoxLayout(details)
        dl.setSpacing(8)

        dl.addWidget(self._lbl("Prerequisites"))
        self.prereq_edit = QLineEdit()
        self.prereq_edit.setPlaceholderText(
            ", för OR och ; för AND  (ex: ID1018 ; IS1200)")
        dl.addWidget(self.prereq_edit)

        dl.addWidget(self._lbl("Anteckningar"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(80)
        dl.addWidget(self.notes_edit)

        dl.addWidget(self._lbl("Viktiga datum"))
        self.dates_edit = QLineEdit()
        self.dates_edit.setPlaceholderText(
            "Titel - YYYY-MM-DD, Titel - YYYY-MM-DD")
        dl.addWidget(self.dates_edit)

        dl.addStretch()
        tabs.addTab(details, "Detaljer")

        outer.addWidget(tabs)

        # Knappar
        self.save_btn = QPushButton("Spara")
        self.save_btn.clicked.connect(self._save)
        outer.addWidget(self.save_btn)

        self.delete_btn = QPushButton("Ta bort kurs")
        self.delete_btn.setStyleSheet("""
            QPushButton { background:#dc2626; color:white; border:none;
                padding:8px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#b91c1c; }
        """)
        self.delete_btn.clicked.connect(self._delete)
        outer.addWidget(self.delete_btn)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "font-size:12px; color:#7D4B7D; font-weight:bold; background:transparent;")
        return l

    def _on_slider(self, value):
        if not self.course:
            return
        hp = value * 0.5
        self.hp_value_label.setText(str(hp))

    def _set_grade(self, grade):
        for g, btn in self.grade_btns.items():
            btn.setChecked(g == grade)

    def _set_source(self, source):
        self.src_it_btn.setChecked(source == "IT")
        self.src_ext_btn.setChecked(source == "external")

    def _on_pf_toggled(self, checked):
        for btn in self.grade_btns.values():
            btn.setEnabled(not checked)
        if checked:
            self._set_grade("")

    def load_course(self, course):
        self.course = course
        self.title_label.setText(course.code)

        # Grundinfo
        self.code_edit.setText(course.code)
        self.name_edit.setText(course.name)
        self.hp_label.setText(f"HP: {course.hp_total}")

        # Slider — varje steg = 0.5 HP
        self.hp_slider.setMaximum(int(course.hp_total * 2))
        self.hp_slider.setValue(int(course.hp_done * 2))
        self.hp_value_label.setText(str(course.hp_done))

        # Betyg
        self._set_grade(course.grade or "")
        self._on_pf_toggled(course.pass_fail)
        self.pf_check.setChecked(course.pass_fail)

        # Source
        self._set_source(course.source)

        # HP readonly om i DB
        in_db = course.code.upper() in self.kth_db
        self.hp_label.setVisible(True)

        # Detaljer
        from dialogs import prerequisites_to_text, text_to_prerequisites
        self.prereq_edit.setText(prerequisites_to_text(course.prerequisites))

        dates_text = ""
        if course.important_dates:
            dates_text = ", ".join(
                f"{d['title']} - {d['date']}"
                for d in course.important_dates
            )
        self.dates_edit.setText(dates_text)
        self.notes_edit.setPlainText(course.notes or "")

    def _save(self):
        from dialogs import text_to_prerequisites
        from storage import save_courses

        c = self.course
        c.code  = self.code_edit.text().upper()
        c.name  = self.name_edit.text()

        # HP från slider (varje steg = 0.5 HP)
        c.hp_done = self.hp_slider.value() * 0.5

        # Automatisk status
        if c.hp_done >= c.hp_total and c.hp_total > 0:
            c.status = "completed"
        elif c.hp_done > 0:
            c.status = "in progress"

        # Betyg
        grade = next(
            (g for g, btn in self.grade_btns.items() if btn.isChecked()), "")
        c.grade    = grade or None
        c.pass_fail = self.pf_check.isChecked()
        c.source   = "IT" if self.src_it_btn.isChecked() else "external"

        # Detaljer
        c.prerequisites = text_to_prerequisites(self.prereq_edit.text())
        c.notes = self.notes_edit.toPlainText().strip() or None

        dates_list = []
        text = self.dates_edit.text().strip()
        if text:
            for item in text.split(","):
                item = item.strip()
                if "-" in item:
                    title, date = item.split("-", 1)
                    dates_list.append(
                        {"title": title.strip(), "date": date.strip()})
        c.important_dates = dates_list

        save_courses(self.planner.courses, simulate=self.planner.simulate)
        self.planner.refresh_ui()
        self.slide_out()

    def _delete(self):
        from storage import save_courses
        self.planner.courses.remove(self.course)
        save_courses(self.planner.courses, simulate=self.planner.simulate)
        self.planner.refresh_ui()
        self.slide_out()

    # ---------- ANIMATION ----------

    def slide_in(self):
        parent = self.parent()
        h = parent.height()
        self.setGeometry(parent.width(), 0, self.PANEL_WIDTH, h)
        self.show()
        self.raise_()

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(250)
        self._anim.setStartValue(QRect(parent.width(), 0, self.PANEL_WIDTH, h))
        self._anim.setEndValue(
            QRect(parent.width() - self.PANEL_WIDTH, 0, self.PANEL_WIDTH, h))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def slide_out(self):
        parent = self.parent()
        h = parent.height()

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(200)
        self._anim.setStartValue(
            QRect(parent.width() - self.PANEL_WIDTH, 0, self.PANEL_WIDTH, h))
        self._anim.setEndValue(
            QRect(parent.width(), 0, self.PANEL_WIDTH, h))
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    def resizeEvent(self, event):
        if self.isVisible():
            parent = self.parent()
            self.setGeometry(
                parent.width() - self.PANEL_WIDTH, 0,
                self.PANEL_WIDTH, parent.height())