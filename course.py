from dataclasses import dataclass

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag
from theme import GRADE_COLORS, STATUS_COLORS

@dataclass
class Course:
    name: str
    code: str
    hp_total: float
    hp_done: float
    year: int
    period: int
    source: str = "IT"
    status: str = "planned"
    grade: str | None = None
    prerequisites: list[str] | None = None 

class CourseLabel(QLabel):

    def __init__(self, course: Course, planner):
        super().__init__()

        self.course = course
        self.planner = planner
        self.warning = False
        self.drag_start_position = QPoint()

        self.setTextFormat(Qt.TextFormat.RichText)
        self.setFixedHeight(30)
        self.setMouseTracking(True)

        self.update_default_text()

    def default_text(self):
        c = self.course

        base = f"{c.hp_done}/{c.hp_total} HP {c.code}"

        if self.warning:
            base = "⚠ " + base

        return base
    
    def hover_text(self):
        """Text shown on hover"""
        c = self.course

        if c.grade:
            color = GRADE_COLORS.get(c.grade, "black")
            grade = f'<span style="color:{color}; font-weight:bold">{c.grade}</span>'
            grade_text = f" {grade}"
        else:
            grade_text = ""

        return f"{c.name}{grade_text}"

    def update_default_text(self):
        self.setText(self.default_text())

    def enterEvent(self, event):
        self.setText(self.hover_text())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_default_text()
        super().leaveEvent(event)

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if (
            event.pos() - self.drag_start_position
        ).manhattanLength() < 8:
            return

        drag = QDrag(self)

        mime = QMimeData()
        mime.setText(self.course.code)

        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)
    
    def mouseDoubleClickEvent(self, event):

        from course_details import CourseDetailsDialog

        dialog = CourseDetailsDialog(self.planner, self.course)
        dialog.exec()

        super().mouseDoubleClickEvent(event)