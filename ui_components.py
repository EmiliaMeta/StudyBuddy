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
        bar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

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


# ---------- PROFILE PANEL ----------

class ProfilePanel(QWidget):
    """Sidopanel för användarprofil och programval."""

    PANEL_WIDTH = 380

    def __init__(self, planner):
        super().__init__(planner)
        self.planner = planner
        self._anim   = None

        self.setFixedWidth(self.PANEL_WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            ProfilePanel {
                background: #F3B9C7;
                border-left: 2px solid #A45FA0;
            }
            QLabel { background: transparent; }
            QLineEdit, QComboBox {
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
        """)

        self._build_ui()
        self.hide()

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "font-size:12px; color:#7D4B7D; font-weight:bold; background:transparent;")
        return l

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Profil")
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#A45FA0;
                font-size:16px; border:none; padding:0; }
            QPushButton:hover { background:#EFCDD6; border-radius:14px; }
        """)
        close_btn.clicked.connect(self.slide_out)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        outer.addLayout(header)

        # Namn
        outer.addWidget(self._lbl("Namn"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ditt namn")
        outer.addWidget(self.name_edit)

        # Program
        outer.addWidget(self._lbl("Program"))
        self.program_combo = QComboBox()
        self.program_combo.setEditable(True)
        self.program_combo.lineEdit().setPlaceholderText(
            "Sök programkod eller namn...")
        outer.addWidget(self.program_combo)

        # Nivå
        outer.addWidget(self._lbl("Nivå"))
        level_row = QHBoxLayout()
        self.kandidat_btn = QPushButton("Kandidat")
        self.master_btn   = QPushButton("Master/Civilingenjör")
        for btn in [self.kandidat_btn, self.master_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background:#EFCDD6; color:#4B1528;
                    border:none; border-radius:6px; padding:6px 12px; }
                QPushButton:checked { background:#A45FA0; color:white; }
            """)
        self.kandidat_btn.clicked.connect(lambda: self._set_level("kandidat"))
        self.master_btn.clicked.connect(lambda: self._set_level("master"))
        self.kandidat_btn.clicked.connect(self._update_csn_status)
        self.master_btn.clicked.connect(self._update_csn_status)
        level_row.addWidget(self.kandidat_btn)
        level_row.addWidget(self.master_btn)
        outer.addLayout(level_row)

        outer.addStretch()

        # Grade Average
        outer.addWidget(self._lbl("Grade Average"))
        self.grade_frame = QFrame()
        self.grade_frame.setStyleSheet("""
            QFrame { background:#EFCDD6; border-radius:8px; }
            QLabel { background:transparent; }
        """)
        grade_inner = QVBoxLayout(self.grade_frame)
        grade_inner.setContentsMargins(10, 8, 10, 8)
        grade_inner.setSpacing(2)
        self.grade_display = QLabel("-")
        self.grade_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_display.setStyleSheet("font-size:28px; font-weight:bold; color:#4B1528;")
        self.grade_sub = QLabel("")
        self.grade_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_sub.setStyleSheet("font-size:13px; color:#7D4B7D;")
        grade_inner.addWidget(self.grade_display)
        grade_inner.addWidget(self.grade_sub)
        outer.addWidget(self.grade_frame)

        # CSN-info
        outer.addWidget(self._lbl("CSN-status"))
        csn_frame = QFrame()
        csn_frame.setStyleSheet("""
            QFrame { background:#EFCDD6; border-radius:8px; }
            QLabel { background:transparent; }
        """)
        csn_inner = QVBoxLayout(csn_frame)
        csn_inner.setSpacing(4)
        csn_inner.setContentsMargins(10, 8, 10, 8)

        weeks_row = QHBoxLayout()
        weeks_lbl = QLabel("Förbrukade veckor:")
        weeks_lbl.setStyleSheet("font-size:12px; color:#7D4B7D;")
        self.csn_spin = QLineEdit()
        self.csn_spin.setPlaceholderText("0")
        self.csn_spin.setFixedWidth(60)
        self.csn_spin.setStyleSheet(
            "background:white; border:1px solid #D4A0C8; border-radius:6px; padding:4px;")
        weeks_row.addWidget(weeks_lbl)
        weeks_row.addWidget(self.csn_spin)
        csn_inner.addLayout(weeks_row)

        self.csn_status_label = QLabel("")
        self.csn_status_label.setWordWrap(True)
        self.csn_status_label.setStyleSheet("font-size:13px; color:#4B1528;")
        csn_inner.addWidget(self.csn_status_label)

        outer.addWidget(csn_frame)

        # Masterprogram (valfritt)
        outer.addWidget(self._lbl("Masterprogram (valfritt)"))
        self.master_combo = QComboBox()
        self.master_combo.setEditable(True)
        self.master_combo.lineEdit().setPlaceholderText("Sök masterprogram...")
        outer.addWidget(self.master_combo)

        import_master_btn = QPushButton("Importera masterkurser")
        import_master_btn.setStyleSheet("""
            QPushButton { background:#0e7490; color:white; border:none;
                padding:8px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#0c6680; }
        """)
        import_master_btn.clicked.connect(self._import_master_courses)
        outer.addWidget(import_master_btn)

        self.import_btn = QPushButton("Importera obligatoriska kurser")
        self.import_btn.setStyleSheet("""
            QPushButton { background:#6366f1; color:white; border:none;
                padding:10px; border-radius:6px; font-weight:bold; }
            QPushButton:hover { background:#4f46e5; }
        """)
        self.import_btn.clicked.connect(self._import_courses)
        outer.addWidget(self.import_btn)

        save_btn = QPushButton("Spara profil")
        save_btn.clicked.connect(self._save)
        outer.addWidget(save_btn)

        self.csn_spin.textChanged.connect(self._update_csn_status)

    def _update_grade(self):
        from stats import calculate_grade_average, numeric_to_grade
        avg = calculate_grade_average(self.planner.courses)
        if avg is None:
            self.grade_display.setText("-")
            self.grade_sub.setText("")
        else:
            self.grade_display.setText(numeric_to_grade(avg))
            self.grade_sub.setText(str(avg))

    def _update_csn_status(self):
        from stats import csn_stats
        try:
            weeks = int(self.csn_spin.text())
        except ValueError:
            return
        level = "kandidat" if self.kandidat_btn.isChecked() else "master"
        s = csn_stats(self.planner.courses, weeks, level=level)
        s = csn_stats(self.planner.courses, weeks)
        if not s["csn_ok"]:
            missing = round(s["required_now"] - s["completed_hp"], 1)
            self.csn_status_label.setText(
                f"⚠ Saknar {missing} HP (krav: {s['required_now']} HP)\n"
                f"{s['terms_left']} terminer kvar")
            self.csn_status_label.setStyleSheet("font-size:13px; color:#dc2626;")
        elif s["hp_needed"] > 0:
            self.csn_status_label.setText(
                f"Behöver {s['hp_needed']} HP denna termin\n"
                f"{s['terms_left']} terminer kvar")
            self.csn_status_label.setStyleSheet("font-size:13px; color:#4B1528;")
        else:
            self.csn_status_label.setText(
                f"✔ Krav uppfyllt\n{s['terms_left']} terminer kvar")
            self.csn_status_label.setStyleSheet("font-size:13px; color:#166534;")

    def _set_level(self, level):
        self.kandidat_btn.setChecked(level == "kandidat")
        self.master_btn.setChecked(level == "master")

    def load_profile(self, profile, program_index):
        self.name_edit.setText(profile.get("name", ""))
        self._set_level(profile.get("level", "kandidat"))

        # Fyll combo med program
        self.program_combo.clear()
        self._program_index = program_index
        for p in program_index:
            self.program_combo.addItem(
                f"{p['code']} — {p['name']}", p['code'])

        # Sätt nuvarande program
        code = profile.get("program_code", "")
        idx = self.program_combo.findData(code)
        if idx >= 0:
            self.program_combo.setCurrentIndex(idx)

        # Fyll master_combo med masterprogram
        self.master_combo.clear()
        self.master_combo.addItem("", "")
        for p in program_index:
            name = p.get("name", "")
            if any(kw in name.lower() for kw in ["master", "magister"]) or \
               p.get("code", "").startswith("T"):
                self.master_combo.addItem(f"{p['code']} — {name}", p['code'])

        master_code = self.planner.profile.get("master_code", "")
        midx = self.master_combo.findData(master_code)
        if midx >= 0:
            self.master_combo.setCurrentIndex(midx)
        self._update_csn_status()
        self._update_grade()

    def _get_selected_code(self):
        idx = self.program_combo.currentIndex()
        if idx >= 0:
            return self.program_combo.itemData(idx) or ""
        return self.program_combo.currentText().split("—")[0].strip().upper()

    def _save(self):
        from storage import save_profile, save_csn_weeks

        code = self._get_selected_code()
        idx  = self.program_combo.currentIndex()
        name_prog = ""
        if idx >= 0:
            name_prog = self.program_combo.itemText(idx).split("—")[-1].strip()

        profile = {
            "name":         self.name_edit.text().strip(),
            "program_code": code,
            "program_name": name_prog,
            "level":        "kandidat" if self.kandidat_btn.isChecked() else "master",
            "csn_weeks":    int(self.csn_spin.text() or "0"),
            "master_code":  self.master_combo.currentData() or "",
        }

        save_profile(profile, simulate=self.planner.simulate)
        old_level = self.planner.profile.get("level", "master")
        self.planner.profile = profile

        # Synka CSN-veckor
        self.planner.csn_weeks_used = int(self.csn_spin.text() or "0")
        save_csn_weeks(self.planner.csn_weeks_used, simulate=self.planner.simulate)

        # Bygg om griden om nivån ändrades
        if profile["level"] != old_level:
            self.planner.rebuild_grid(profile["level"])
        else:
            self.planner.update_hp_labels()

        self.slide_out()

    def _import_courses(self):
        from storage import load_program
        from course import Course
        from PyQt6.QtWidgets import QMessageBox

        code = self._get_selected_code()
        if not code:
            return

        prog = load_program(code)
        if not prog:
            QMessageBox.warning(self, "Saknas",
                f"Ingen programdatabas hittades för {code}.\n"
                "Kör build_program_db.py först.")
            return

        mandatory = [c for c in prog.get("courses", []) if c.get("mandatory")]
        if not mandatory:
            QMessageBox.information(self, "Inga kurser",
                "Inga obligatoriska kurser hittades för detta program.")
            return

        existing_codes = {c.code for c in self.planner.courses}
        new_courses    = [c for c in mandatory if c["code"] not in existing_codes]
        overlap        = [c for c in mandatory if c["code"] in existing_codes]

        msg = f"Hittade {len(mandatory)} obligatoriska kurser.\n"
        if new_courses:
            msg += f"• {len(new_courses)} nya kurser läggs till\n"
        if overlap:
            msg += f"• {len(overlap)} kurser finns redan — vad ska hända?"

        box = QMessageBox(self)
        box.setWindowTitle("Importera kurser")
        box.setText(msg)
        keep_btn      = box.addButton("Behåll befintliga", QMessageBox.ButtonRole.NoRole)
        overwrite_btn = box.addButton("Skriv över", QMessageBox.ButtonRole.YesRole)
        box.addButton("Avbryt", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == keep_btn or clicked == overwrite_btn:
            overwrite = clicked == overwrite_btn

            # Ta bort befintliga om overwrite
            if overwrite:
                self.planner.courses = [
                    c for c in self.planner.courses
                    if c.code not in {m["code"] for m in mandatory}
                ]

            kth_db = self.planner.kth_db

            for c in mandatory:
                if c["code"] in existing_codes and not overwrite:
                    continue
                # Hämta namn och HP från kth_db om tillgängligt
                db_entry = kth_db.get(c["code"], {})
                self.planner.courses.append(Course(
                    code      = c["code"],
                    name      = db_entry.get("name", c.get("name", "")),
                    hp_total  = db_entry.get("hp", c.get("hp", 7.5)),
                    hp_done   = 0,
                    year      = min(c.get("year", 0), 2),
                    period    = min(c.get("period", 0), 3),
                    source    = "IT",
                    status    = "planned",
                ))

            from storage import save_courses
            save_courses(self.planner.courses, simulate=self.planner.simulate)
            self.planner.refresh_ui()
            self.slide_out()

    def _import_master_courses(self):
        from storage import load_program
        from course import Course
        from PyQt6.QtWidgets import QMessageBox

        code = self.master_combo.currentData() or ""
        if not code:
            QMessageBox.warning(self, "Inget program", "Välj ett masterprogram först.")
            return

        prog = load_program(code)
        if not prog:
            QMessageBox.warning(self, "Saknas",
                f"Ingen programdatabas för {code}.\nKör build_program_db.py först.")
            return

        mandatory = [c for c in prog.get("courses", []) if c.get("mandatory")]
        if not mandatory:
            QMessageBox.information(self, "Inga kurser",
                "Inga obligatoriska kurser hittades.")
            return

        existing_codes = {c.code for c in self.planner.courses}
        new_c  = [c for c in mandatory if c["code"] not in existing_codes]
        overlap = [c for c in mandatory if c["code"] in existing_codes]

        msg = f"Hittade {len(mandatory)} obligatoriska masterkurser.\n"
        if new_c:
            msg += f"• {len(new_c)} nya kurser läggs till (år 4-5)\n"
        if overlap:
            msg += f"• {len(overlap)} kurser finns redan"

        box = QMessageBox(self)
        box.setWindowTitle("Importera masterkurser")
        box.setText(msg)
        keep_btn      = box.addButton("Behåll befintliga", QMessageBox.ButtonRole.NoRole)
        overwrite_btn = box.addButton("Skriv över", QMessageBox.ButtonRole.YesRole)
        box.addButton("Avbryt", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked in (keep_btn, overwrite_btn):
            overwrite = clicked == overwrite_btn
            if overwrite:
                self.planner.courses = [
                    c for c in self.planner.courses
                    if c.code not in {m["code"] for m in mandatory}
                ]
            kth_db = self.planner.kth_db
            for c in mandatory:
                if c["code"] in existing_codes and not overwrite:
                    continue
                db_entry = kth_db.get(c["code"], {})
                # Masterkurser placeras i år 4-5 (index 3-4)
                yr = min(max(c.get("year", 3), 3), 4)
                self.planner.courses.append(Course(
                    code     = c["code"],
                    name     = db_entry.get("name", c.get("name", "")),
                    hp_total = db_entry.get("hp", c.get("hp", 7.5)),
                    hp_done  = 0,
                    year     = yr,
                    period   = min(c.get("period", 0), 3),
                    source   = "IT",
                    status   = "planned",
                ))
            from storage import save_courses
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
        self._anim.setEndValue(QRect(parent.width(), 0, self.PANEL_WIDTH, h))
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    def resizeEvent(self, event):
        if self.isVisible():
            parent = self.parent()
            self.setGeometry(
                parent.width() - self.PANEL_WIDTH, 0,
                self.PANEL_WIDTH, parent.height())