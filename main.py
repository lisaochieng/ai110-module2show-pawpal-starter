"""Temporary testing ground for PawPal+ logic.

Run with:  python main.py
Builds an owner with a couple of pets and prints today's schedule.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and a few care tasks."""
    owner = Owner(name="Lisa", available_minutes=90)

    dog = Pet(name="Biscuit", species="Dog", breed="Golden Retriever")
    dog.add_task(Task("Morning walk", duration=30, priority="high", preferred_time="08:00"))
    dog.add_task(Task("Feeding", duration=10, priority="high", preferred_time="08:30"))
    dog.add_task(Task("Grooming", duration=45, priority="low"))

    cat = Pet(name="Miso", species="Cat", breed="Tabby")
    cat.add_task(Task("Feeding", duration=10, priority="high", preferred_time="09:00"))
    cat.add_task(Task("Litter box", duration=15, priority="medium"))
    cat.add_task(Task("Play time", duration=20, priority="medium"))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan in a readable, terminal-friendly layout."""
    plan = scheduler.generate_plan(owner.all_tasks())

    print("=" * 44)
    print(f"  Today's Schedule for {owner.name}")
    print(f"  Time available: {owner.available_minutes} min")
    print("=" * 44)

    if not plan:
        print("  Nothing scheduled.")
    else:
        for i, task in enumerate(plan, start=1):
            time = task.preferred_time or "  -  "
            print(f"  {i}. [{time:>5}] {task.name:<16} {task.duration:>3} min  ({task.priority})")

    if scheduler.last_skipped:
        print("-" * 44)
        print("  Skipped (not enough time):")
        for task in scheduler.last_skipped:
            print(f"    - {task.name} ({task.duration} min, {task.priority})")

    print("=" * 44)
    print("\nWhy this plan?")
    print(scheduler.explain())


if __name__ == "__main__":
    owner = build_demo_owner()
    scheduler = Scheduler(owner.available_minutes)
    print_schedule(owner, scheduler)
