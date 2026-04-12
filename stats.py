from datetime import datetime
# ---------- PROGRAM CONSTANTS ----------

HP_PER_YEAR = 60

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

GRADE_VALUES = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "E": 1,
    "F": 0
}

IT_PROGRAM_HP    = 180   # kandidat default
MASTER_PROGRAM_HP = 300
MATNAT_BLOCK_HP  = 15
IT_BLOCK_HP      = 21

CSN_MAX_WEEKS_KANDIDAT = 160
CSN_MAX_WEEKS_MASTER   = 240

# ---------- CSN CONSTANTS ----------

CSN_WEEKS_PER_TERM  = 20    # veckor per termin
CSN_HP_PER_WEEK     = 1.5   # 1,5 HP = 1 heltidsvecka
CSN_RATE_EARLY      = 0.625 # första 40 heltidsveckor: 62,5%
CSN_RATE_NORMAL     = 0.75  # efter 40 heltidsveckor: 75%
CSN_EARLY_CUTOFF    = 40    # gräns för lägre krav


def csn_required_hp(weeks_total):
    """
    Ackumulerat HP-krav efter ett givet antal heltidsveckor.
    Första 40 veckorna: 62,5%, därefter 75%.
    CSN avrundar kravet nedåt till närmaste heltal.
    """
    if weeks_total <= 0:
        return 0
    first = min(weeks_total, CSN_EARLY_CUTOFF) * CSN_HP_PER_WEEK * CSN_RATE_EARLY
    rest  = max(0, weeks_total - CSN_EARLY_CUTOFF) * CSN_HP_PER_WEEK * CSN_RATE_NORMAL
    return int(first + rest)  # avrundat nedåt


def csn_stats(courses, weeks_used, level="master"):
    """
    Beräkna CSN-relaterad statistik.
    weeks_used = antal heltidsveckor förbrukade INNAN nuvarande period.
    level = 'kandidat' eller 'master'
    """
    max_weeks    = CSN_MAX_WEEKS_KANDIDAT if level == "kandidat" else CSN_MAX_WEEKS_MASTER
    completed_hp = sum(c.hp_done for c in courses)

    weeks_after_this = weeks_used + CSN_WEEKS_PER_TERM
    weeks_left       = max(0, max_weeks - weeks_after_this)
    terms_left       = weeks_left // CSN_WEEKS_PER_TERM

    required_now        = csn_required_hp(weeks_used)
    required_after_this = csn_required_hp(weeks_after_this)

    csn_ok    = completed_hp >= required_now
    hp_needed = max(0.0, round(required_after_this - completed_hp, 1))
    at_risk   = hp_needed > (CSN_WEEKS_PER_TERM * CSN_HP_PER_WEEK)

    return {
        "completed_hp":  completed_hp,
        "weeks_used":    weeks_used,
        "weeks_left":    weeks_left,
        "terms_left":    terms_left,
        "required_now":  required_now,
        "required_next": required_after_this,
        "hp_needed":     hp_needed,
        "csn_ok":        csn_ok,
        "at_risk":       at_risk,
    }


def missing_prerequisites(course, courses):

    if not course.prerequisites:
        return []

    completed = {
        c.code for c in courses
        if c.status == "completed"
    }

    missing_groups = []

    for group in course.prerequisites:
        satisfied = any(code in completed for code in group)

        if not satisfied:
            missing_groups.append(group)

    return missing_groups

def normalize_grade(grade):
    """Normaliserar grade input."""
    if not grade:
        return None

    grade = grade.strip().upper()

    return grade if grade in GRADE_VALUES else None


def calculate_grade_average(courses):
    """HP-viktat betygssnitt."""

    total_weighted = 0
    total_hp = 0

    for c in courses:
        if c.pass_fail:
            continue

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
    return sum(
        c.hp_done
        for c in courses
        if c.source == "IT"
    )


def total_it_hp(courses):
    return sum(c.hp_total for c in courses if c.source == "IT")

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

def upcoming_events(courses):
    """Returnerar alla upcoming events sorterade efter datum."""

    events = []

    for c in courses:

        if not c.important_dates:
            continue

        for d in c.important_dates:

            # stöd för både gamla och nya format
            if isinstance(d, str):
                title = ""
                date = d
            else:
                title = d.get("title", "")
                date = d.get("date", "")

            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
            except:
                continue

            events.append({
                "date": dt,
                "title": title,
                "course": c.code
            })

    events.sort(key=lambda x: x["date"])

    return events