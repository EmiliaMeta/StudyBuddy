import json
from course import Course
from utils import resource_path
from dataclasses import asdict


def load_courses():
    try:
        with open(resource_path("data/courses.json"), encoding="utf-8") as f:
            courses = json.load(f)

        for c in courses:
            c.setdefault("grade", None)
            c.setdefault("notes", "")
            c.setdefault("important_dates", [])
            c.setdefault("pass_fail", False)

        return [Course(**c) for c in courses]

    except Exception as e:
        print("Failed to load courses:", e)
        return []


def save_courses(courses, simulate=False):
    if simulate:
        return
    try:
        with open(resource_path("data/courses.json"), "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in courses], f, indent=4)
    except Exception as e:
        print("Failed to save courses:", e)


def load_csn_weeks():
    try:
        with open(resource_path("data/csn_weeks.json"), encoding="utf-8") as f:
            return json.load(f).get("weeks_used", 0)
    except Exception:
        return 0


def save_csn_weeks(weeks, simulate=False):
    if simulate:
        return
    try:
        with open(resource_path("data/csn_weeks.json"), "w", encoding="utf-8") as f:
            json.dump({"weeks_used": weeks}, f)
    except Exception as e:
        print("Failed to save CSN weeks:", e)


def load_profile():
    try:
        with open(resource_path("data/profile.json"), encoding="utf-8") as f:
            p = json.load(f)
            p.setdefault("name", "")
            p.setdefault("program_code", "")
            p.setdefault("program_name", "")
            p.setdefault("level", "kandidat")
            p.setdefault("csn_weeks", 0)
            return p
    except Exception:
        return {
            "name": "",
            "program_code": "",
            "program_name": "",
            "level": "kandidat",
            "csn_weeks": 0,
        }


def save_profile(profile, simulate=False):
    if simulate:
        return
    try:
        with open(resource_path("data/profile.json"), "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save profile:", e)


def load_program_index():
    try:
        with open(resource_path("data/programs/_index.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_program(code):
    try:
        with open(resource_path(f"data/programs/{code.upper()}.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None