"""Tests for PawPal+ core behaviors.

Grouped by feature: basics, sorting, filtering, recurrence, conflict
detection, and the time-budget planner. Recurrence tests pass an explicit
`today` date so they don't depend on the day the suite happens to run.

Run with:  python -m pytest
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


# --- helpers ---------------------------------------------------------------

def build_owner() -> Owner:
    """A small owner with two pets and a few timed tasks, for reuse."""
    owner = Owner("Lisa", available_minutes=90)
    dog = Pet("Biscuit", "Dog")
    dog.add_task(Task("Walk", 30, "high", preferred_time="08:00"))
    dog.add_task(Task("Groom", 45, "low", preferred_time="11:00"))
    cat = Pet("Miso", "Cat")
    cat.add_task(Task("Feed", 10, "high", preferred_time="09:00"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# --- basics (existing) -----------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip a task's completed flag to True."""
    task = Task("Morning walk", duration=30, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should grow that pet's task list by one."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", duration=10, priority="high"))

    assert len(pet.tasks) == 1


def test_add_task_tags_pet_name():
    """Pet.add_task should stamp the task with the pet's name (for filtering)."""
    pet = Pet("Biscuit", "Dog")
    task = Task("Feeding", duration=10, priority="high")
    pet.add_task(task)
    assert task.pet_name == "Biscuit"


# --- sorting correctness ---------------------------------------------------

def test_sort_by_time_orders_chronologically():
    """Tasks should come back earliest-first regardless of insertion order."""
    sched = Scheduler(90)
    tasks = [
        Task("Late", 10, "low", preferred_time="17:00"),
        Task("Early", 10, "high", preferred_time="08:00"),
        Task("Mid", 10, "medium", preferred_time="12:30"),
    ]
    ordered = sched.sort_by_time(tasks)
    assert [t.name for t in ordered] == ["Early", "Mid", "Late"]


def test_sort_by_time_puts_untimed_last():
    """A task with no preferred_time should sort after all timed tasks."""
    sched = Scheduler(90)
    tasks = [
        Task("NoTime", 10, "low"),
        Task("Morning", 10, "high", preferred_time="08:00"),
    ]
    ordered = sched.sort_by_time(tasks)
    assert [t.name for t in ordered] == ["Morning", "NoTime"]


def test_sort_by_time_empty_list():
    """Edge case: sorting no tasks returns an empty list, not an error."""
    assert Scheduler(90).sort_by_time([]) == []


def test_sort_by_time_does_not_mutate_input():
    """sort_by_time returns a new list and leaves the original order intact."""
    sched = Scheduler(90)
    tasks = [
        Task("B", 10, "low", preferred_time="09:00"),
        Task("A", 10, "low", preferred_time="08:00"),
    ]
    sched.sort_by_time(tasks)
    assert [t.name for t in tasks] == ["B", "A"]  # unchanged


# --- filtering -------------------------------------------------------------

def test_filter_by_pet_name():
    """Filtering by pet name returns only that pet's tasks."""
    sched = Scheduler(90)
    biscuit = sched.filter_tasks(build_owner().all_tasks(), pet_name="Biscuit")
    assert len(biscuit) == 2
    assert all(t.pet_name == "Biscuit" for t in biscuit)


def test_filter_by_pet_name_is_case_insensitive():
    """Pet-name matching ignores case."""
    sched = Scheduler(90)
    assert len(sched.filter_tasks(build_owner().all_tasks(), pet_name="biscuit")) == 2


def test_filter_by_completion_status():
    """completed=True/False splits done vs pending tasks."""
    sched = Scheduler(90)
    tasks = build_owner().all_tasks()
    tasks[0].mark_complete()
    assert len(sched.filter_tasks(tasks, completed=True)) == 1
    assert len(sched.filter_tasks(tasks, completed=False)) == len(tasks) - 1


def test_filter_combines_criteria_with_and():
    """Status and pet filters combine: Biscuit's *pending* tasks only."""
    sched = Scheduler(90)
    tasks = build_owner().all_tasks()
    for t in tasks:
        if t.name == "Walk":
            t.mark_complete()
    pending_biscuit = sched.filter_tasks(tasks, completed=False, pet_name="Biscuit")
    assert [t.name for t in pending_biscuit] == ["Groom"]


def test_filter_no_criteria_returns_all():
    """Calling filter_tasks with no criteria returns every task."""
    sched = Scheduler(90)
    tasks = build_owner().all_tasks()
    assert len(sched.filter_tasks(tasks)) == len(tasks)


# --- recurrence logic ------------------------------------------------------

def test_next_occurrence_daily_advances_one_day():
    """A daily task completed today is due again tomorrow, uncompleted."""
    task = Task("Walk", 30, "high", recurrence="daily")
    nxt = task.next_occurrence(today=date(2026, 7, 6))
    assert nxt is not None
    assert nxt.due_date == date(2026, 7, 7)
    assert nxt.completed is False
    assert nxt.name == "Walk"


def test_next_occurrence_weekly_advances_seven_days():
    """A weekly task advances by 7 days."""
    task = Task("Groom", 45, "low", recurrence="weekly")
    nxt = task.next_occurrence(today=date(2026, 7, 6))
    assert nxt.due_date == date(2026, 7, 13)


def test_next_occurrence_non_recurring_returns_none():
    """A one-off task has no next occurrence."""
    task = Task("One-off vet", 60, "high")
    assert task.next_occurrence(today=date(2026, 7, 6)) is None


def test_next_occurrence_handles_month_rollover():
    """Edge case: a daily task completed on Jul 31 rolls over to Aug 1."""
    task = Task("Walk", 30, "high", recurrence="daily")
    nxt = task.next_occurrence(today=date(2026, 7, 31))
    assert nxt.due_date == date(2026, 8, 1)


def test_next_occurrence_handles_year_rollover():
    """Edge case: a daily task completed on Dec 31 rolls over to Jan 1."""
    task = Task("Walk", 30, "high", recurrence="daily")
    nxt = task.next_occurrence(today=date(2026, 12, 31))
    assert nxt.due_date == date(2027, 1, 1)


def test_complete_task_spawns_next_daily_occurrence():
    """Completing a daily task marks it done AND adds tomorrow's occurrence."""
    pet = Pet("Biscuit", "Dog")
    walk = Task("Walk", 30, "high", recurrence="daily")
    pet.add_task(walk)
    assert len(pet.tasks) == 1

    spawned = pet.complete_task(walk, today=date(2026, 7, 6))

    assert walk.completed is True          # original stays, marked done
    assert spawned is not None
    assert spawned.due_date == date(2026, 7, 7)
    assert spawned.completed is False
    assert spawned.pet_name == "Biscuit"   # pet tag carried onto the copy
    assert len(pet.tasks) == 2             # history + next occurrence


def test_complete_task_non_recurring_adds_nothing():
    """Completing a one-off task adds no new task."""
    pet = Pet("Miso", "Cat")
    litter = Task("Litter box", 15, "medium")
    pet.add_task(litter)

    spawned = pet.complete_task(litter, today=date(2026, 7, 6))

    assert spawned is None
    assert litter.completed is True
    assert len(pet.tasks) == 1


# --- conflict detection ----------------------------------------------------

def test_detect_conflicts_flags_same_time_across_pets():
    """Two tasks (different pets) at the same time produce one warning."""
    sched = Scheduler(90)
    tasks = [
        Task("Walk", 30, "high", preferred_time="08:00", pet_name="Biscuit"),
        Task("Meds", 5, "high", preferred_time="08:00", pet_name="Miso"),
    ]
    conflicts = sched.detect_conflicts(tasks)
    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_detect_conflicts_flags_same_pet_same_time():
    """Two tasks for the *same* pet at the same time also clash."""
    sched = Scheduler(90)
    tasks = [
        Task("Walk", 30, "high", preferred_time="08:00", pet_name="Biscuit"),
        Task("Feed", 10, "high", preferred_time="08:00", pet_name="Biscuit"),
    ]
    assert len(sched.detect_conflicts(tasks)) == 1


def test_detect_conflicts_none_when_times_unique():
    """No warnings when every task has a distinct time."""
    sched = Scheduler(90)
    tasks = [
        Task("Walk", 30, "high", preferred_time="08:00"),
        Task("Feed", 10, "high", preferred_time="09:00"),
    ]
    assert sched.detect_conflicts(tasks) == []


def test_detect_conflicts_ignores_untimed_tasks():
    """Edge case: untimed tasks float, so two of them are not a conflict."""
    sched = Scheduler(90)
    tasks = [Task("Play", 20, "low"), Task("Nap", 10, "low")]
    assert sched.detect_conflicts(tasks) == []


def test_detect_conflicts_stores_last_conflicts():
    """detect_conflicts caches its result on last_conflicts."""
    sched = Scheduler(90)
    tasks = [
        Task("A", 10, "high", preferred_time="08:00"),
        Task("B", 10, "high", preferred_time="08:00"),
    ]
    result = sched.detect_conflicts(tasks)
    assert sched.last_conflicts == result
    assert len(sched.last_conflicts) == 1


# --- time-budget planning --------------------------------------------------

def test_pet_with_no_tasks_produces_empty_plan():
    """Edge case: an owner whose pet has no tasks yields an empty plan."""
    owner = Owner("Empty", available_minutes=60)
    owner.add_pet(Pet("Ghost", "Cat"))
    sched = Scheduler(60)
    assert sched.generate_plan(owner.all_tasks()) == []
    assert sched.detect_conflicts(owner.all_tasks()) == []


def test_generate_plan_skips_low_priority_when_time_runs_out():
    """When the budget is tight, the low-priority task is the one skipped."""
    sched = Scheduler(40)
    tasks = [
        Task("Walk", 30, "high"),
        Task("Feed", 10, "high"),
        Task("Groom", 45, "low"),  # won't fit
    ]
    plan = sched.generate_plan(tasks)
    planned_names = [t.name for t in plan]
    skipped_names = [t.name for t in sched.last_skipped]
    assert "Walk" in planned_names and "Feed" in planned_names
    assert skipped_names == ["Groom"]
