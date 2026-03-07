# Study Planner (PyQt6)

A visual study planning application built with **Python and PyQt6** that
helps students organize courses, track progress, and monitor degree
requirements.

The application provides a drag-and-drop study grid, progress tracking,
and grade statistics in an intuitive interface.

------------------------------------------------------------------------

# Features

## Course Planning

-   Organize courses by **year and period**
-   Visual grid layout for easy overview
-   Drag-and-drop courses between periods

## Progress Tracking

Tracks several types of progress automatically:

-   Total completed HP
-   IT program progress (out of 180 HP)
-   MatNat block progress
-   IT block progress
-   Yearly progress (60 HP per year)

All progress is visualized using **game-style progress bars**.

------------------------------------------------------------------------

## Course Status System

Courses can have different statuses:

-   Planned
-   In progress
-   Completed
-   Failed

Each status has its own color for quick visual recognition.

------------------------------------------------------------------------

## Grade Tracking

Courses can optionally store a **grade**.

The program calculates:

-   Weighted grade average
-   Grade equivalent (A--F)

Example:

Grade Average: 3.03 (C)

Grades are weighted by course HP.

------------------------------------------------------------------------

## Course Categories

Courses are automatically categorized into:

-   **MatNat block**
-   **IT block**
-   **External courses**

These are visually indicated by colored borders:

  Indicator            Meaning
  -------------------- -----------------
  Left orange border   External course
  Right red border     MatNat block
  Right blue border    IT block

------------------------------------------------------------------------

## Interactive Course Labels

When hovering over a course you can see:

-   Course name
-   Grade (if available)

The labels include:

-   Smooth hover animation
-   Fade effect
-   Drag-and-drop support

------------------------------------------------------------------------

## Keyboard Shortcuts

  Key   Action
  ----- ---------------------------------------
  ESC   Close application with fade animation

------------------------------------------------------------------------

# Project Structure

study-planner/

├── main.py\
├── planner.py\
├── course.py\
├── stats.py\
├── dialogs.py\
├── ui_components.py

├── data/\
│ └── courses.json

└── README.md

------------------------------------------------------------------------

## File overview

  File                Purpose
  ------------------- ---------------------------------------
  main.py             Application entry point
  planner.py          Main UI and layout
  course.py           Course data model and UI label
  stats.py            All calculations (HP, blocks, grades)
  dialogs.py          Add/edit course dialogs
  ui_components.py    UI elements like progress bars
  data/courses.json   Stored course data

------------------------------------------------------------------------

# Installation

## Requirements

Python 3.10+

Install dependencies:

pip install PyQt6

------------------------------------------------------------------------

# Running the Program

Run the application:

python main.py

------------------------------------------------------------------------

# Building a Standalone Executable

You can package the application into a single executable using
**PyInstaller**.

Install PyInstaller:

pip install pyinstaller

Build the executable:

pyinstaller --onefile --windowed main.py

The executable will appear in:

dist/main.exe

You can share this file with others.

------------------------------------------------------------------------

# Future Improvements

Possible improvements for the application:

-   Export study plan to PDF
-   GPA prediction
-   Dark mode
-   Course search/filter
-   Statistics graphs
-   Cloud sync

------------------------------------------------------------------------

# Author

Created as a personal study planning tool using **Python + PyQt6**.
