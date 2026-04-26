# StudyBuddy: Visual Study Planner

A desktop application built in Python to help KTH students visually plan their degree, track progress, and monitor grades — all in one place.

> Built as a personal tool to solve a real problem: KTH's official planning tools are clunky and don't give a good overview of your degree progress.

---

## Features

- **Drag-and-drop course grid**: organize courses across years and study periods visually
- **Automatic progress tracking**: total HP, IT block, MatNat block, and yearly goals (60 HP/year)
- **Game-style progress bars**: instant visual feedback on degree completion
- **Course status system**: Planned / In Progress / Completed / Failed, color-coded
- **Weighted GPA calculator**: calculates grade average weighted by course HP, with letter grade (A–F)
- **Course categories**: automatically tags courses as IT block, MatNat block, or external, shown via colored borders
- **Smooth hover animations**: course labels with fade effects and drag-and-drop support
- **Standalone executable**: packaged with PyInstaller, no Python installation required for end users

---

## Screenshots

*Coming soon*

---

## Architecture

The project is structured around separation of concerns, with dedicated modules for data, UI, and logic:

```
StudyBuddy/
├── main.py            # Entry point
├── planner.py         # Main UI and layout
├── course.py          # Course data model and UI label
├── stats.py           # All calculations (HP, blocks, GPA)
├── dialogs.py         # Add/edit course dialogs
├── ui_components.py   # Reusable UI elements (progress bars etc.)
└── data/
    └── courses.json   # Persistent course data
```

**Key design decisions:**
- `stats.py` is fully decoupled from UI. All calculations are pure functions, easy to test
- `course.py` separates the data model from the visual label component
- JSON-based persistence keeps the data portable and human-readable

---

## Getting Started

**Requirements:** Python 3.10+

```bash
# Install dependencies
pip install PyQt6

# Run the application
python main.py
```

**Or download the standalone executable** (no Python needed):
> See [Releases](../../releases)

### Build it yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
# Output: dist/main.exe
```

---

## 🔧 Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| PyQt6 | Desktop UI framework |
| JSON | Data persistence |
| PyInstaller | Packaging as standalone executable |

---

## Roadmap

- [ ] Export study plan to PDF
- [ ] GPA prediction / what-if calculator
- [ ] Dark mode
- [ ] Course search and filter
- [ ] Statistics graphs
- [ ] Cloud sync

---

## Author

**Emilia Lindqvist**  
Civil engineering student in Information Technology, KTH  
emiliameta@gmail.com · [GitHub](https://github.com/EmiliaMeta)
