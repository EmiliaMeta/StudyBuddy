import sys
import os


def resource_path(relative_path):
    """
    Sökväg till bundlade/read-only filer.
    Fungerar både under utveckling och i PyInstaller-bygge.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def writable_path(relative_path):
    """
    Sökväg till skrivbara filer (courses.json, profile.json, csn_weeks.json).
    När fryst (exe): bredvid .exe-filen.
    Under utveckling: projektmappen.
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)