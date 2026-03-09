from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox,
    QDoubleSpinBox, QLineEdit, QPushButton,
    QTextEdit
)

from course import Course, STATUS_COLORS
from storage import save_courses


# ---------- HELPERS ----------

def prerequisites_to_text(prereqs):
    """Convert internal prerequisite structure to text."""
    if not prereqs:
        return ""

    groups = []
    for group in prereqs:
        groups.append(", ".join(group))

    return " ; ".join(groups)


def text_to_prerequisites(text):
    """Parse text into prerequisite structure."""
    text = text.strip()
    if not text:
        return None

    groups = []
    for group in text.split(";"):

        codes = [
            x.strip().upper()
            for x in group.split(",")
            if x.strip()
        ]

        if codes:
            groups.append(codes)

    return groups if groups else None

def edit_course_dialog(planner, course):

    d = QDialog(planner)
    form = QFormLayout(d)

    year = QComboBox()
    year.addItems(["1","2","3"])
    year.setCurrentIndex(course.year)

    period = QComboBox()
    period.addItems(["1","2","3","4"])
    period.setCurrentIndex(course.period)

    status = QComboBox()
    status.addItems(list(STATUS_COLORS))
    status.setCurrentText(course.status)

    source = QComboBox()
    source.addItems(["IT","external"])
    source.setCurrentText(course.source)

    hp = QDoubleSpinBox()
    hp.setRange(0,30)
    hp.setValue(course.hp_total)

    done = QDoubleSpinBox()
    done.setRange(0,30)
    done.setValue(course.hp_done)

    code = QLineEdit(course.code)
    name = QLineEdit(course.name)

    notes = QTextEdit(course.notes or "")

    if course.important_dates:
        text = ", ".join(
            f"{d['title']} - {d['date']}"
            for d in course.important_dates
        )
    else:
        text = ""

    dates = QLineEdit(text)
    dates.setPlaceholderText("YYYY-MM-DD, YYYY-MM-DD")

    prerequisites = QLineEdit(prerequisites_to_text(course.prerequisites))
    prerequisites.setPlaceholderText(
        "Use , for OR and ; for AND (ex: ID1018, MF1000 ; IS1200)"
    )

    grade = QComboBox()
    grade.addItems(["", "A", "B", "C", "D", "E", "F"])
    grade.setCurrentText(course.grade or "")

    for t,w in [
        ("Year",year),("Period",period),("Source",source),
        ("Status",status),("HP",hp),("Completed",done),
        ("Code",code),("Name",name),
        ("Prerequisites", prerequisites),
        ("Notes", notes),("Important dates", dates),
        ("Grade", grade)
    ]:
        form.addRow(t,w)

    save = QPushButton("Save")
    delete = QPushButton("Delete")

    form.addRow(save)
    form.addRow(delete)

    def save_course():

        course.year = year.currentIndex()
        course.period = period.currentIndex()
        course.status = status.currentText()
        course.source = source.currentText()
        course.hp_total = hp.value()
        course.hp_done = done.value()
        course.code = code.text().upper()
        course.name = name.text()
        course.grade = grade.currentText() or None
        course.notes = notes.toPlainText().strip() or None

        text = dates.text().strip()

        dates_list = []

        if text:
            for item in text.split(","):
                item = item.strip()

                if "-" in item:
                    title, date = item.split("-", 1)

                    dates_list.append({
                        "title": title.strip(),
                        "date": date.strip()
                    })

        course.important_dates = dates_list

        course.prerequisites = text_to_prerequisites(
            prerequisites.text()
        )

        save_courses(planner.courses)
        planner.refresh_ui()

        d.accept()

    def delete_course():

        planner.courses.remove(course)
        save_courses(planner.courses)
        planner.refresh_ui()

        d.accept()

    save.clicked.connect(save_course)
    delete.clicked.connect(delete_course)

    d.exec()


# ---------- ADD COURSE ----------

def add_course_dialog(planner):

    d = QDialog(planner)
    form = QFormLayout(d)

    year = QComboBox(); year.addItems(["1","2","3"])
    period = QComboBox(); period.addItems(["1","2","3","4"])

    hp = QDoubleSpinBox()
    hp.setRange(0,30)
    hp.setValue(7.5)

    code = QLineEdit()
    name = QLineEdit()

    source = QComboBox()
    source.addItems(["IT","external"])

    grade = QComboBox()
    grade.addItems(["", "A", "B", "C", "D", "E", "F"])

    for t,w in [
        ("Year",year),("Period",period),
        ("HP",hp),("Code",code),("Name",name),
        ("Source",source),("Grade",grade)
    ]:
        form.addRow(t,w)

    add = QPushButton("Add")
    form.addRow(add)

    def submit():

        planner.courses.append(
            Course(
                name=name.text(),
                code=code.text().upper(),
                hp_total=hp.value(),
                hp_done=0,
                year=year.currentIndex(),
                period=period.currentIndex(),
                source=source.currentText(),
                grade=grade.currentText() or None,
                prerequisites=None
            )
        )

        save_courses(planner.courses)
        planner.refresh_ui()

        d.accept()

    add.clicked.connect(submit)

    d.exec()