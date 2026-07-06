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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
