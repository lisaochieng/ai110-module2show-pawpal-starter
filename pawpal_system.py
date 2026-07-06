"""PawPal+ logic layer.

Backend classes for the pet care planner. See diagrams/uml.mmd for the design.
"""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Lower number = higher priority. Used to sort tasks in the daily plan.
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# How many days until a recurring task's next occurrence.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, grooming, etc.)."""

    name: str
    duration: int  # minutes
    priority: str  # "high", "medium", or "low"
    preferred_time: str = ""  # optional, e.g. "08:00"
    recurrence: str = ""  # optional frequency, e.g. "daily", "weekly"
    completed: bool = False
    pet_name: str = ""  # set automatically by Pet.add_task, used for filtering
    due_date: date | None = None  # the day this occurrence is scheduled for

    def is_recurring(self) -> bool:
        """Return True if this task repeats on some frequency."""
        return bool(self.recurrence.strip())

    def next_occurrence(self, today: date | None = None) -> "Task | None":
        """Return a fresh, uncompleted copy scheduled for the next occurrence.

        Returns None for one-off (non-recurring) tasks. For a "daily" task the
        new due_date is today + 1 day; for "weekly" it's today + 7 days. We use
        timedelta so the arithmetic rolls over months and years correctly
        (e.g. Jul 31 + 1 day -> Aug 1). The `today` argument defaults to the
        real current date but can be passed explicitly to make tests
        deterministic.
        """
        interval = RECURRENCE_DAYS.get(self.recurrence.strip().lower())
        if interval is None:
            return None
        base = today if today is not None else date.today()
        return replace(
            self,
            due_date=base + timedelta(days=interval),
            completed=False,
        )

    def priority_rank(self) -> int:
        """Return a sortable rank for this task's priority (lower = higher).

        Unknown priorities sort last.
        """
        return PRIORITY_ORDER.get(self.priority.strip().lower(), len(PRIORITY_ORDER))

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True


@dataclass
class Pet:
    """A pet owned by the user, with its own list of care tasks."""

    name: str
    species: str
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet, tagging it with the pet's name.

        Tagging lets the Scheduler filter a flat list of tasks by pet later.
        """
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet (no error if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def complete_task(self, task: Task, today: date | None = None) -> Task | None:
        """Mark a task complete and roll a recurring task to its next date.

        Marks `task` done. If it recurs ("daily"/"weekly"), a fresh copy for
        the next occurrence is created and added to this pet automatically,
        then returned. For one-off tasks nothing new is added and None is
        returned. The completed task stays in the list as history.
        """
        task.mark_complete()
        upcoming = task.next_occurrence(today)
        if upcoming is not None:
            self.add_task(upcoming)
        return upcoming

    def pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that still need doing."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    """The person using PawPal+, with their pets and daily time budget."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet for this owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


class Scheduler:
    """The brain: retrieves, organizes, and manages tasks across pets."""

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes
        self.last_plan: list[Task] = []  # tasks that fit, in order
        self.last_skipped: list[Task] = []  # tasks dropped for lack of time
        self.last_conflicts: list[str] = []  # warnings from detect_conflicts

    def generate_plan(self, tasks: list[Task]) -> list[Task]:
        """Build a daily plan from the given tasks.

        Considers only incomplete tasks, orders them by priority (then by
        shorter duration so more fit), and greedily includes tasks until the
        available time runs out. Tasks that don't fit are recorded in
        last_skipped. Accepts tasks from a single pet or from Owner.all_tasks(),
        so it can plan across pets.
        """
        pending = [task for task in tasks if not task.completed]
        ordered = sorted(pending, key=lambda t: (t.priority_rank(), t.duration))

        plan: list[Task] = []
        skipped: list[Task] = []
        remaining = self.available_minutes
        for task in ordered:
            if task.duration <= remaining:
                plan.append(task)
                remaining -= task.duration
            else:
                skipped.append(task)

        self.last_plan = plan
        self.last_skipped = skipped
        return plan

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by preferred_time ("HH:MM"), earliest first.

        Uses sorted() with a lambda as the key. Zero-padded "HH:MM" strings
        sort lexicographically in the same order they fall on a clock
        ("08:00" < "08:30" < "09:00"), so we can sort the strings directly
        with no time parsing. Tasks with no preferred_time are pushed to the
        end by substituting a sentinel ("99:99") that sorts after any real
        time. sorted() is stable, so tasks with equal times keep their
        insertion order.
        """
        return sorted(tasks, key=lambda task: task.preferred_time or "99:99")

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return the subset of tasks matching the given criteria.

        completed: True -> only finished tasks, False -> only pending,
                   None -> don't filter on status.
        pet_name:  keep only tasks belonging to the named pet
                   (case-insensitive); None -> don't filter on pet.

        Criteria combine with AND. Pass nothing to get every task back.
        """
        result = list(tasks)
        if completed is not None:
            result = [task for task in result if task.completed == completed]
        if pet_name is not None:
            result = [
                task for task in result
                if task.pet_name.lower() == pet_name.lower()
            ]
        return result

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Detect tasks scheduled for the same time slot and warn about them.

        Lightweight strategy: tasks are grouped by their exact "HH:MM"
        preferred_time, and any slot holding more than one task is reported.
        This catches clashes both within one pet and across different pets
        (a dog walk and a cat feeding both booked for 08:00). Tasks with no
        preferred_time are ignored, since a floating task can't collide.

        Returns a list of human-readable warning strings (empty when there are
        no conflicts) and also stores it on self.last_conflicts. It never
        raises: a clash produces a warning message, not a crash, so the caller
        can surface it and carry on.
        """
        by_time: dict[str, list[Task]] = {}
        for task in tasks:
            slot = task.preferred_time.strip()
            if not slot:
                continue
            by_time.setdefault(slot, []).append(task)

        warnings: list[str] = []
        for slot in sorted(by_time):
            clashing = by_time[slot]
            if len(clashing) > 1:
                labels = ", ".join(f"{t.name} ({t.pet_name})" for t in clashing)
                warnings.append(
                    f"Conflict at {slot}: {len(clashing)} tasks booked "
                    f"together - {labels}"
                )

        self.last_conflicts = warnings
        return warnings

    def explain(self) -> str:
        """Return a short explanation of the last generated plan."""
        if not self.last_plan and not self.last_skipped:
            return "No plan has been generated yet."

        scheduled_minutes = sum(task.duration for task in self.last_plan)
        lines = [
            f"You have {self.available_minutes} min available today.",
            f"Scheduled {len(self.last_plan)} task(s) using {scheduled_minutes} min, "
            "ordered by priority (higher priority first, shorter tasks breaking ties):",
        ]
        for task in self.last_plan:
            lines.append(f"  - {task.name} ({task.duration} min, {task.priority})")

        if self.last_skipped:
            lines.append(
                f"Skipped {len(self.last_skipped)} task(s) that didn't fit the time budget:"
            )
            for task in self.last_skipped:
                lines.append(f"  - {task.name} ({task.duration} min, {task.priority})")

        return "\n".join(lines)
