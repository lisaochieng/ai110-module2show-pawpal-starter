"""PawPal+ logic layer.

Backend classes for the pet care planner, generated as skeletons from the UML
in diagrams/uml.mmd. Method bodies are stubs to be filled in later.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, grooming, etc.)."""

    name: str
    duration: int  # minutes
    priority: str  # e.g. "high", "medium", "low"
    preferred_time: str = ""  # optional, e.g. "08:00"
    recurrence: str = ""  # optional, e.g. "daily", "weekly"

    def is_recurring(self) -> bool:
        """Return True if this task repeats (daily/weekly)."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet owned by the user, with its own list of care tasks."""

    name: str
    species: str
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The person using PawPal+, along with their pets and daily time budget."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet for this owner."""
        raise NotImplementedError


class Scheduler:
    """Builds a daily plan from a pet's tasks and the owner's time budget."""

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    def generate_plan(self, pet: Pet) -> list[Task]:
        """Return an ordered list of tasks that fit the available time."""
        raise NotImplementedError

    def explain(self) -> str:
        """Return a short explanation of how the plan was ordered."""
        raise NotImplementedError
