from dataclasses import dataclass, field
from typing import List, Optional
from enum import IntEnum


class Priority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


# ─────────────────────────────────────────────
# CareTask  — a single pet care activity
# ─────────────────────────────────────────────
@dataclass
class CareTask:
    name: str
    duration: int               # minutes
    priority: Priority
    category: str               # "feeding", "walk", "medication", "grooming", etc.
    required: bool = True
    frequency: str = "daily"    # "daily", "weekly", "as-needed"
    completed: bool = False

    def update_task(self, **kwargs) -> None:
        """Update any task field by keyword argument."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.completed = True

    def reset(self) -> None:
        """Clear the completed flag so the task reappears tomorrow."""
        self.completed = False

    def get_task_summary(self) -> str:
        """Return a single-line human-readable description of the task."""
        status = "Done" if self.completed else "Pending"
        return (
            f"[{status}] {self.name} ({self.category}) | "
            f"{self.duration} min | Priority: {self.priority.name} | "
            f"Required: {self.required} | Frequency: {self.frequency}"
        )


# ─────────────────────────────────────────────
# Pet  — stores pet details + its own task list
# ─────────────────────────────────────────────
@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    energy_level: str           # "low", "medium", "high"
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Append a new care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> None:
        """Remove the task matching task_name from this pet's list."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_tasks(
        self,
        category: Optional[str] = None,
        required_only: bool = False,
    ) -> List[CareTask]:
        """Return tasks, optionally filtered by category or required status."""
        result = self.tasks
        if category:
            result = [t for t in result if t.category == category]
        if required_only:
            result = [t for t in result if t.required]
        return result

    def update_pet_info(self, **kwargs) -> None:
        """Update any pet field by keyword argument (tasks list is protected)."""
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "tasks":
                setattr(self, key, value)

    def get_pet_summary(self) -> str:
        """Return a single-line summary of the pet's profile and task count."""
        return (
            f"{self.name} ({self.species}, {self.breed}) | "
            f"Age: {self.age} | Energy: {self.energy_level} | "
            f"Tasks: {len(self.tasks)}"
        )


# ─────────────────────────────────────────────
# Owner  — manages multiple pets; aggregates all tasks
# ─────────────────────────────────────────────
@dataclass
class Owner:
    name: str
    available_time: int         # minutes per day
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[CareTask]:
        """Flatten all pets' task lists into one list for the Scheduler."""
        return [task for pet in self.pets for task in pet.tasks]

    def update_profile(
        self,
        name: Optional[str] = None,
        available_time: Optional[int] = None,
        preferences: Optional[List[str]] = None,
    ) -> None:
        """Update owner name, daily time budget, or care preferences."""
        if name is not None:
            self.name = name
        if available_time is not None:
            self.available_time = available_time
        if preferences is not None:
            self.preferences = preferences

    def get_availability(self) -> int:
        """Return the owner's total available minutes for today."""
        return self.available_time


# ─────────────────────────────────────────────
# DailyPlan  — output produced by the Scheduler
# ─────────────────────────────────────────────
@dataclass
class DailyPlan:
    date: str                   # "YYYY-MM-DD"
    owner: Optional[Owner] = field(default=None)
    scheduled_tasks: List[CareTask] = field(default_factory=list)
    skipped_tasks: List[CareTask] = field(default_factory=list)
    total_time_used: int = 0    # minutes

    def display_plan(self) -> None:
        """Print the full scheduled and skipped task list to the terminal."""
        print(f"\n=== Daily Plan: {self.date} ===")
        if self.owner:
            print(f"Owner: {self.owner.name}  |  Available: {self.owner.available_time} min")
        print(f"Time used: {self.total_time_used} min\n")
        print("Scheduled:")
        for task in self.scheduled_tasks:
            print(f"  {task.get_task_summary()}")
        if self.skipped_tasks:
            print("\nSkipped (time ran out):")
            for task in self.skipped_tasks:
                print(f"  {task.get_task_summary()}")

    def show_skipped_tasks(self) -> None:
        """Print only the tasks that were skipped due to time constraints."""
        if not self.skipped_tasks:
            print("No tasks were skipped.")
            return
        print("Skipped tasks:")
        for task in self.skipped_tasks:
            print(f"  {task.get_task_summary()}")

    def get_summary(self) -> str:
        """Return a one-line string with date, counts, and total time used."""
        return (
            f"Date: {self.date} | "
            f"Scheduled: {len(self.scheduled_tasks)} | "
            f"Skipped: {len(self.skipped_tasks)} | "
            f"Time used: {self.total_time_used} min"
        )


# ─────────────────────────────────────────────
# Scheduler  — the "brain": retrieves tasks from
#              Owner → pets, sorts, and fits them
#              into the owner's available time.
#
# Retrieval chain:
#   Scheduler.owner
#       └─ Owner.get_all_tasks()
#               └─ [pet.tasks for pet in owner.pets]
# ─────────────────────────────────────────────
class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.scheduled_tasks: List[CareTask] = []
        self.skipped_tasks: List[CareTask] = []

    def sort_tasks(self) -> List[CareTask]:
        """Sort all tasks: required first, then by priority, then shortest duration."""
        tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (not t.required, int(t.priority), t.duration),
        )

    def generate_plan(self, date: str) -> DailyPlan:
        """Greedily fit sorted tasks into the owner's available time and return a DailyPlan."""
        sorted_tasks = self.sort_tasks()        # explicit call — no hidden re-sort
        available = self.owner.get_availability()
        self.scheduled_tasks = []
        self.skipped_tasks = []
        time_used = 0

        for task in sorted_tasks:
            if task.completed:
                continue                        # skip already-done tasks
            if time_used + task.duration <= available:
                self.scheduled_tasks.append(task)
                time_used += task.duration
            else:
                self.skipped_tasks.append(task)

        return DailyPlan(
            date=date,
            owner=self.owner,
            scheduled_tasks=self.scheduled_tasks,
            skipped_tasks=self.skipped_tasks,
            total_time_used=time_used,
        )

    def explain_plan(self) -> str:
        """Return a human-readable narrative of the last generated plan."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No plan generated yet — call generate_plan() first."

        lines = [
            f"Plan for {self.owner.name}  "
            f"({self.owner.available_time} min available)"
        ]
        lines.append("\nScheduled tasks:")
        for task in self.scheduled_tasks:
            lines.append(f"  - {task.get_task_summary()}")

        if self.skipped_tasks:
            lines.append("\nSkipped (not enough time remaining):")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.get_task_summary()}")

        return "\n".join(lines)
