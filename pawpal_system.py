from dataclasses import dataclass, field, replace as _replace
from datetime import date as _date, timedelta
from typing import List, Optional
from enum import IntEnum


class Priority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


_TIME_SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}


def _hhmm_to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to total minutes since midnight for arithmetic comparisons."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(minutes: int) -> str:
    """Convert total minutes since midnight back to "HH:MM" for readable warnings."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


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
    preferred_time: str = "any" # "morning", "afternoon", "evening", "any"
    start_time: str = "08:00"   # "HH:MM" 24-hour; used by sort_by_time()
    completed: bool = False
    last_completed_date: Optional[str] = None  # ISO date "YYYY-MM-DD"
    next_due_date: Optional[str] = None        # set by get_next_occurrence()

    def update_task(self, **kwargs) -> None:
        """Update any task field by keyword argument."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def mark_complete(self, date: Optional[str] = None) -> None:
        """Mark this task done; record the date for recurrence tracking."""
        self.completed = True
        if date:
            self.last_completed_date = date

    def reset(self) -> None:
        """Clear the completed flag so the task reappears tomorrow."""
        self.completed = False

    def is_due_today(self, date: str) -> bool:
        """Return True if this task should appear in today's plan.

        Decision order — first matching branch wins:
          1. next_due_date is set  → explicit date from get_next_occurrence();
                                     uses <= so overdue tasks still surface.
          2. frequency == "daily"  → due unless already completed on this date.
          3. frequency == "weekly" → due if never completed, or last completion
                                     was 7+ days ago (timedelta comparison).
          4. frequency == "as-needed" → always eligible; owner decides when.

        Args:
            date: ISO-format date string "YYYY-MM-DD" representing today.
        """
        # next_due_date takes priority when set by get_next_occurrence()
        if self.next_due_date is not None:
            return self.next_due_date <= date  # also catches overdue tasks
        if self.frequency == "daily":
            return self.last_completed_date != date
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            last = _date.fromisoformat(self.last_completed_date)
            today = _date.fromisoformat(date)
            return (today - last).days >= 7
        return True  # "as-needed" always eligible

    def get_next_occurrence(self, completed_date: str) -> Optional["CareTask"]:
        """Return a fresh copy of this task due on its next recurrence date.

        How timedelta works here:
            base = date.fromisoformat("2026-06-23")   # a date object
            base + timedelta(days=1)                  # → 2026-06-24
            base + timedelta(weeks=1)                 # → 2026-06-30

        timedelta stores an offset (days, seconds, microseconds).  Adding it
        to a date object produces a new date shifted by exactly that amount —
        Python handles month rollovers, leap years, etc. automatically.

        Returns None for "as-needed" tasks (no automatic rescheduling).
        """
        if self.frequency == "as-needed":
            return None

        # timedelta in action — the key calculation
        base  = _date.fromisoformat(completed_date)
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        next_date = (base + delta).isoformat()   # back to "YYYY-MM-DD" string

        # dataclasses.replace() copies every field, overriding only what we pass
        return _replace(
            self,
            completed=False,
            last_completed_date=None,
            next_due_date=next_date,
        )

    def get_task_summary(self) -> str:
        """Return a single-line human-readable description of the task."""
        status = "Done" if self.completed else "Pending"
        return (
            f"[{status}] {self.name} ({self.category}) | "
            f"{self.duration} min | Priority: {self.priority.name} | "
            f"Required: {self.required} | Frequency: {self.frequency} | "
            f"Time: {self.preferred_time}"
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
        """Append a care task; raises ValueError if a task with the same name exists."""
        if any(t.name == task.name for t in self.tasks):
            raise ValueError(f"Task '{task.name}' already exists for {self.name}")
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

    def get_all_tasks(
        self,
        pet_name: Optional[str] = None,
        exclude_completed: bool = True,
    ) -> List[CareTask]:
        """Flatten pets' task lists; optionally filter by pet name or skip completed tasks."""
        tasks = [
            task
            for pet in self.pets
            if pet_name is None or pet.name == pet_name
            for task in pet.tasks
        ]
        if exclude_completed:
            tasks = [t for t in tasks if not t.completed]
        return tasks

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
    warnings: List[str] = field(default_factory=list)

    def display_plan(self) -> None:
        """Print the full scheduled and skipped task list to the terminal."""
        print(f"\n=== Daily Plan: {self.date} ===")
        if self.owner:
            print(f"Owner: {self.owner.name}  |  Available: {self.owner.available_time} min")
        print(f"Time used: {self.total_time_used} min\n")
        if self.warnings:
            print("Warnings:")
            for w in self.warnings:
                print(f"  ! {w}")
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

    def sort_tasks(self, tasks: Optional[List[CareTask]] = None) -> List[CareTask]:
        """Sort tasks using a 4-element tuple key for stable multi-criteria ordering.

        Sort key: (not required, priority, time-slot order, duration)
          1. not required  — False sorts before True, so required tasks rise to top.
          2. priority      — Priority is an IntEnum: HIGH=1 < MEDIUM=2 < LOW=3,
                             so lower integer = higher urgency = earlier in list.
          3. time-slot     — _TIME_SLOT_ORDER maps morning→0, afternoon→1,
                             evening→2, any→3; tasks with earlier preferred slots
                             are scheduled before later or unspecified ones.
          4. duration      — shortest task first within a group; this is the
                             greedy knapsack heuristic: fitting more short tasks
                             maximises the number of tasks completed per day.

        Python's sort is stable — tasks equal on all four keys keep insertion order.

        Args:
            tasks: list to sort; defaults to all non-completed owner tasks.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (
                not t.required,
                int(t.priority),
                _TIME_SLOT_ORDER.get(t.preferred_time, 3),
                t.duration,
            ),
        )

    def sort_by_time(self, tasks: Optional[List[CareTask]] = None) -> List[CareTask]:
        """Sort tasks chronologically by start_time ("HH:MM").

        Zero-padded "HH:MM" strings sort lexicographically == chronologically,
        so a plain lambda on the string is all that's needed.
        Ties (same start_time) are broken by shortest duration first.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: (t.start_time, t.duration))

    def filter_tasks(
        self,
        tasks: List[CareTask],
        status: Optional[str] = None,
        pet_name: Optional[str] = None,
    ) -> List[CareTask]:
        """Return a filtered view of a task list using lambda predicates.

        status:   "pending" | "completed" | None (no status filter)
        pet_name: exact pet name          | None (all pets)
        """
        # Map each status label to a lambda that returns True for matching tasks.
        # Using a dict of lambdas makes it easy to add new statuses later.
        STATUS_PREDICATES = {
            "pending":   lambda t: not t.completed,
            "completed": lambda t: t.completed,
        }

        result: List[CareTask] = tasks

        # Apply status filter if a known status was requested
        if status in STATUS_PREDICATES:
            result = list(filter(STATUS_PREDICATES[status], result))

        # Apply pet filter: keep only tasks that belong to the named pet.
        # id(task) is used for identity because CareTask has no back-reference to Pet.
        if pet_name is not None:
            pet_task_ids = {
                id(task)
                for pet in self.owner.pets
                if pet.name == pet_name
                for task in pet.tasks
            }
            result = list(filter(lambda t: id(t) in pet_task_ids, result))

        return result

    def detect_conflicts(
        self, tasks: Optional[List[CareTask]] = None
    ) -> List[str]:
        """Return warning strings for every pair of tasks whose time windows overlap.

        Never raises — always returns a list (empty = no conflicts).

        Overlap test (standard interval arithmetic):
            Convert "HH:MM" + duration to [start, end) in minutes since midnight.
            Two tasks conflict when:
                start_A < end_B  AND  start_B < end_A
            This is the only condition needed — it handles partial overlaps,
            one task contained inside another, and exact same start time.

        The warning message includes the pet name for each task so you can tell
        whether the conflict is within one pet's day or across two pets.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks(exclude_completed=False)

        # Build task-identity → pet-name map for richer messages.
        # id() is used because CareTask has no back-reference to its pet.
        task_to_pet = {
            id(task): pet.name
            for pet in self.owner.pets
            for task in pet.tasks
        }

        warnings: List[str] = []

        # Check every unique pair — O(n²) but fine for a handful of pet tasks
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                a_start = _hhmm_to_minutes(a.start_time)
                a_end   = a_start + a.duration
                b_start = _hhmm_to_minutes(b.start_time)
                b_end   = b_start + b.duration

                if a_start < b_end and b_start < a_end:
                    pet_a = task_to_pet.get(id(a), "?")
                    pet_b = task_to_pet.get(id(b), "?")
                    warnings.append(
                        f"CONFLICT: [{pet_a}] '{a.name}' "
                        f"{a.start_time}–{_minutes_to_hhmm(a_end)}  overlaps  "
                        f"[{pet_b}] '{b.name}' "
                        f"{b.start_time}–{_minutes_to_hhmm(b_end)}"
                    )

        return warnings

    def reschedule_completed_tasks(
        self, pet: "Pet", completed_date: str
    ) -> List[CareTask]:
        """Swap every completed recurring task on `pet` for its next occurrence.

        For each completed task:
          1. Call get_next_occurrence() — uses timedelta to compute the next date.
          2. Remove the completed version from the pet's list.
          3. Add the fresh copy (next_due_date already set) back in.

        Returns the list of newly created next-occurrence tasks so callers can
        inspect or print what was rescheduled.

        "as-needed" tasks return None from get_next_occurrence() and are simply
        removed from the list without replacement.
        """
        rescheduled: List[CareTask] = []

        for task in list(pet.tasks):   # iterate a snapshot — we mutate pet.tasks below
            if not task.completed:
                continue

            next_task = task.get_next_occurrence(completed_date)
            pet.remove_task(task.name)           # drop the completed instance first

            if next_task is not None:
                pet.tasks.append(next_task)      # append directly (name slot is free)
                rescheduled.append(next_task)

        return rescheduled

    def generate_plan(self, date: str) -> DailyPlan:
        """Build today's DailyPlan using a greedy scheduling algorithm.

        Pipeline — each step feeds the next:
          1. Normalize  — "today" is converted to a real ISO date string so
                          recurrence comparisons work correctly.
          2. Candidates — get_all_tasks(exclude_completed=True) drops tasks
                          already marked done.
          3. Due filter — is_due_today() removes tasks not yet due based on
                          their frequency and last_completed_date / next_due_date.
          4. Sort       — sort_tasks() orders by (required, priority, slot, duration)
                          so high-priority required tasks are always attempted first.
          5. Greedy fit — walk the sorted list in order; include a task if
                          time_used + duration <= available, otherwise skip it.
                          This is a greedy knapsack: not globally optimal but
                          fast (O(n)) and predictable for a daily planner.
          6. Warnings   — budget overrun and time-window conflicts are collected
                          into DailyPlan.warnings instead of raising exceptions.

        Side effects:
            Sets self.scheduled_tasks and self.skipped_tasks so that
            explain_plan() can narrate the result without re-running the algorithm.

        Args:
            date: "YYYY-MM-DD" or the literal string "today".

        Returns:
            A fully populated DailyPlan instance.
        """
        # Normalize "today" to a real ISO date string for recurrence comparisons
        today_str = _date.today().isoformat() if date == "today" else date

        # Filter to tasks that are not completed AND are due today per their frequency
        candidates = self.owner.get_all_tasks(exclude_completed=True)
        due_tasks = [t for t in candidates if t.is_due_today(today_str)]

        sorted_tasks = self.sort_tasks(due_tasks)
        available = self.owner.get_availability()
        self.scheduled_tasks = []
        self.skipped_tasks = []
        time_used = 0
        plan_warnings: List[str] = []

        # Conflict detection: warn when required tasks alone exceed available time
        required_time = sum(t.duration for t in sorted_tasks if t.required)
        if required_time > available:
            plan_warnings.append(
                f"Required tasks need {required_time} min but only {available} min "
                f"available — some required tasks will be skipped."
            )

        for task in sorted_tasks:
            if time_used + task.duration <= available:
                self.scheduled_tasks.append(task)
                time_used += task.duration
            else:
                self.skipped_tasks.append(task)

        # Detect time-window conflicts among scheduled tasks and surface as warnings
        plan_warnings.extend(self.detect_conflicts(self.scheduled_tasks))

        return DailyPlan(
            date=today_str,
            owner=self.owner,
            scheduled_tasks=self.scheduled_tasks,
            skipped_tasks=self.skipped_tasks,
            total_time_used=time_used,
            warnings=plan_warnings,
        )

    def explain_plan(self) -> str:
        """Return a human-readable narrative of the last generated plan."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No plan generated yet — call generate_plan() first."

        def section(title: str, tasks: list) -> list:
            return [title] + [f"  - {t.get_task_summary()}" for t in tasks]

        lines = [
            f"Plan for {self.owner.name} ({self.owner.available_time} min available)",
            *section("\nScheduled tasks:", self.scheduled_tasks),
        ]
        if self.skipped_tasks:
            lines += section("\nSkipped (not enough time remaining):", self.skipped_tasks)

        return "\n".join(lines)
