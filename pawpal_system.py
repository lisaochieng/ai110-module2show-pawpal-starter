"""PawPal+ logic layer.

Backend classes for the pet care planner. See diagrams/uml.mmd for the design.
"""

from dataclasses import dataclass, field

# Lower number = higher priority. Used to sort tasks in the daily plan.
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, grooming, etc.)."""

    name: str
    duration: int  # minutes
    priority: str  # "high", "medium", or "low"
    preferred_time: str = ""  # optional, e.g. "08:00"
    recurrence: str = ""  # optional frequency, e.g. "daily", "weekly"
    completed: bool = False

    def is_recurring(self) -> bool:
        """Return True if this task repeats on some frequency."""
        return bool(self.recurrence.strip())

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
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet (no error if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)

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
