import sys
import os
import json

from PyQt6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton,
    QVBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QShortcut, QKeySequence

from course import Course, CourseLabel

from stats import (
    calculate_grade_average,
    numeric_to_grade,
    total_completed_hp,
    total_it_hp,
    block_hp,
    course_block,
    HP_PER_YEAR,
    BLOCK_COLORS,
    SOURCE_COLORS,
    PERIOD_COLORS,
    STATUS_COLORS
)

from dialogs import edit_course_dialog, add_course_dialog
from ui_components import create_progress_bars


# ---------- PATH HANDLING ----------

def resource_path(relative_path):
    """Fungerar både i utveckling och PyInstaller exe"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ---------- MAIN UI ----------

class StudyPlanner(QWidget):

    # ---------- DATA ----------

    def load_courses(self):
        try:
            with open(resource_path("data/courses.json"), encoding="utf-8") as f:
                courses = json.load(f)

            for c in courses:
                c.setdefault("grade", None)

            return [Course(**c) for c in courses]

        except Exception as e:
            print("Failed to load courses:", e)
            return []

    def save_courses(self):
        try:
            with open(resource_path("data/courses.json"), "w", encoding="utf-8") as f:
                json.dump([c.__dict__ for c in self.courses], f, indent=4)

        except Exception as e:
            print("Failed to save courses:", e)

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

        self.save_courses()
        self.refresh_ui()
        event.acceptProposedAction()

    # ---------- KEY EVENTS ----------

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

    # ---------- INIT ----------

    def __init__(self):
        super().__init__()

        QShortcut(QKeySequence("Escape"), self, activated=self.fade_and_close)

        self.showMaximized()
        self.setMinimumSize(900, 700)

        self.courses = self.load_courses()

        self.cells = {}
        self.year_labels = {}

        layout = QVBoxLayout(self)

        # ---------- ADD COURSE ----------

        add = QPushButton("Add Course")
        add.clicked.connect(lambda: add_course_dialog(self))
        layout.addWidget(add)

        # ---------- PROGRESS BARS ----------

        self.progress = create_progress_bars()
        layout.addLayout(self.progress["layout"])

        # ---------- GRADE AVERAGE ----------

        self.grade_avg_label = QLabel("Grade Average: -")
        self.grade_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_avg_label.setStyleSheet("font-weight:bold;padding:4px;")
        layout.addWidget(self.grade_avg_label)

        # ---------- LEGEND ----------

        legend = QLabel(
            "Legend: 🟥 MatNat block   🟦 IT block   🟧 External course"
        )

        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legend.setStyleSheet("font-weight:bold;padding:4px;")

        layout.addWidget(legend)

        # ---------- GRID ----------

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

                box.setStyleSheet(f"""
                QFrame {{
                    background:qlineargradient(
                        x1:0,y1:0,x2:1,y2:1,
                        stop:0 {g1}, stop:1 {g2});
                    border-radius:8px;
                }}""")

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

    # ---------- COURSE DISPLAY ----------

    def display_courses(self):

        for course in self.courses:

            label = CourseLabel(course)

            color = STATUS_COLORS.get(course.status, "white")

            left = (
                f"6px solid {SOURCE_COLORS['external']}"
                if course.source == "external"
                else "none"
            )

            block = course_block(course)

            right = (
                f"6px solid {BLOCK_COLORS[block]}"
                if block
                else "none"
            )

            label.setStyleSheet(f"""
                background:{color};
                border-left:{left};
                border-right:{right};
                padding:6px;
            """)

            label.mouseDoubleClickEvent = lambda e, c=course: edit_course_dialog(self, c)

            self.cells[(course.year, course.period)]["layout"].addWidget(label)

    # ---------- UPDATE STATS ----------

    def update_hp_labels(self):

        # period HP
        for (r, c), cell in self.cells.items():

            total = sum(
                x.hp_done for x in self.courses
                if x.year == r and x.period == c
            )

            cell["hp"].setText(f"Total: {total} HP")

        # year HP
        for y, label in self.year_labels.items():

            total = sum(x.hp_done for x in self.courses if x.year == y)

            progress = min(total / HP_PER_YEAR, 1)

            border = "4px solid #2ecc71" if total >= HP_PER_YEAR else "none"

            label.setText(f"{total} / {HP_PER_YEAR} HP")

            label.setStyleSheet(f"""
            QLabel {{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7CFC9A,
                    stop:{progress} #7CFC9A,
                    stop:{progress} #eeeeee,
                    stop:1 #eeeeee);
                border-radius:10px;
                border:{border};
                font-weight:bold;
                font-size:16px;
                padding:10px;
            }}""")

        # global stats
        completed = total_completed_hp(self.courses)
        it = total_it_hp(self.courses)

        matnat = block_hp(self.courses, "matnat")
        it_block = block_hp(self.courses, "it")

        p = self.progress["bars"]

        p["it_program"].setValue(int(it))
        p["it_program"].setFormat(f"IT Program Progress: {it} / 180 HP")

        p["completed"].setValue(int(completed))
        p["completed"].setFormat(f"Completed: {completed} / 180 HP")

        p["matnat"].setValue(int(matnat))
        p["matnat"].setFormat(f"MatNat block: {matnat} / 15 HP")

        p["it_block"].setValue(int(it_block))
        p["it_block"].setFormat(f"IT block: {it_block} / 21 HP")

        # grade average
        avg = calculate_grade_average(self.courses)
        grade = numeric_to_grade(avg)

        if avg is None:
            self.grade_avg_label.setText("Grade Average: -")
        else:
            self.grade_avg_label.setText(f"Grade Average: {grade} ({avg})")
    # ---------- REFRESH ----------

    def refresh_ui(self):

        for cell in self.cells.values():

            layout = cell["layout"]

            while layout.count() > 2:
                w = layout.takeAt(2).widget()
                if w:
                    w.deleteLater()

        self.display_courses()
        self.update_hp_labels()