import sys
from PyQt6.QtWidgets import QApplication
from planner import StudyPlanner

app = QApplication(sys.argv)

window = StudyPlanner()
window.showFullScreen()


sys.exit(app.exec())