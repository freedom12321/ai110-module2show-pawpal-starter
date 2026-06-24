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

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python3 -m pytest tests/test_pawpal.py -v
```

Run with coverage:

```bash
python3 -m pytest tests/test_pawpal.py -v --cov=pawpal_system --cov-report=term-missing
```

### What the tests cover

| Area | Tests |
|---|---|
| **Task lifecycle** | Marking a task complete flips `completed` to `True`; adding tasks increments the pet's task count |
| **Sorting correctness** | `sort_by_time()` returns tasks in ascending `start_time` order; ties are broken by shortest duration first |
| **Recurrence logic** | A completed daily task's `get_next_occurrence()` returns a fresh copy with `next_due_date` set to the following day; `reschedule_completed_tasks()` removes the old task and appends the new one; `as-needed` tasks are removed without replacement |
| **Conflict detection** | Same `start_time` triggers a warning; partial time-window overlap triggers a warning; adjacent tasks (end == start) do **not** trigger a warning |

### Successful test run output

```
============================= test session starts ==============================
platform darwin -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/lihanxia/Documents/codepath /ai110-module2show-pawpal-starter
collected 10 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [ 10%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 20%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 30%]
tests/test_pawpal.py::test_sort_by_time_tie_broken_by_shortest_duration PASSED [ 40%]
tests/test_pawpal.py::test_get_next_occurrence_daily_advances_one_day PASSED [ 50%]
tests/test_pawpal.py::test_reschedule_completed_tasks_replaces_daily_task PASSED [ 60%]
tests/test_pawpal.py::test_as_needed_task_not_rescheduled PASSED         [ 70%]
tests/test_pawpal.py::test_detect_conflicts_same_start_time PASSED       [ 80%]
tests/test_pawpal.py::test_detect_conflicts_partial_overlap PASSED       [ 90%]
tests/test_pawpal.py::test_detect_conflicts_adjacent_tasks_do_not_conflict PASSED [100%]

============================== 10 passed in 0.01s ==============================
```

### Confidence Level: ★★★★☆ (4/5)

The core scheduling logic — sorting, conflict detection, and daily recurrence — is well-covered and all tests pass. One star is held back because `generate_plan()`'s greedy fit loop (the full end-to-end budget allocation) is not yet tested directly, and `is_due_today()` for the weekly branch (6-day vs. 7-day boundary) also has no test. Adding those two cases would bring confidence to 5/5.

## 📐 Smarter Scheduling

The scheduling logic lives in `pawpal_system.py` across five classes: `CareTask`, `Pet`, `Owner`, `DailyPlan`, and `Scheduler`.

### Feature overview

| Feature | Method(s) | Where |
|---|---|---|
| Sort by priority | `Scheduler.sort_tasks()` | `Scheduler` |
| Sort by start time | `Scheduler.sort_by_time()` | `Scheduler` |
| Filter by status or pet | `Scheduler.filter_tasks()` | `Scheduler` |
| Conflict detection | `Scheduler.detect_conflicts()` | `Scheduler` |
| Recurrence check | `CareTask.is_due_today()` | `CareTask` |
| Next occurrence | `CareTask.get_next_occurrence()` | `CareTask` |
| Auto-reschedule | `Scheduler.reschedule_completed_tasks()` | `Scheduler` |

---

### Sorting

#### `Scheduler.sort_tasks(tasks=None)`

Sorts tasks using a 4-element tuple key so multiple criteria are applied in one pass:

```
key = (not required, priority int, time-slot order, duration)
```

| Position | Field | Logic |
|---|---|---|
| 1 | `required` | `not required` → `False < True`, required tasks rise to top |
| 2 | `priority` | `Priority` is an `IntEnum`: `HIGH=1 < MEDIUM=2 < LOW=3` |
| 3 | `preferred_time` | `morning=0, afternoon=1, evening=2, any=3` via `_TIME_SLOT_ORDER` |
| 4 | `duration` | Shortest first — greedy heuristic to fit more tasks in the time budget |

Used internally by `generate_plan()` before the greedy fit loop.

#### `Scheduler.sort_by_time(tasks=None)`

Sorts tasks chronologically by their `start_time` field (`"HH:MM"` string).

```python
sorted(tasks, key=lambda t: (t.start_time, t.duration))
```

Zero-padded `"HH:MM"` strings sort lexicographically in the same order as chronologically, so no date conversion is needed. Ties on start time are broken by shortest duration first. Used when displaying the task table in the UI with "Sort by: start time" selected.

---

### Filtering

#### `Scheduler.filter_tasks(tasks, status=None, pet_name=None)`

Returns a filtered view of a task list without mutating the original. Both filters are optional and can be combined.

**Status filter** — implemented with a dict of lambda predicates:

```python
STATUS_PREDICATES = {
    "pending":   lambda t: not t.completed,
    "completed": lambda t: t.completed,
}
result = list(filter(STATUS_PREDICATES[status], tasks))
```

Using a dict of lambdas means adding a new status (e.g. `"overdue"`) requires one new entry, not a new `elif` branch.

**Pet filter** — since `CareTask` has no back-reference to its pet, the method builds an identity set using `id()`:

```python
pet_task_ids = {id(task) for pet in owner.pets if pet.name == pet_name for task in pet.tasks}
result = list(filter(lambda t: id(t) in pet_task_ids, result))
```

In `app.py`, both filters are applied before sorting so the sort only runs on the visible subset.

---

### Conflict Detection

#### `Scheduler.detect_conflicts(tasks=None)`

Checks every unique pair of tasks for time-window overlap. Returns a list of warning strings — never raises an exception.

**Overlap test** (standard interval arithmetic):

```python
a_start = _hhmm_to_minutes(a.start_time)   # "09:15" → 555
a_end   = a_start + a.duration

# Two tasks conflict when:
if a_start < b_end and b_start < a_end:
    # overlap exists
```

This single condition covers all three overlap shapes:

| Shape | Example |
|---|---|
| Partial overlap | A: 09:00–09:30, B: 09:15–09:45 |
| One task contained inside another | A: 09:00–10:00, B: 09:15–09:30 |
| Exact same start time | A: 09:00–09:20, B: 09:00–09:15 |

Each warning message names the pet for both tasks so cross-pet conflicts are immediately visible:

```
CONFLICT: [Buddy] 'Morning Walk' 07:00–07:30  overlaps  [Buddy] 'Breakfast' 07:15–07:25
```

`generate_plan()` calls `detect_conflicts(self.scheduled_tasks)` automatically and appends any findings to `DailyPlan.warnings`, so warnings surface in both the CLI output and the Streamlit UI.

Two helper functions support this method:

- `_hhmm_to_minutes(hhmm)` — converts `"HH:MM"` → total minutes since midnight
- `_minutes_to_hhmm(minutes)` — converts minutes back to `"HH:MM"` for readable end-times in warnings

---

### Recurring Tasks

Three methods work together to handle daily and weekly recurrence.

#### `CareTask.is_due_today(date)`

Decides whether a task should appear in today's plan. Decision order — first matching branch wins:

| Branch | Condition | Due when |
|---|---|---|
| Explicit next date | `next_due_date` is set | `next_due_date <= today` (catches overdue) |
| Daily | `frequency == "daily"` | `last_completed_date != today` |
| Weekly | `frequency == "weekly"` | Never completed, or last completion was 7+ days ago |
| As-needed | `frequency == "as-needed"` | Always eligible |

#### `CareTask.get_next_occurrence(completed_date)`

Returns a fresh copy of the task scheduled for its next recurrence date, using Python's `timedelta`:

```python
base  = date.fromisoformat(completed_date)   # e.g. 2026-06-23
delta = timedelta(days=1)   # daily
#       timedelta(weeks=1)  # weekly
next_date = (base + delta).isoformat()        # → "2026-06-24"
```

`timedelta` handles month rollovers, leap years, and year boundaries automatically. The fresh copy is created with `dataclasses.replace()`, which copies all fields and overrides only `completed=False`, `last_completed_date=None`, and `next_due_date=next_date`.

Returns `None` for `"as-needed"` tasks — no automatic rescheduling.

#### `Scheduler.reschedule_completed_tasks(pet, completed_date)`

Swaps every completed recurring task on a pet for its next occurrence in one call:

1. Iterates a snapshot of `pet.tasks` (so mutations mid-loop are safe)
2. Calls `get_next_occurrence()` for each completed task
3. Removes the completed instance with `pet.remove_task()` (clears the name slot)
4. Appends the fresh copy directly back to `pet.tasks`
5. Returns the list of newly created tasks so callers can display what was rescheduled

`"as-needed"` tasks that return `None` from `get_next_occurrence()` are removed without replacement.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## Sample Output

====================================================
       PawPal+ — Today's Schedule
====================================================
Owner : Alex
Pets  : Buddy, Luna
Budget: 90 min available
----------------------------------------------------

Scheduled Tasks:
  [REQUIRED]   Breakfast              5 min  (feeding)
  [REQUIRED]   Litter Box             5 min  (grooming)
  [REQUIRED]   Breakfast             10 min  (feeding)
  [REQUIRED]   Morning Walk          30 min  (walk)
  [REQUIRED]   Flea Treatment         5 min  (medication)
  [REQUIRED]   Hairball Meds          5 min  (medication)
  [optional]   Laser Toy             15 min  (enrichment)

  Total time used: 75 min / 90 min

Skipped (not enough time):
  - Fetch / Play (20 min)

----------------------------------------------------
Plan for Alex  (90 min available)

Scheduled tasks:
  - [Pending] Breakfast (feeding) | 5 min | Priority: HIGH | Required: True | Frequency: daily
  - [Pending] Litter Box (grooming) | 5 min | Priority: HIGH | Required: True | Frequency: daily
  - [Pending] Breakfast (feeding) | 10 min | Priority: HIGH | Required: True | Frequency: daily
  - [Pending] Morning Walk (walk) | 30 min | Priority: HIGH | Required: True | Frequency: daily
  - [Pending] Flea Treatment (medication) | 5 min | Priority: MEDIUM | Required: True | Frequency: weekly
  - [Pending] Hairball Meds (medication) | 5 min | Priority: MEDIUM | Required: True | Frequency: weekly
  - [Pending] Laser Toy (enrichment) | 15 min | Priority: LOW | Required: False | Frequency: daily

Skipped (not enough time remaining):
  - [Pending] Fetch / Play (enrichment) | 20 min | Priority: LOW | Required: False | Frequency: daily