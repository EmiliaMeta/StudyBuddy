from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout,
    QPushButton, QProgressBar, QFrame
)

from stats import missing_prerequisites
from dialogs import edit_course_dialog
from theme import STATUS_COLORS, TITLE_STYLE

class CourseDetailsDialog(QDialog):

    def __init__(self, planner, course):
        super().__init__(planner)

        self.planner = planner
        self.course = course

        self.setWindowTitle(course.code)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        title = QLabel(course.name)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        code = QLabel(course.code)
        code.setStyleSheet("color:gray")
        layout.addWidget(code)

        status_color = STATUS_COLORS.get(course.status, "white")

        status = QLabel(f"Status: {course.status}")
        status.setStyleSheet(f"""
        background:{status_color};
        padding:4px;
        border-radius:6px;
        font-weight:bold;
        """)

        layout.addWidget(status)

        hp = QLabel(f"HP: {course.hp_done} / {course.hp_total}")
        layout.addWidget(hp)

        progress = QProgressBar()
        progress.setMaximum(int(course.hp_total))
        progress.setValue(int(course.hp_done))

        layout.addWidget(progress)
        layout.addWidget(QLabel("<b>🔑 Prerequisites<b>"))

        completed = {
            c.code for c in planner.courses
            if c.status == "completed"
        }

        missing = missing_prerequisites(course, planner.courses)

        if not course.prerequisites:
            layout.addWidget(QLabel(""))

        else:
            for group in course.prerequisites:
                satisfied = any(code in completed for code in group)

                text = " OR ".join(group)

                label = QLabel(text)

                if satisfied:
                    label.setStyleSheet("color:green")
                    label.setText("✔ " + text)

                else:
                    label.setStyleSheet("color:red")
                    label.setText("✖ " + text)

                layout.addWidget(label)

        if missing:
            warning = QLabel("⚠ Missing prerequisites")
            warning.setStyleSheet("""
            color:red;
            font-weight:bold;
            """)

            layout.addWidget(warning)
        edit = QPushButton("Edit Course")
        
        if course.notes:
            notes = QLabel(course.notes)
            notes.setWordWrap(True)

            layout.addWidget(notes)
        
        if course.important_dates:
            layout.addWidget(QLabel("<b>Important Dates<b>"))

            for d in course.important_dates:
                layout.addWidget(QLabel(f"• {d}"))

        def open_edit():
            edit_course_dialog(planner, course)
            self.close()

        edit.clicked.connect(open_edit)

        layout.addWidget(edit)