from PyQt6.QtWidgets import QProgressBar, QGridLayout


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
        "completed": QProgressBar(),
        "matnat": QProgressBar(),
        "it_block": QProgressBar()
    }

    bars["it_program"].setMaximum(180)
    bars["completed"].setMaximum(180)
    bars["matnat"].setMaximum(15)
    bars["it_block"].setMaximum(21)

    # ---------- styling (game style bars) ----------

    style_bar(bars["it_program"], "#3b82f6", "#1d4ed8")   # blue
    style_bar(bars["completed"], "#4ade80", "#16a34a")    # green
    style_bar(bars["matnat"], "#8e90d0", "#6569cf")       # red
    style_bar(bars["it_block"], "#e585d5", "#e35ccd")     # light blue

    # ---------- layout ----------

    layout = QGridLayout()

    layout.addWidget(bars["it_program"], 0, 0)
    layout.addWidget(bars["completed"], 1, 0)
    layout.addWidget(bars["matnat"], 0, 1)
    layout.addWidget(bars["it_block"], 1, 1)

    layout.setHorizontalSpacing(15)
    layout.setVerticalSpacing(6)

    for bar in bars.values():
        bar.setFixedHeight(26)

    return {
        "bars": bars,
        "layout": layout
    }