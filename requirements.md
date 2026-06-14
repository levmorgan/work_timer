# Pomodoro Timer – Requirements Document

## 1. Overview
A stylish, minimal Pomodoro timer desktop application written in Python.  
**Color scheme**: greyscale (monochromatic).  
**Core purpose**: track work and rest periods, display daily progress toward a configurable goal, and provide historical statistics.

---

## 2. Technology Stack
- **Language**: Python 3
- **GUI framework**: PySide (Qt for Python)
- **Graph plotting**: Matplotlib (embedded in PySide)
- **Data storage**: SQLite database

---

## 3. Core User Interface

### 3.1 Main Timer View
- **Center, large**: Remaining time in current work or rest period (MM:SS format).
- **Below, center, smaller**: Daily completion counter and goal, e.g. `5/14`.
  - On non‑work days: show `0/0`.
  - Resets at midnight (system time) regardless of work‑day setting.
- **Upper‑right corner**:
  - First line: period type – `"work"`, `"rest"`, or `"long rest"`.
  - Second line (only during work periods, right‑aligned): progress toward long rest, e.g. `3/4`.
    - Tracks consecutive work sessions since the last long rest. Resets **only after a long rest**.
- **Upper‑left corner**:
  - **Gear icon** → opens Settings screen.
  - **Graph icon** (to the right of gear) → opens Stats screen.

### 3.2 Timer Controls (bottom center)
- **Play/Pause button**: starts or pauses the timer.
- **Stop button**: 
  - If timer is at the beginning of a work period *and* paused, does nothing.
  - Otherwise, resets to the start of a work period and leaves timer paused.
- **Fast‑forward button**: skips to the next period in the sequence (work → rest → long rest → work, etc.).
  - After skipping, timer remains **paused** – user must start it manually.

### 3.3 End‑of‑Period Behaviour
- When a work or rest period reaches 00:00:
  - A **sound** plays.
  - The timer digits **blink**.
  - A **modal** appears with two buttons: `"Continue"` and `"Finish"`.
    - `"Continue"`: proceeds to the next period (as per sequence) and starts the timer automatically.
    - `"Finish"`: stops the timer and returns to the start of a work period, paused.
  - If the user does not interact within **5 minutes**, the alert stops automatically and the timer enters the paused state at the beginning of the next period.

---

## 4. Settings Screen
Accessible via the gear icon. Configurable options:

| Setting | Description | Default (suggestion) |
|---------|-------------|------------------------|
| Work duration | Length of a work period (minutes) | 25 |
| Rest duration | Length of a rest period (minutes) | 5 |
| Long rest | Enable/disable long rest periods | Enabled |
| Work periods before long rest | How many work sessions before a long rest | 4 |
| Goal | Number of work periods to complete per day | 14 |
| Work days | Days of the week to count for stats | Monday–Friday |
| Colour scheme | Dark or Light (greyscale) | Dark |
| Always on top | Keep the timer window always visible | Disabled |

---

## 5. Stats Screen
Accessible via the graph icon.

- Displays a **line graph** of work periods completed per day.
- When the line is hovered, it should show the date and number of work periods completed.
- X‑axis: only days that are **configured as work days** (no gaps for non‑work days).
- Y‑axis: number of completed work periods.
- Today’s partial progress **is included** (current count so far).
- Time range buttons: `7d`, `30d`, `90d`, `All`
  - `All` shows every day since first recorded use.
- Data is read from the SQLite database.

---

## 6. Data Persistence
### 6.1 SQLite Database
- Stores:
  - User settings.
  - Daily completion records (date, work periods finished).
- On first run, database is created automatically.
- Window size and position are also persisted (e.g., in the database or a separate config table).

### 6.2 Daily Counter Reset
- At midnight (system clock), the daily counter resets to 0, even if the application is open.

---

## 7. Additional Functionality
### 7.1 Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Space | Play / Pause |
| Escape | Stop (same as Stop button) |
| Right arrow | Fast‑forward |

### 7.2 Always on Top
- Toggle in Settings; when enabled, the main window stays above other windows.

### 7.3 Window State
- The application remembers its **size and position** across sessions.
- It **does not** minimize to the system tray.

---

## 8. Miscellaneous
- The design is minimal and clean.
- No unnecessary decorations or complex animations (blinking digits on period end is the only dynamic effect).
- Sound file: a simple, short alert (to be bundled or generated programmatically).

---

**End of document**
