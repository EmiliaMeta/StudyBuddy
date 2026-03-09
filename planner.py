import sys
from PyQt6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton,
    QVBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QShortcut, QKeySequence

from course import CourseLabel
from dialogs import add_course_dialog
from ui_components import create_progress_bars
from storage import load_courses, save_courses
from stats import (
    calculate_grade_average,
    numeric_to_grade,
    total_completed_hp,
    total_it_hp,
    block_hp,
    missing_prerequisites,
    upcoming_events,
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
    PERIOD_COLORS,
    STATUS_COLORS
)


class StudyPlanner(QWidget):

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

        save_courses(self.courses)
        self.refresh_ui()
        event.acceptProposedAction()

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

    def open_add_course(self):
        add_course_dialog(self)

    def __init__(self):
        super().__init__()

        QShortcut(QKeySequence("Escape"), self, activated=self.fade_and_close)

        self.setStyleSheet(APP_STYLE)
        self.showMaximized()
        self.setMinimumSize(900, 700)

        self.courses = load_courses()
        self.cells = {}

        layout = QVBoxLayout(self)

        #  ADD COURSE 
        add = QPushButton("Add Course")
        add.clicked.connect(self.open_add_course)
        layout.addWidget(add)

        #  PROGRESS BARS 
        self.progress = create_progress_bars()
        layout.addLayout(self.progress["layout"])

        # GRADE AVERAGE 
        self.grade_avg_label = QLabel("Grade Average: -")
        self.grade_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_avg_label.setStyleSheet("font-weight:bold;padding:4px;")
        layout.addWidget(self.grade_avg_label)

        # GRID 
        grid = QGridLayout()
            # EVENTS PANEL 
        self.events_frame = QFrame()
        self.events_frame.setStyleSheet(events_panel_style())

        events_layout = QVBoxLayout(self.events_frame)

        self.events_title = QLabel("Upcoming Deadlines")
        self.events_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.events_title.setStyleSheet("font-weight:bold;font-size:16px")

        events_layout.addWidget(self.events_title)

        self.events_box = QVBoxLayout()
        events_layout.addLayout(self.events_box)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        layout.addLayout(grid)
        # period columns
        for i in range(5):
            grid.setColumnStretch(i, 1)
        # calendar column
        grid.setColumnStretch(1, 1)
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

                hp = QLabel("Total: 0 HP")
                hp.setAlignment(Qt.AlignmentFlag.AlignCenter)

                v.addWidget(title)
                v.addWidget(hp)

                box.setLayout(v)

                grid.addWidget(box, r, c)

                self.cells[(r, c)] = {"layout": v, "hp": hp}
        grid.addWidget(self.events_frame, 0, 4, 3, 1)
        self.display_courses()
        self.update_hp_labels()
        self.update_events()

    # COURSE DISPLAY 
    def display_courses(self):

        for course in self.courses:

            label = CourseLabel(course, self)

            if missing_prerequisites(course, self.courses):
                label.warning = True
                label.update_default_text()

            color = STATUS_COLORS.get(course.status, "white")

            left, right = course_borders(course)

            label.setStyleSheet(course_label_style(color, left, right))

            self.cells[(course.year, course.period)]["layout"].addWidget(label)
    
    #  UPDATE STATS 
    def update_bar(self, bar, value, total, label):

        bar.setValue(int(value))
        bar.setFormat(f"{label}: {value} / {total} HP")

    def update_events(self):
        while self.events_box.count():
            w = self.events_box.takeAt(0).widget()
            if w:
                w.deleteLater()

        events = upcoming_events(self.courses)

        for e in events[:8]:

            date = e["date"].strftime("%d %b")
            title = e["title"]
            course = e["course"]

            card = QFrame()
            card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.45);
                border-radius:8px;
                padding:6px;
            }
            """)

            layout = QVBoxLayout(card)

            date_label = QLabel(date)
            date_label.setStyleSheet("font-weight:bold;font-size:14px")

            title_label = QLabel(title)
            title_label.setWordWrap(True)

            course_label = QLabel(course)
            course_label.setStyleSheet("color:#444")

            layout.addWidget(date_label)
            layout.addWidget(title_label)
            layout.addWidget(course_label)

            self.events_box.addWidget(card)

        self.events_box.addStretch()

    def update_hp_labels(self):

        # period totals
        for (r, c), cell in self.cells.items():

            total = sum(
                x.hp_done for x in self.courses
                if x.year == r and x.period == c
            )

            cell["hp"].setText(f"Total: {total} HP")

        # global stats
        completed = total_completed_hp(self.courses)
        it = total_it_hp(self.courses)

        matnat = block_hp(self.courses, "matnat")
        it_block = block_hp(self.courses, "it")

        p = self.progress["bars"]

        self.update_bar(p["it_program"], it, IT_PROGRAM_HP, "IT Program Progress")
        self.update_bar(p["completed"], completed, IT_PROGRAM_HP, "Completed")
        self.update_bar(p["matnat"], matnat, MATNAT_BLOCK_HP, "MatNat block")
        self.update_bar(p["it_block"], it_block, IT_BLOCK_HP, "IT block")

        avg = calculate_grade_average(self.courses)
        grade = numeric_to_grade(avg)

        if avg is None:
            self.grade_avg_label.setText("Grade Average: -")
        else:
            self.grade_avg_label.setText(f"Grade Average: {grade} ({avg})")

    #  REFRESH 
    def refresh_ui(self):

        for cell in self.cells.values():

            layout = cell["layout"]

            while layout.count() > 2:
                w = layout.takeAt(2).widget()
                if w:
                    w.deleteLater()

        self.display_courses()
        self.update_hp_labels()
        self.update_events()