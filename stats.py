# ---------- PROGRAM CONSTANTS ----------

HP_PER_YEAR = 60


# ---------- COURSE BLOCKS ----------

COURSE_BLOCKS = {
    "matnat": {
        "SF1686","SF1626","SF1683","SF1633",
        "EQ1110","SK1118","SK1110","DD1351","SF1546"
    },
    "it": {
        "DD2350","DD2352","ID1214","IV1351",
        "ID1217","II1303","IV1350","IS1300","IL1333"
    }
}


EXCLUSIVE_GROUPS = [
    {"EQ1110","SF1683","SF1633"},
    {"DD2350","DD2352"}
]


# ---------- UI COLORS ----------

BLOCK_COLORS = {
    "matnat": "#ff6b6b",
    "it": "#4dabf7",
}

SOURCE_COLORS = {
    "external": "#f59f00",
}

PERIOD_COLORS = [
    ("#e6ccff","#99ccff"),
    ("#ffd6e7","#ffb3d1"),
    ("#d4ffd4","#99ffcc"),
    ("#fff0b3","#ffd480"),
]

STATUS_COLORS = {
    "planned": "white",
    "in progress": "#87CEFA",
    "completed": "#7CFC9A",
    "failed": "#FF7F7F",
}

GRADE_COLORS = {
    "A": "#22c55e",
    "B": "#4ade80",
    "C": "#facc15",
    "D": "#fb923c",
    "E": "#ef4444",
}


# ---------- GRADE SYSTEM ----------

GRADE_VALUES = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "E": 1,
    "F": 0
}


def normalize_grade(grade):
    """Normaliserar grade input."""
    if not grade:
        return None

    grade = grade.strip().upper()

    return grade if grade in GRADE_VALUES else None


# ---------- STAT FUNCTIONS ----------

def calculate_grade_average(courses):
    """HP-viktat betygssnitt."""

    total_weighted = 0
    total_hp = 0

    for c in courses:

        grade = normalize_grade(c.grade)

        if not grade:
            continue

        value = GRADE_VALUES[grade]

        total_weighted += value * c.hp_total
        total_hp += c.hp_total

    if total_hp == 0:
        return None

    return round(total_weighted / total_hp, 2)

def numeric_to_grade(avg):

    if avg is None:
        return None

    if avg >= 4.5:
        return "A"
    if avg >= 3.5:
        return "B"
    if avg >= 2.5:
        return "C"
    if avg >= 1.5:
        return "D"
    if avg >= 0.5:
        return "E"

    return "F"


def total_completed_hp(courses):
    return sum(c.hp_done for c in courses)


def total_it_hp(courses):
    return sum(c.hp_total for c in courses if c.source == "IT")


# ---------- BLOCK LOGIC ----------

def course_block(course):
    """Returnerar vilket block kursen tillhör."""

    for block, codes in COURSE_BLOCKS.items():
        if course.code in codes:
            return block

    return None


def filter_exclusive_courses(courses):
    """Hantera kurser där bara en får räknas."""

    used = set()
    result = []

    for course in courses:

        if course.code in used:
            continue

        for group in EXCLUSIVE_GROUPS:

            if course.code in group:

                group_courses = [
                    c for c in courses if c.code in group
                ]

                best = max(group_courses, key=lambda x: x.hp_done)

                result.append(best)
                used.update(group)

                break
        else:
            result.append(course)

    return result


def block_hp(courses, block):
    """Returnerar HP för ett block."""

    codes = COURSE_BLOCKS.get(block, set())

    filtered = [
        c for c in courses if c.code in codes
    ]

    filtered = filter_exclusive_courses(filtered)

    return sum(c.hp_done for c in filtered)