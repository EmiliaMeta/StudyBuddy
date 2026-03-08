import json
from course import Course
from utils import resource_path


def load_courses():

    try:
        with open(resource_path("data/courses.json"), encoding="utf-8") as f:
            courses = json.load(f)

        for c in courses:
            c.setdefault("grade", None)

        return [Course(**c) for c in courses]

    except Exception as e:
        print("Failed to load courses:", e)
        return []


def save_courses(courses):

    try:
        with open(resource_path("data/courses.json"), "w", encoding="utf-8") as f:
            json.dump([c.__dict__ for c in courses], f, indent=4)

    except Exception as e:
        print("Failed to save courses:", e)