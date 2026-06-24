import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import CareTask, Pet, Owner, Scheduler, Priority


def test_mark_complete_changes_status():
    task = CareTask(name="Morning Walk", duration=30, priority=Priority.HIGH, category="walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=2, energy_level="high")
    assert len(pet.tasks) == 0
    pet.add_task(CareTask(name="Breakfast", duration=10, priority=Priority.HIGH, category="feeding"))
    assert len(pet.tasks) == 1
    pet.add_task(CareTask(name="Evening Walk", duration=20, priority=Priority.MEDIUM, category="walk"))
    assert len(pet.tasks) == 2


# ── Sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should order tasks by start_time ascending."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    pet.add_task(CareTask(name="Evening Walk",  duration=20, priority=Priority.LOW,    category="walk",    start_time="18:00"))
    pet.add_task(CareTask(name="Breakfast",     duration=10, priority=Priority.HIGH,   category="feeding", start_time="07:30"))
    pet.add_task(CareTask(name="Afternoon Play",duration=15, priority=Priority.MEDIUM, category="enrichment", start_time="13:00"))

    owner = Owner(name="Alex", available_time=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time()
    times = [t.start_time for t in sorted_tasks]
    assert times == sorted(times), f"Expected chronological order, got {times}"


def test_sort_by_time_tie_broken_by_shortest_duration():
    """When two tasks share a start_time, the shorter one should come first."""
    pet = Pet(name="Luna", species="Cat", breed="Siamese", age=2, energy_level="medium")
    pet.add_task(CareTask(name="Long Med",  duration=20, priority=Priority.HIGH, category="medication", start_time="09:00"))
    pet.add_task(CareTask(name="Short Med", duration= 5, priority=Priority.HIGH, category="medication", start_time="09:00"))

    owner = Owner(name="Alex", available_time=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time()
    assert sorted_tasks[0].name == "Short Med"
    assert sorted_tasks[1].name == "Long Med"


# ── Recurrence logic ─────────────────────────────────────────────────────────

def test_get_next_occurrence_daily_advances_one_day():
    """Completing a daily task should produce a copy due the following day."""
    task = CareTask(name="Breakfast", duration=10, priority=Priority.HIGH,
                    category="feeding", frequency="daily")
    next_task = task.get_next_occurrence("2026-06-23")

    assert next_task is not None
    assert next_task.next_due_date == "2026-06-24"
    assert next_task.completed is False
    assert next_task.last_completed_date is None


def test_reschedule_completed_tasks_replaces_daily_task():
    """reschedule_completed_tasks() should swap a completed daily task for its next occurrence."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    task = CareTask(name="Morning Walk", duration=30, priority=Priority.HIGH,
                    category="walk", frequency="daily")
    task.mark_complete(date="2026-06-23")
    pet.add_task(task)

    owner = Owner(name="Alex", available_time=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    rescheduled = scheduler.reschedule_completed_tasks(pet, completed_date="2026-06-23")

    assert len(rescheduled) == 1
    assert rescheduled[0].next_due_date == "2026-06-24"
    assert rescheduled[0].completed is False
    # The completed original should be gone; only the fresh copy remains
    assert len(pet.tasks) == 1
    assert pet.tasks[0].next_due_date == "2026-06-24"


def test_as_needed_task_not_rescheduled():
    """as-needed tasks should be removed without creating a next occurrence."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    task = CareTask(name="Flea Dip", duration=15, priority=Priority.MEDIUM,
                    category="grooming", frequency="as-needed")
    task.mark_complete()
    pet.add_task(task)

    owner = Owner(name="Alex", available_time=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    rescheduled = scheduler.reschedule_completed_tasks(pet, completed_date="2026-06-23")

    assert rescheduled == []        # nothing to reschedule
    assert len(pet.tasks) == 0      # completed as-needed task is removed


# ── Conflict detection ────────────────────────────────────────────────────────

def test_detect_conflicts_same_start_time():
    """Two tasks with the same start_time must be flagged as a conflict."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    pet.add_task(CareTask(name="Walk",      duration=30, priority=Priority.HIGH,   category="walk",    start_time="09:00"))
    pet.add_task(CareTask(name="Breakfast", duration=10, priority=Priority.HIGH,   category="feeding", start_time="09:00"))

    owner = Owner(name="Alex", available_time=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "CONFLICT" in warnings[0]


def test_detect_conflicts_partial_overlap():
    """Tasks whose windows partially overlap should be flagged."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    # Task A: 09:00–09:30, Task B: 09:15–09:45 → overlap from 09:15 to 09:30
    pet.add_task(CareTask(name="Walk",  duration=30, priority=Priority.HIGH, category="walk",    start_time="09:00"))
    pet.add_task(CareTask(name="Meds",  duration=30, priority=Priority.HIGH, category="medication", start_time="09:15"))

    owner = Owner(name="Alex", available_time=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1


def test_detect_conflicts_adjacent_tasks_do_not_conflict():
    """Tasks that touch end-to-end (A ends exactly when B starts) are NOT a conflict."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3, energy_level="high")
    # Task A: 09:00–09:30, Task B starts at 09:30 — no overlap
    pet.add_task(CareTask(name="Walk",      duration=30, priority=Priority.HIGH, category="walk",    start_time="09:00"))
    pet.add_task(CareTask(name="Breakfast", duration=10, priority=Priority.HIGH, category="feeding", start_time="09:30"))

    owner = Owner(name="Alex", available_time=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts()
    assert warnings == []
