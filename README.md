# work_timer

A minimal, greyscale Pomodoro timer for macOS, Linux, and Windows.

## features

- configurable work, rest, and long-rest durations
- optional long-rest periods after N work sessions
- daily goal tracking with midnight reset
- history graph showing completed work periods per day
- custom alarm sounds (drop .wav or .mp3 files in `alarms/`)
- adjustable alarm volume
- dark and light colour schemes
- always-on-top support
- keyboard shortcuts: space (play/pause), escape (stop), right arrow (fast-forward)
- window size/position remembered across sessions

## macos

### install

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### run

```
.venv/bin/python main.py
```

### build

```
.venv/bin/pip install -r requirements-dev.txt
./build_mac.sh
# output: dist/work_timer.app
```

## linux

### install

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### run

```
.venv/bin/python main.py
```

### build

```
.venv/bin/pip install -r requirements-dev.txt
./build_linux.sh
# output: dist/work_timer/work_timer
```

## windows

### install

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### run

```
.venv\Scripts\python main.py
```

### build

```
.venv\Scripts\pip install -r requirements-dev.txt
build_windows.bat
# output: dist\work_timer\work_timer.exe
```

## settings

| setting | default | description |
|---------|---------|-------------|
| work_duration | 25 min | length of a work period |
| rest_duration | 5 min | length of a rest period |
| long_rest_duration | 15 min | length of a long rest |
| long_rest | enabled | enable long rest periods |
| work_periods_before_long_rest | 4 | work sessions before a long rest |
| goal | 14 | work periods to complete per day |
| work_days | mon–fri | days that count toward the goal |
| colour_scheme | dark | dark or light |
| always_on_top | disabled | keep window above other windows |
| alarm_sound | default | choose from files in `alarms/` |
| alarm_volume | 100% | alarm loudness |

## tech

python 3.9+, PySide6, matplotlib, SQLite
