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
from ui_components import (
    create_progress_bars, animate_bar_success,
    ConfettiWidget, SimulateBanner, SimulatePanel, EditPanel, ProfilePanel
)
from storage import (
    load_courses, save_courses, load_csn_weeks, save_csn_weeks,
    load_profile, save_profile, load_program_index
)
from stats import (
    calculate_grade_average,
    numeric_to_grade,
    total_completed_hp,
    total_it_hp,
    block_hp,
    missing_prerequisites,
    upcoming_events,
    csn_stats,
    IT_PROGRAM_HP,
    MASTER_PROGRAM_HP,
    IT_BLOCK_HP,
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
        self.profile = load_profile()
        self.program_index = load_program_index()

        self._build_ui()
        self.setStyleSheet(APP_STYLE)

        self.edit_panel    = EditPanel(self, self.kth_db)
        self.profile_panel = ProfilePanel(self)
        self.profile_panel.load_profile(self.profile, self.program_index)

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
        self.inner_layout.setContentsMargins(8, 6, 8, 6)
        self.inner_layout.setSpacing(6)
        self.main_layout.addWidget(inner)

        self.progress = create_progress_bars()

        # Osynliga labels för update-logik
        self.grade_avg_label   = QLabel("-")
        self.grade_avg_sub     = QLabel("")
        self.csn_terms_label   = QLabel("-")
        self.csn_hp_label      = QLabel("")
        self.csn_warning_label = QLabel("")
        self.csn_weeks_spin    = QSpinBox()
        self.csn_weeks_spin.setRange(0, 220)
        self.csn_weeks_spin.setValue(self.csn_weeks_used)
        self.csn_weeks_spin.valueChanged.connect(self._on_csn_weeks_changed)

        # KNAPPAR (vänster kolumn)
        self.profile_btn = QPushButton("👤  Profil")
        self.profile_btn.clicked.connect(self.open_profile)
        self.profile_btn.setStyleSheet("""
        QPushButton { background:#EFCDD6; color:#4B1528; border:none;
            padding:6px; border-radius:6px; font-weight:bold; }
        QPushButton:hover { background:#D4A0C8; }
        """)

        add = QPushButton("Add Course")
        add.clicked.connect(self.open_add_course)

        self.simulate_btn = QPushButton("▶ Simulate")
        self.simulate_btn.clicked.connect(self.toggle_simulate)
        self.simulate_btn.setStyleSheet("""
        QPushButton { background:#6366f1; border:none; padding:6px;
            border-radius:6px; color:white; font-weight:bold; }
        QPushButton:hover { background:#4f46e5; }
        """)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        left_col.addWidget(self.profile_btn)
        left_col.addWidget(add)
        left_col.addWidget(self.simulate_btn)

        # PROGRESSBARS (höger kolumn, fullbredd)
        p = self.progress["bars"]
        bars_col = QVBoxLayout()
        bars_col.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addWidget(p["it_program"])
        row1.addWidget(p["completed"])

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(p["matnat"])
        row2.addWidget(p["it_block"])

        bars_col.addLayout(row1)
        bars_col.addLayout(row2)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)
        top_layout.addLayout(left_col, 0)
        top_layout.addLayout(bars_col, 1)

        self.inner_layout.addLayout(top_layout)

        # KURSGRID (3 eller 5 år beroende på nivå)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)

        for i in range(5):
            self.grid.setColumnStretch(i, 1)

        level    = self.profile.get("level", "master")
        num_rows = 5 if level == "master" else 3
        self._build_grid_rows(num_rows)

        # EVENTS PANEL
        self.events_panel = EventsPanel()
        self.right_panel  = self.events_panel
        self.grid.addWidget(self.events_panel, 0, 4, num_rows, 1)

        self.inner_layout.addLayout(self.grid)

        self.display_courses()
        self.update_hp_labels()
        self.events_panel.refresh(self.courses)

    # ---------- SIMULATE ----------

    def _set_right_panel(self, widget):
        """Byt ut panelen i kolumn 4 i griden."""
        num_rows = 5 if self.profile.get("level", "master") == "master" else 3
        self.right_panel.hide()
        self.right_panel = widget
        self.grid.addWidget(widget, 0, 4, num_rows, 1)
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

    def _build_grid_rows(self, num_rows):
        """Bygg grid-celler för num_rows år."""
        for r in range(num_rows):
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
                self.grid.addWidget(box, r, c)
                self.cells[(r, c)] = {"layout": v, "hp": None}

    def rebuild_grid(self, level):
        """Rebuild griden när nivå ändras (3 <-> 5 år)."""
        num_rows = 5 if level == "master" else 3

        # Ta bort alla gamla widgets från grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.cells.clear()
        self._build_grid_rows(num_rows)

        self.events_panel = EventsPanel()
        self.right_panel  = self.events_panel
        self.grid.addWidget(self.events_panel, 0, 4, num_rows, 1)

        self.display_courses()
        self.update_hp_labels()
        self.events_panel.refresh(self.courses)

    def open_profile(self):
        self.profile_panel.load_profile(self.profile, self.program_index)
        self.profile_panel.slide_in()

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
        bar.setMaximum(int(total * 10))
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
        level = self.profile.get("level", "master")
        s = csn_stats(self.courses, self.csn_weeks_used, level=level)

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

        level      = self.profile.get("level", "master")
        program_hp = IT_PROGRAM_HP if level == "kandidat" else MASTER_PROGRAM_HP

        p = self.progress["bars"]
        self.update_bar(p["it_program"], it,       program_hp,      "IT Program Progress")
        self.update_bar(p["completed"],  completed, program_hp,      "Completed")
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