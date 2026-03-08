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
    course_block,
    missing_prerequisites,
    HP_PER_YEAR,
    IT_BLOCK_HP,
    IT_PROGRAM_HP,
    MATNAT_BLOCK_HP
)
from theme import (
    course_label_style,
    year_progress_style,
    period_box_style,
    course_borders,
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
        self.year_labels = {}

        layout = QVBoxLayout(self)

        add = QPushButton("Add Course")
        add.clicked.connect(self.open_add_course)        
        layout.addWidget(add)

        self.progress = create_progress_bars()
        layout.addLayout(self.progress["layout"])

        self.grade_avg_label = QLabel("Grade Average: -")
        self.grade_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_avg_label.setStyleSheet("font-weight:bold;padding:4px;")
        layout.addWidget(self.grade_avg_label)

        legend = QLabel(
            "Legend: 🟥 MatNat block   🟦 IT block   🟧 External course"
        )

        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legend.setStyleSheet("font-weight:bold;padding:4px;")

        layout.addWidget(legend)

        grid = QGridLayout()

        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        layout.addLayout(grid)

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

            year = QLabel("0 HP")
            year.setMinimumWidth(120)
            year.setAlignment(Qt.AlignmentFlag.AlignCenter)

            grid.addWidget(year, r, 4)

            self.year_labels[r] = year

        self.display_courses()
        self.update_hp_labels()

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
    
    def update_bar(self, bar, value, total, label):
        bar.setValue(int(value))
        bar.setFormat(f"{label}: {value} / {total} HP")
        

    def update_hp_labels(self):
        for (r, c), cell in self.cells.items():

            total = sum(
                x.hp_done for x in self.courses
                if x.year == r and x.period == c
            )

            cell["hp"].setText(f"Total: {total} HP")

        for y, label in self.year_labels.items():

            total = sum(x.hp_done for x in self.courses if x.year == y)

            progress = min(total / HP_PER_YEAR, 1)

            border = "4px solid #2ecc71" if total >= HP_PER_YEAR else "none"

            label.setText(f"{total} / {HP_PER_YEAR} HP")

            label.setStyleSheet(year_progress_style(progress, border))

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

    def refresh_ui(self):
        for cell in self.cells.values():
            layout = cell["layout"]

            while layout.count() > 2:
                w = layout.takeAt(2).widget()
                if w:
                    w.deleteLater()

        self.display_courses()
        self.update_hp_labels()