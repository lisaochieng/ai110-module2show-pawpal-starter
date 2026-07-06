"""Temporary testing ground for PawPal+ logic.

Run with:  python main.py
Builds an owner with a couple of pets and exercises the Scheduler's
sorting, filtering, and planning methods in the terminal.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and a few care tasks.

    Tasks are added intentionally OUT OF TIME ORDER so we can prove that
    Scheduler.sort_by_time() really reorders them (and isn't just relying
    on the order we happened to type them in).
    """
    owner = Owner(name="Lisa", available_minutes=90)

    dog = Pet(name="Biscuit", species="Dog", breed="Golden Retriever")
    dog.add_task(Task("Grooming", duration=45, priority="low", preferred_time="11:00",
                      recurrence="weekly"))
    dog.add_task(Task("Morning walk", duration=30, priority="high", preferred_time="08:00",
                      recurrence="daily"))
    dog.add_task(Task("Feeding", duration=10, priority="high", preferred_time="08:30",
                      recurrence="daily"))

    cat = Pet(name="Miso", species="Cat", breed="Tabby")
    cat.add_task(Task("Play time", duration=20, priority="medium", preferred_time="17:00"))
    cat.add_task(Task("Feeding", duration=10, priority="high", preferred_time="09:00",
                      recurrence="daily"))
    cat.add_task(Task("Litter box", duration=15, priority="medium"))  # no set time, one-off
    # Deliberate clash: Miso's meds are booked at 08:00, the same slot as
    # Biscuit's morning walk -> a cross-pet conflict for detect_conflicts().
    cat.add_task(Task("Medication", duration=5, priority="high", preferred_time="08:00"))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


def format_task(task: Task) -> str:
    """One-line, terminal-friendly description of a task."""
    time = task.preferred_time or "  -  "
    recur = f" (recur.: {task.recurrence})" if task.is_recurring() else ""
    due = f" due {task.due_date}" if task.due_date else ""
    done = " [DONE]" if task.completed else ""
    return (
        f"[{time:>5}] {task.name:<14} {task.duration:>3} min  "
        f"({task.priority:<6}) - {task.pet_name}{recur}{due}{done}"
    )


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a labeled list of tasks."""
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("  (none)")
        return
    for task in tasks:
        print(f"  {format_task(task)}")


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan in a readable, terminal-friendly layout."""
    plan = scheduler.generate_plan(owner.all_tasks())

    print("\n" + "=" * 48)
    print(f"  Today's Schedule for {owner.name}")
    print(f"  Time available: {owner.available_minutes} min")
    print("=" * 48)

    if not plan:
        print("  Nothing scheduled.")
    else:
        for i, task in enumerate(plan, start=1):
            print(f"  {i}. {format_task(task)}")

    if scheduler.last_skipped:
        print("-" * 48)
        print("  Skipped (not enough time):")
        for task in scheduler.last_skipped:
            print(f"    - {task.name} ({task.duration} min, {task.priority})")

    print("=" * 48)


if __name__ == "__main__":
    owner = build_demo_owner()
    scheduler = Scheduler(owner.available_minutes)

    all_tasks = owner.all_tasks()

    # --- As entered (deliberately out of order) --------------------------
    print_tasks("All tasks (as entered - unsorted):", all_tasks)

    # --- Sorting by time -------------------------------------------------
    print_tasks(
        "All tasks sorted by time (sort_by_time):",
        scheduler.sort_by_time(all_tasks),
    )

    # --- Conflict detection ----------------------------------------------
    print("\nConflict detection (detect_conflicts):")
    print("-" * 38)
    conflicts = scheduler.detect_conflicts(all_tasks)
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No time conflicts found.")

    # --- Filtering by pet name -------------------------------------------
    print_tasks(
        "Filtered: only Biscuit's tasks (filter_tasks pet_name=...):",
        scheduler.filter_tasks(all_tasks, pet_name="Biscuit"),
    )

    # --- Filtering by completion status ----------------------------------
    # Mark one one-off task complete so the status filter has something to
    # hide. (We use Miso's "Play time" here so it doesn't collide with the
    # recurring-task demo further down, which completes Biscuit's walk.)
    all_tasks[3].mark_complete()  # Play time (Miso), non-recurring
    print_tasks(
        "Filtered: only pending tasks (filter_tasks completed=False):",
        scheduler.filter_tasks(all_tasks, completed=False),
    )
    print_tasks(
        "Filtered: only completed tasks (filter_tasks completed=True):",
        scheduler.filter_tasks(all_tasks, completed=True),
    )

    # --- Combining sort + filter -----------------------------------------
    misos_pending = scheduler.filter_tasks(
        scheduler.sort_by_time(all_tasks), completed=False, pet_name="Miso"
    )
    print_tasks("Miso's pending tasks, sorted by time:", misos_pending)

    # --- Recurring tasks: completing one spawns the next occurrence ------
    dog = owner.pets[0]
    walk = dog.tasks[1]  # "Morning walk", recurrence="daily"
    print_tasks("Biscuit's tasks BEFORE completing the daily walk:", dog.tasks)

    spawned = dog.complete_task(walk)
    print(f"\nCompleted '{walk.name}'. Auto-created next occurrence: "
          f"{spawned.name} due {spawned.due_date}")

    print_tasks(
        "Biscuit's tasks AFTER (note the completed one stays + a new dated one):",
        dog.tasks,
    )

    # --- Full daily plan (existing behaviour) ----------------------------
    print_schedule(owner, scheduler)
    print("\nWhy this plan?")
    print(scheduler.explain())
