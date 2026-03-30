import copy

from PyQt6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QShortcut, QKeySequence

from course import CourseLabel
from course_details import CourseDetailsDialog
from dialogs import add_course_dialog, load_kth_db
from ui_components import create_progress_bars, animate_bar_success, ConfettiWidget, SimulateBanner, SimulatePanel, EditPanel
from storage import load_courses, save_courses, load_csn_weeks, save_csn_weeks
from stats import (
    calculate_grade_average,
    numeric_to_grade,
    total_completed_hp,
    total_it_hp,
    block_hp,
    missing_prerequisites,
    upcoming_events,
    csn_stats,
    IT_BLOCK_HP,
    IT_PROGRAM_HP,
    MATNAT_BLOCK_HP
)
from theme import (
    course_label_style,
    period_box_style,
    course_borders,
    events_panel_style,
    APP_STYLE,
    SIMULATE_STYLE,
    PERIOD_COLORS,
    STATUS_COLORS
)


# ---------- EVENTS PANEL ----------

class EventsPanel(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(events_panel_style())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        title = QLabel("Upcoming Deadlines")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold;font-size:16px")
        outer.addWidget(title)

        # Scroll area för events
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")

        self.events_box = QVBoxLayout(content)
        self.events_box.setSpacing(2)
        self.events_box.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(content)

        # Tvinga content att hålla sig inom scroll-areans bredd
        scroll.horizontalScrollBar().setEnabled(False)
        def _resize_content(event):
            content.setMaximumWidth(scroll.viewport().width())
        scroll.resizeEvent = _resize_content

        outer.addWidget(scroll)

    def refresh(self, courses):
        while self.events_box.count():
            w = self.events_box.takeAt(0).widget()
            if w:
                w.deleteLater()

        events = upcoming_events(courses)
        current_date = None
        container_layout = None

        for e in events:
            date_str = e["date"].strftime("%d %b")

            if date_str != current_date:
                header = QLabel(date_str)
                header.setStyleSheet("font-weight:bold;font-size:15px;margin-top:6px;")
                self.events_box.addWidget(header)

                container = QFrame()
                container.setStyleSheet("QFrame { background:white; border-radius:8px; padding:4px; }")
                container_layout = QVBoxLayout(container)
                container_layout.setSpacing(2)
                self.events_box.addWidget(container)

                current_date = date_str

            label = QLabel(f"{e['title']} — {e['course']}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size:13px;padding-left:4px;")
            container_layout.addWidget(label)

        self.events_box.addStretch()


# ---------- STUDY PLANNER ----------

class StudyPlanner(QWidget):

    def __init__(self):
        super().__init__()

        QShortcut(QKeySequence("Escape"), self, activated=self.fade_and_close)

        self.setMinimumSize(900, 700)
        self.showMaximized()

        # Simulate state
        self.simulate = False
        self._real_courses = None  # snapshot av riktiga kurser

        self.courses = load_courses()
        self.cells = {}
        self.completed_bars = set()
        self.csn_weeks_used = load_csn_weeks()
        self.kth_db = load_kth_db()

        self._build_ui()
        self.setStyleSheet(APP_STYLE)

        # Edit panel (overlay, skapas efter UI är byggt)
        self.edit_panel = EditPanel(self, self.kth_db)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # SIMULATE BANNER (dold från start)
        self.banner = SimulateBanner(on_exit=self.exit_simulate)
        self.banner.hide()
        self.main_layout.addWidget(self.banner)

        # INNER CONTENT
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        self.main_layout.addWidget(inner)

        self.progress = create_progress_bars()

        CARD_STYLE = """
            QFrame {
                background: #EFCDD6;
                border-radius: 10px;
            }
        """

        # GRADE-KORT
        self.grade_avg_label = QLabel("-")
        self.grade_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_avg_label.setStyleSheet("font-size:28px; font-weight:bold; padding:0;")

        self.grade_avg_sub = QLabel("")
        self.grade_avg_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_avg_sub.setStyleSheet("color:gray; font-size:13px; padding:0;")

        grade_title = QLabel("Grade Average")
        grade_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grade_title.setStyleSheet("font-size:12px; color:gray; padding:0;")

        grade_card = QFrame()
        grade_card.setStyleSheet(CARD_STYLE)
        grade_inner = QVBoxLayout(grade_card)
        grade_inner.setSpacing(2)
        grade_inner.setContentsMargins(10, 8, 10, 8)
        grade_inner.addWidget(grade_title)
        grade_inner.addWidget(self.grade_avg_label)
        grade_inner.addWidget(self.grade_avg_sub)

        # CSN-KORT
        self.csn_terms_label = QLabel("-")
        self.csn_terms_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csn_terms_label.setStyleSheet("font-size:28px; font-weight:bold; padding:0;")

        self.csn_hp_label = QLabel("- HP/termin")
        self.csn_hp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csn_hp_label.setStyleSheet("font-size:13px; color:gray; padding:0;")

        self.csn_warning_label = QLabel("")
        self.csn_warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csn_warning_label.setWordWrap(True)
        self.csn_warning_label.setStyleSheet("font-size:11px; color:#dc2626; font-weight:bold; padding:0;")

        csn_title = QLabel("CSN kvar")
        csn_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        csn_title.setStyleSheet("font-size:12px; color:gray; padding:0;")

        # Spinbox för förbrukade veckor
        weeks_row = QHBoxLayout()
        weeks_row.setContentsMargins(0, 0, 0, 0)

        weeks_lbl = QLabel("Veckor:")
        weeks_lbl.setStyleSheet("font-size:11px; color:gray; padding:0; background:transparent;")

        self.csn_weeks_spin = QSpinBox()
        self.csn_weeks_spin.setRange(0, 220)
        self.csn_weeks_spin.setValue(self.csn_weeks_used)
        self.csn_weeks_spin.setSuffix(" v")
        self.csn_weeks_spin.setFixedWidth(72)
        self.csn_weeks_spin.setStyleSheet("font-size:11px;")
        self.csn_weeks_spin.valueChanged.connect(self._on_csn_weeks_changed)

        weeks_row.addWidget(weeks_lbl)
        weeks_row.addWidget(self.csn_weeks_spin)
        weeks_row.addStretch()

        csn_card = QFrame()
        csn_card.setStyleSheet(CARD_STYLE)
        csn_inner = QVBoxLayout(csn_card)
        csn_inner.setSpacing(2)
        csn_inner.setContentsMargins(10, 8, 10, 8)
        csn_inner.addWidget(csn_title)
        csn_inner.addLayout(weeks_row)
        csn_inner.addWidget(self.csn_terms_label)
        csn_inner.addWidget(self.csn_hp_label)
        csn_inner.addWidget(self.csn_warning_label)

        # KNAPPAR under grade-kortet
        add = QPushButton("Add Course")
        add.clicked.connect(self.open_add_course)

        self.simulate_btn = QPushButton("▶ Simulate")
        self.simulate_btn.clicked.connect(self.toggle_simulate)
        self.simulate_btn.setStyleSheet("""
        QPushButton {
            background: #6366f1;
            border: none;
            padding: 6px;
            border-radius: 6px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover { background: #4f46e5; }
        """)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        left_col.addWidget(grade_card)
        left_col.addWidget(add)
        left_col.addWidget(self.simulate_btn)

        # MITTEN: CSN-kort (sträcker sig i höjd)
        csn_col = QVBoxLayout()
        csn_col.addWidget(csn_card)

        # HÖGER: 2x2 bars grid
        p = self.progress["bars"]
        bars_grid = QGridLayout()
        bars_grid.setSpacing(6)
        bars_grid.addWidget(p["it_program"], 0, 0)
        bars_grid.addWidget(p["completed"],  0, 1)
        bars_grid.addWidget(p["matnat"],     1, 0)
        bars_grid.addWidget(p["it_block"],   1, 1)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.addLayout(left_col,   0)
        top_layout.addLayout(csn_col,    0)
        top_layout.addLayout(bars_grid,  1)

        self.inner_layout.addLayout(top_layout)

        # GRID
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        for i in range(5):
            grid.setColumnStretch(i, 1)

        for r in range(3):
            for c in range(4):
                g1, g2 = PERIOD_COLORS[c]

                box = QFrame()
                box.setAcceptDrops(True)
                box.dragEnterEvent = self.drag_enter
                box.dropEvent = lambda event, r=r, c=c: self.drop_course(event, r, c)
                box.setStyleSheet(period_box_style(g1, g2))

                v = QVBoxLayout()

                title = QLabel(f"Year {r+1}, P{c+1}")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                title.setStyleSheet("font-weight:bold")

                v.addWidget(title)
                box.setLayout(v)

                grid.addWidget(box, r, c)
                self.cells[(r, c)] = {"layout": v, "hp": None}

        # EVENTS PANEL
        self.events_panel = EventsPanel()
        self.right_panel = self.events_panel  # håller koll på vad som sitter i kolumn 4
        grid.addWidget(self.events_panel, 0, 4, 3, 1)

        self.grid = grid  # spara referens för att byta panel senare
        self.inner_layout.addLayout(grid)

        self.display_courses()
        self.update_hp_labels()
        self.events_panel.refresh(self.courses)

    # ---------- SIMULATE ----------

    def _set_right_panel(self, widget):
        """Byt ut panelen i kolumn 4 i griden."""
        self.right_panel.hide()
        self.right_panel = widget
        self.grid.addWidget(widget, 0, 4, 3, 1)
        widget.show()

    def toggle_simulate(self):
        if self.simulate:
            self.exit_simulate()
        else:
            self.enter_simulate()

    def enter_simulate(self):
        self.simulate = True
        self._real_courses = load_courses()
        self.courses = copy.deepcopy(self._real_courses)
        self.completed_bars = set()

        self.banner.show()
        self.setStyleSheet(SIMULATE_STYLE)
        self.simulate_btn.hide()

        # Byt kalender mot simulate-panel
        self.simulate_panel = SimulatePanel(self)
        self.simulate_panel.weeks_spin.setValue(self.csn_weeks_used)
        self._set_right_panel(self.simulate_panel)

        self.refresh_ui()

    def exit_simulate(self):
        self.simulate = False
        self.courses = self._real_courses
        self._real_courses = None
        self.completed_bars = set()

        self.banner.hide()
        self.setStyleSheet(APP_STYLE)
        self.simulate_btn.show()

        # Återställ kalender
        self._set_right_panel(self.events_panel)

        self.refresh_ui()

    def reset_simulate(self):
        """Återställ simulate-kurser till snapshot utan att lämna simulate-läge."""
        self.courses = copy.deepcopy(self._real_courses)
        self.completed_bars = set()
        self.refresh_ui()

    # ---------- DRAG & DROP ----------

    def drag_enter(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def drop_course(self, event, r, c):
        code = event.mimeData().text()
        for course in self.courses:
            if course.code == code:
                course.year = r
                course.period = c
                break
        save_courses(self.courses, simulate=self.simulate)
        self.refresh_ui()
        event.acceptProposedAction()

    # ---------- ACTIONS ----------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def fade_and_close(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def _on_csn_weeks_changed(self, value):
        self.csn_weeks_used = value
        save_csn_weeks(value, simulate=self.simulate)
        self.update_csn()

    def open_add_course(self):
        add_course_dialog(self)

    def open_course_details(self, course):
        self.edit_panel.load_course(course)
        self.edit_panel.slide_in()

    # ---------- COURSE DISPLAY ----------

    def display_courses(self):
        for course in self.courses:
            label = CourseLabel(course, on_double_click=self.open_course_details)

            if missing_prerequisites(course, self.courses):
                label.warning = True
                label.update_default_text()

            color = STATUS_COLORS.get(course.status, "white")
            left, right = course_borders(course)
            label.setStyleSheet(course_label_style(color, left, right))

            self.cells[(course.year, course.period)]["layout"].addWidget(label)

    # ---------- STATS ----------

    def update_bar(self, bar, value, total, label):
        display_value = min(value, total)
        bar.setValue(int(display_value * 10))

        if value >= total:
            bar.setFormat(f"{label}: ✔ COMPLETE")
            if label not in self.completed_bars:
                self.completed_bars.add(label)
                animate_bar_success(bar)
                if not self.simulate:
                    ConfettiWidget(self)
        else:
            bar.setFormat(f"{label}: {display_value} / {total} HP")

    def update_csn(self):
        s = csn_stats(self.courses, self.csn_weeks_used)

        self.csn_terms_label.setText(f"{s['terms_left']} term")

        if not s["csn_ok"]:
            missing = round(s["required_now"] - s["completed_hp"], 1)
            self.csn_hp_label.setText(f"Saknar {missing} HP (krav: {s['required_now']} HP)")
            self.csn_warning_label.setText("⚠ CSN-kravet ej uppfyllt!")
            self.csn_terms_label.setStyleSheet("font-size:28px; font-weight:bold; color:#dc2626; padding:0;")
        elif s["at_risk"]:
            self.csn_hp_label.setText(f"Behöver {s['hp_needed']} HP denna termin")
            self.csn_warning_label.setText("⚠ Svår takt denna termin")
            self.csn_terms_label.setStyleSheet("font-size:28px; font-weight:bold; color:#f59e0b; padding:0;")
        elif s["hp_needed"] > 0:
            self.csn_hp_label.setText(f"Behöver {s['hp_needed']} HP denna termin")
            self.csn_warning_label.setText("")
            self.csn_terms_label.setStyleSheet("font-size:28px; font-weight:bold; padding:0;")
        else:
            self.csn_hp_label.setText("Krav uppfyllt ✔")
            self.csn_warning_label.setText("")
            self.csn_terms_label.setStyleSheet("font-size:28px; font-weight:bold; padding:0;")

    def update_hp_labels(self):
        for (r, c), cell in self.cells.items():
            total = sum(
                x.hp_done for x in self.courses
                if x.year == r and x.period == c
            )
            # hp-label är borttagen från gridceller

        completed = total_completed_hp(self.courses)
        it        = total_it_hp(self.courses)
        matnat    = block_hp(self.courses, "matnat")
        it_block  = block_hp(self.courses, "it")

        p = self.progress["bars"]
        self.update_bar(p["it_program"], it,       IT_PROGRAM_HP,   "IT Program Progress")
        self.update_bar(p["completed"],  completed, IT_PROGRAM_HP,   "Completed")
        self.update_bar(p["matnat"],     matnat,    MATNAT_BLOCK_HP, "MatNat block")
        self.update_bar(p["it_block"],   it_block,  IT_BLOCK_HP,     "IT block")

        avg = calculate_grade_average(self.courses)
        grade = numeric_to_grade(avg)

        if avg is None:
            self.grade_avg_label.setText("-")
            self.grade_avg_sub.setText("")
        else:
            self.grade_avg_label.setText(grade)
            self.grade_avg_sub.setText(f"{avg}")

        self.update_csn()

    # ---------- REFRESH ----------

    def refresh_ui(self):
        for cell in self.cells.values():
            layout = cell["layout"]
            while layout.count() > 1:
                w = layout.takeAt(1).widget()
                if w:
                    w.deleteLater()

        self.display_courses()
        self.update_hp_labels()

        if not self.simulate:
            self.events_panel.refresh(self.courses)