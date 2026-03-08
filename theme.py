from stats import course_block

# ---------- APP COLORS ----------

APP_BACKGROUND = "#C396A1"
CARD_BACKGROUND = "#A28089"

ACCENT_PRIMARY = "#64B9C4"
ACCENT_SECONDARY = "#9DF9EF"
ACCENT_WARNING = "#FFAFB6"

TEXT_COLOR = "#2f2f2f"

STATUS_COLORS = {
    "planned": "#EDF7F6",
    "in progress": "#9DC8F9",
    "completed": "#3EE68F",
    "failed": "#F5737D",
}
GRADE_COLORS = {
    "A": "#6ee7b7",
    "B": "#a7f3d0",
    "C": "#fde68a",
    "D": "#fdba74",
    "E": "#fca5a5",
}
BLOCK_COLORS = {
    "matnat": "#8e90d0",
    "it": "#e585d5",
}
SOURCE_COLORS = {
    "external": "#E9D790",
}
PERIOD_COLORS = [
    ("#e1bdbd", "#F3AAAA"),
    ("#B497CF", "#7A8BC1"),
    ("#D7B6D5", "#BD75A7"),
    ("#DF9AAD", "#BC6A7D"),
]

TITLE_STYLE = """
font-size:22px;
font-weight:bold;
"""

CARD_STYLE = """
background:white;
border-radius:10px;
padding:6px;
"""

WARNING_STYLE = """
color:red;
font-weight:bold;
"""

APP_STYLE = f"""
QWidget {{
    background: {APP_BACKGROUND};
    color: {TEXT_COLOR};
    font-family: "Segoe UI";
}}

QFrame {{
    background: {CARD_BACKGROUND};
    border-radius:8px;
}}

QPushButton {{
    background:{ACCENT_PRIMARY};
    border:none;
    padding:6px;
    border-radius:6px;
}}

QPushButton:hover {{
    background:{ACCENT_SECONDARY};
}}
"""

def course_label_style(background, left_border, right_border):
    """Return stylesheet for course labels."""

    return f"""
    QLabel {{
        background:{background};
        border-left:{left_border};
        border-right:{right_border};
        padding:2px;
        border-radius:4px;
    }}
    """

def year_progress_style(progress, border):
    """Return stylesheet for year progress labels."""

    return f"""
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
    }}
    """

def period_box_style(color1, color2):
    """Style for semester/period boxes in the planner grid."""

    return f"""
    QFrame {{
        background:qlineargradient(
            x1:0,y1:0,x2:1,y2:1,
            stop:0 {color1}, stop:1 {color2});
        border-radius:8px;
    }}
    """

def course_borders(course):
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

    return left, right