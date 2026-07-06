# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

PawPal+ is more than a task list — the `Scheduler` applies real algorithms to
turn a pile of tasks into a sensible daily plan:

- **Priority-based planning** — greedily packs the day's tasks by priority
  (high → low), fits them within the owner's time budget, and reports anything
  that had to be skipped (`Scheduler.generate_plan`).
- **Sorting by time** — orders tasks chronologically from their `"HH:MM"`
  preferred time, with untimed tasks placed last (`Scheduler.sort_by_time`).
- **Filtering** — narrows the task list by pet (case-insensitive) and/or
  completion status (`Scheduler.filter_tasks`).
- **Conflict warnings** — flags when two tasks (same pet or different pets)
  are booked for the same time slot, returning a friendly warning instead of
  crashing (`Scheduler.detect_conflicts`).
- **Daily / weekly recurrence** — completing a recurring task automatically
  schedules its next occurrence (daily → +1 day, weekly → +7 days) while
  keeping the finished one as history (`Task.next_occurrence` +
  `Pet.complete_task`).
- **Plan explanations** — a plain-language summary of what was scheduled,
  what was skipped, and why (`Scheduler.explain`).

See [Smarter Scheduling](#-smarter-scheduling) below for the method-by-method
details, and `diagrams/uml_final.mmd` for the class design.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output from running `python main.py`:

```
============================================
  Today's Schedule for Lisa
  Time available: 90 min
============================================
  1. [08:30] Feeding           10 min  (high)
  2. [09:00] Feeding           10 min  (high)
  3. [08:00] Morning walk      30 min  (high)
  4. [  -  ] Litter box        15 min  (medium)
  5. [  -  ] Play time         20 min  (medium)
--------------------------------------------
  Skipped (not enough time):
    - Grooming (45 min, low)
============================================

Why this plan?
You have 90 min available today.
Scheduled 5 task(s) using 85 min, ordered by priority (higher priority first, shorter tasks breaking ties):
  - Feeding (10 min, high)
  - Feeding (10 min, high)
  - Morning walk (30 min, high)
  - Litter box (15 min, medium)
  - Play time (20 min, medium)
Skipped 1 task(s) that didn't fit the time budget:
  - Grooming (45 min, low)
```

## 🧪 Testing PawPal+

Run the full suite from the project root with:

```bash
python -m pytest
```

> Use `python -m pytest` (not bare `pytest`) so the repo root is on
> `sys.path` and the tests can import `pawpal_system`.

### What the tests cover

The suite in `tests/test_pawpal.py` (26 tests) verifies every "smarter
scheduling" behavior, covering both happy paths and edge cases:

- **Basics** — `mark_complete()` flips status; `Pet.add_task()` grows the list and tags the task with its pet name.
- **Sorting** (`sort_by_time`) — chronological order, untimed tasks sort last, empty list is safe, and the input list is not mutated.
- **Filtering** (`filter_tasks`) — by pet name (case-insensitive), by completion status, both combined with AND, and no-criteria returns all.
- **Recurrence** (`next_occurrence` / `complete_task`) — daily → +1 day, weekly → +7 days, non-recurring returns `None`, the completed task stays as history, and **month/year rollovers** (Jul 31 → Aug 1, Dec 31 → Jan 1) are correct.
- **Conflict detection** (`detect_conflicts`) — flags same-time clashes within one pet and across pets, no false positives on unique times, and ignores untimed tasks.
- **Planning** (`generate_plan`) — a pet with no tasks yields an empty plan (no crash), and the low-priority task is the one skipped when time runs out.

### Successful test run

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 26 items

tests/test_pawpal.py ..........................                          [100%]

============================= 26 passed in 0.04s ==============================
```

### Confidence level

**⭐⭐⭐⭐☆ (4 / 5)** — All 26 tests pass, covering every scheduling feature
plus the tricky edge cases (empty task lists, date rollovers, untimed tasks).
I held back the fifth star because conflict detection only checks exact time
matches, not overlapping durations (see `reflection.md` §2b), and there are no
tests yet for the Streamlit UI layer in `app.py`.

## 📐 Smarter Scheduling

Beyond the basic priority-and-time plan, PawPal+ adds four "smarter" scheduling
behaviors. Each is a small, independently testable method in `pawpal_system.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting by time | `Scheduler.sort_by_time()` | Orders tasks by `preferred_time`; untimed tasks sort last |
| Filtering | `Scheduler.filter_tasks()` | By completion status and/or pet name (combine with AND) |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns when two tasks share the same `"HH:MM"` slot |
| Recurring tasks | `Task.next_occurrence()` + `Pet.complete_task()` | Completing a daily/weekly task auto-creates the next dated one |

### Sorting behavior — `Scheduler.sort_by_time(tasks)`

Returns tasks ordered by their `preferred_time`, earliest first. Because
zero-padded `"HH:MM"` strings sort lexicographically in the same order they fall
on a clock (`"08:00" < "08:30" < "09:00"`), it sorts the strings directly via a
`sorted()` lambda key — no time parsing needed. Tasks with no `preferred_time`
are pushed to the end. The sort is non-mutating (returns a new list).

### Filtering behavior — `Scheduler.filter_tasks(tasks, *, completed=None, pet_name=None)`

Returns the subset of tasks matching the given criteria:

- `completed=True/False` — only finished / only pending tasks (`None` = ignore).
- `pet_name="Biscuit"` — only that pet's tasks (case-insensitive; `None` = ignore).

Criteria combine with AND, so `filter_tasks(tasks, completed=False, pet_name="Miso")`
returns Miso's pending tasks. Pet-name filtering works because `Pet.add_task()`
tags each task with its owning pet's name (`Task.pet_name`).

### Conflict detection — `Scheduler.detect_conflicts(tasks)`

A lightweight check that groups tasks by their exact `"HH:MM"` `preferred_time`
and returns a list of warning strings for any slot holding more than one task —
catching clashes both within one pet and across different pets. It **never
raises**: a clash produces a warning message (also stored on
`Scheduler.last_conflicts`), not a crash. Untimed tasks are ignored. It checks
exact time matches only, not overlapping durations (see `reflection.md` §2b).

### Recurring task logic — `Task.next_occurrence()` + `Pet.complete_task()`

Tasks may carry a `recurrence` of `"daily"` or `"weekly"`. When a recurring task
is completed via `Pet.complete_task(task)`, the completed instance stays as
history and a fresh, uncompleted copy is auto-created for the next occurrence:
**daily → today + 1 day, weekly → today + 7 days**, computed with
`datetime.timedelta` so month/year rollovers are correct (Jul 31 → Aug 1). The
date math lives in `Task.next_occurrence()`; `Pet.complete_task()` orchestrates
marking done and adding the new occurrence to the pet's list.

## 📸 Demo Walkthrough

### What the UI lets you do

Launch the app with `streamlit run app.py`. From the single-page interface a
pet owner can:

- **Set their profile** — name and how many minutes they have for pet care today.
- **Add pets** — name, species, optional breed.
- **Add tasks** to a chosen pet — title, duration, priority, an optional
  `"HH:MM"` preferred time, and a repeat setting (none / daily / weekly).
- **View, filter, and sort tasks** — a live table with dropdowns to filter by
  pet or completion status and to sort by time or entry order.
- **See conflict warnings** — a yellow banner appears the moment two tasks share
  a time slot, naming the clash and suggesting a fix.
- **Mark tasks done** — completing a recurring task instantly schedules its next
  occurrence and confirms the new date.
- **Generate today's schedule** — a prioritized, time-boxed plan in a clean
  table, a list of anything skipped for lack of time, and a "Why this plan?"
  explanation.

### Example workflow

1. Enter your name and set "Time available today" to `90` minutes.
2. Add a pet: **Mochi**, a dog.
3. Add a task for Mochi: **Morning walk**, 30 min, high priority, time `08:00`,
   repeat **daily**.
4. Add another: **Meds**, 5 min, high priority, time `08:00`.
5. The task table updates and a **conflict warning** appears — both tasks are at
   08:00.
6. Mark "Morning walk" done — the app confirms the next daily walk is scheduled
   for tomorrow.
7. Click **Generate schedule** to see the prioritized plan for today.

### Key Scheduler behaviors on display

- **Sorting** — the task table's "Sort by → Time" option calls
  `Scheduler.sort_by_time`, putting `08:00` before `09:00` and untimed tasks last.
- **Filtering** — the pet/status dropdowns call `Scheduler.filter_tasks`.
- **Conflict warnings** — the banner is driven by `Scheduler.detect_conflicts`.
- **Recurrence** — "Mark done" calls `Pet.complete_task`, which uses
  `Task.next_occurrence` to roll the task to its next date.

### Sample CLI output (`python main.py`)

The same logic can be exercised from the terminal. Running `python main.py`
prints the sorted/filtered task views, a conflict warning, a recurrence demo,
and the final plan:

```
Conflict detection (detect_conflicts):
--------------------------------------
  Conflict at 08:00: 2 tasks booked together - Morning walk (Biscuit), Medication (Miso)

Completed 'Morning walk'. Auto-created next occurrence: Morning walk due 2026-07-07

================================================
  Today's Schedule for Lisa
  Time available: 90 min
================================================
  1. [08:00] Medication       5 min  (high  ) - Miso
  2. [08:30] Feeding         10 min  (high  ) - Biscuit (recur.: daily)
  3. [09:00] Feeding         10 min  (high  ) - Miso (recur.: daily)
  4. [08:00] Morning walk    30 min  (high  ) - Biscuit (recur.: daily) due 2026-07-07
  5. [  -  ] Litter box      15 min  (medium) - Miso
------------------------------------------------
  Skipped (not enough time):
    - Grooming (45 min, low)
================================================
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
