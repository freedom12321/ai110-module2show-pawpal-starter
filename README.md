# PawPal+

A Streamlit app that helps pet owners build a smart daily care schedule. Enter your pet's profile, add care tasks, and the scheduler fits everything into your available time — surfacing priority conflicts and automatically rescheduling recurring tasks for the next day.

---

## Features

### 1. Multi-criteria priority sort
`Scheduler.sort_tasks()` ranks tasks using a 4-element tuple key evaluated in a single pass:

```
key = (not required, priority int, time-slot order, duration)
```

| Position | Field | Logic |
|---|---|---|
| 1 | `required` | Required tasks always appear before optional ones |
| 2 | `priority` | `Priority` IntEnum — HIGH=1 < MEDIUM=2 < LOW=3 |
| 3 | `preferred_time` | morning → afternoon → evening → any |
| 4 | `duration` | Shortest task first — greedy heuristic to fit more tasks per day |

Python's sort is stable, so tasks equal on all four keys keep their insertion order.

### 2. Chronological sort by start time
`Scheduler.sort_by_time()` orders tasks by their `start_time` field (`"HH:MM"`). Zero-padded strings sort lexicographically in the same order as chronologically, so no date parsing is needed. Ties are broken by shortest duration first.

### 3. Greedy daily plan generation
`Scheduler.generate_plan()` runs a greedy knapsack algorithm in O(n):

1. Exclude already-completed tasks
2. Filter to tasks due today via `is_due_today()`
3. Sort by the priority key above
4. Walk the list in order — include a task if `time_used + duration ≤ available`, otherwise skip it
5. Collect conflict warnings and append them to `DailyPlan.warnings`

Not globally optimal, but fast and predictable for a daily planner.

### 4. Conflict detection
`Scheduler.detect_conflicts()` checks every unique pair of tasks for time-window overlap using standard interval arithmetic:

```python
if a_start < b_end and b_start < a_end:   # overlap exists
```

This single condition covers partial overlaps, one task contained inside another, and exact same-start-time pairs. Adjacent tasks (end of A == start of B) correctly produce no warning. Each warning names the pet for both tasks so cross-pet conflicts are immediately visible.

### 5. Recurring task recurrence check
`CareTask.is_due_today(date)` decides whether a task appears in today's plan. Decision order — first matching branch wins:

| Branch | Due when |
|---|---|
| `next_due_date` is set | `next_due_date <= today` — catches overdue tasks |
| `frequency == "daily"` | `last_completed_date != today` |
| `frequency == "weekly"` | Never completed, or last completion was 7+ days ago |
| `frequency == "as-needed"` | Always eligible |

### 6. Automatic next-occurrence scheduling
`CareTask.get_next_occurrence()` uses Python's `timedelta` to compute the next recurrence date:

```python
base  = date.fromisoformat(completed_date)
delta = timedelta(days=1)    # daily
#       timedelta(weeks=1)   # weekly
next_date = (base + delta).isoformat()
```

`timedelta` handles month rollovers, leap years, and year boundaries automatically. A fresh task copy is created with `dataclasses.replace()`, overriding only `completed`, `last_completed_date`, and `next_due_date`. Returns `None` for `as-needed` tasks — no automatic rescheduling.

### 7. End-of-day rescheduling
`Scheduler.reschedule_completed_tasks()` swaps every completed recurring task for its next occurrence in one call. It iterates a snapshot of the task list (safe against mid-loop mutation), removes the completed instance, and appends the fresh copy. `as-needed` tasks are removed without replacement.

### 8. Filter by status or pet
`Scheduler.filter_tasks()` applies optional status (`pending` / `completed`) and pet-name filters without mutating the original list. The status filter is implemented with a dict of lambda predicates — adding a new status requires one new dict entry, not a new `elif` branch.

---

## System design

Five classes make up the core logic in `pawpal_system.py`:

```
Owner ──owns──► Pet ──has──► CareTask ──uses──► Priority (enum)
  │
  └──► Scheduler ──generates──► DailyPlan
```

The retrieval chain runs through `Owner`, not directly to tasks:

```
Scheduler.generate_plan()
    └─ Owner.get_all_tasks()
            └─ pet.tasks  for each pet in owner.pets
```

The UML class diagram source is at [`diagram/uml_final.mmd`](diagram/uml_final.mmd).

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How to use

1. **Owner & Pet Profile** — Enter the owner name, daily time budget (minutes), and pet details. Click **Save profile**.
2. **Add Care Tasks** — Fill in task name, duration, priority, category, frequency, preferred time slot, and start time. Click **Add task**. Repeat for each task.
3. **Filter and sort the task list** — Use the dropdowns above the task table to filter by status or pet, and switch between priority order and chronological order.
4. **Mark a task complete** — Select a pending task from the dropdown and click **Mark done**. Daily and weekly tasks are automatically rescheduled for their next occurrence.
5. **Generate today's schedule** — Click **Generate schedule**. The app shows:
   - Summary metrics (scheduled count, skipped count, time used)
   - Any time-budget or conflict warnings with actionable tips
   - Scheduled tasks table (sorted by priority)
   - Skipped tasks table (tasks that didn't fit in the time budget)
   - A plain-English explanation of why the scheduler chose this order

---

## Demo Walkthrough

### UI features at a glance

| Section | What you can do |
|---|---|
| **Owner & Pet Profile** | Set the owner name, daily time budget (minutes), and pet details. Multiple fields (species, breed, age, energy level) feed into the pet summary shown above the task list. |
| **Add a Care Task** | Choose name, duration, priority (HIGH / MEDIUM / LOW), category, frequency (daily / weekly / as-needed), preferred time slot, and a precise `HH:MM` start time. |
| **Filter & sort controls** | Filter the task table by status (all / pending / completed) and by pet name. Switch sort order between priority rank and chronological start time — the table updates instantly. |
| **Mark a Task Complete** | Select any pending task from a dropdown and click **Mark done**. Daily and weekly tasks are automatically rescheduled for their next occurrence; as-needed tasks are removed. |
| **Generate schedule** | Runs the greedy scheduler. Displays four summary metrics, conflict or budget warnings with tips, a scheduled-tasks table, and a skipped-tasks table. An expandable section shows the plain-English explanation of task order. |

### Example workflow

1. Open the app — `streamlit run app.py` → [http://localhost:8501](http://localhost:8501)
2. **Save profile** — enter owner "Jordan", 90 min available, pet "Mochi" (cat, Siamese, age 2)
3. **Add tasks**:

   | Task | Duration | Priority | Frequency | Start |
   |---|---|---|---|---|
   | Breakfast | 5 min | HIGH | daily | 07:45 |
   | Litter Box | 5 min | HIGH | daily | 09:00 |
   | Hairball Meds | 5 min | MEDIUM | weekly | 11:00 |
   | Laser Toy | 15 min | LOW | daily | 20:00 |

4. **Sort by start time** — the table reorders to 07:45 → 09:00 → 11:00 → 20:00.
5. **Sort by priority** — required HIGH tasks rise to the top; the optional Laser Toy drops to the bottom.
6. **Add a conflicting task** — add "Morning Grooming", 20 min, start time `09:00` (same as Litter Box).
7. **Generate schedule** — a yellow conflict warning appears: _Litter Box (09:00–09:05) overlaps Morning Grooming (09:00–09:20)_ with a tip to adjust one start time.
8. **Mark Hairball Meds done** — a success message shows the next weekly occurrence date (7 days later). The task moves out of pending and reappears with `next_due_date` set.

### Key Scheduler behaviors shown

**Priority sort** — required HIGH tasks always appear before optional LOW tasks, regardless of start time. Within the same priority, shorter tasks come first (greedy heuristic to fit more tasks per day).

**Conflict warnings** — any two tasks whose `[start, start+duration)` windows overlap trigger a warning that names both tasks and their exact windows. Adjacent tasks (one ends at 09:30, the next starts at 09:30) correctly produce no warning.

**Budget overrun** — if required tasks alone exceed available time, a warning appears listing the shortfall in minutes before the schedule table.

**Automatic rescheduling** — marking a daily task done creates a fresh copy due tomorrow; a weekly task lands 7 days later; an as-needed task is removed entirely with no replacement.

---

## CLI demo — `python3 main.py`

`main.py` runs the full scheduling engine without the UI, demonstrating every Scheduler method across two owners (Alex with Buddy and Luna; Sam with Rex and Mochi).

```
timedelta examples
  today      = 2026-06-23
  + 1 day    = 2026-06-24   ← timedelta(days=1)
  + 1 week   = 2026-06-30  ← timedelta(weeks=1)

==================================================================
  BEFORE — tasks as added (no sort, nothing completed yet)
==================================================================

Buddy
------------------------------------------------------------------
  [    ]  18:00  Evening Walk             30 min  daily
  [    ]  07:30  Breakfast                10 min  daily
  [    ]  10:00  Flea Treatment            5 min  weekly
  [    ]  15:30  Fetch / Play             20 min  daily
  [    ]  09:00  Vet Checkup              60 min  as-needed

Luna
------------------------------------------------------------------
  [    ]  20:00  Laser Toy                15 min  daily
  [    ]  09:00  Litter Box                5 min  daily
  [    ]  11:00  Hairball Meds             5 min  weekly
  [    ]  07:45  Breakfast                 5 min  daily

==================================================================
  SORTING DEMO
==================================================================

All tasks — sorted by START TIME  (sort_by_time)
------------------------------------------------------------------
  [    ]  07:30  Breakfast                10 min  daily
  [    ]  07:45  Breakfast                 5 min  daily
  [    ]  09:00  Litter Box                5 min  daily
  [    ]  09:00  Vet Checkup              60 min  as-needed
  [    ]  10:00  Flea Treatment            5 min  weekly
  [    ]  11:00  Hairball Meds             5 min  weekly
  [    ]  15:30  Fetch / Play             20 min  daily
  [    ]  18:00  Evening Walk             30 min  daily
  [    ]  20:00  Laser Toy                15 min  daily

All tasks — sorted by PRIORITY   (sort_tasks)
------------------------------------------------------------------
  [    ]  09:00  Litter Box                5 min  daily
  [    ]  07:45  Breakfast                 5 min  daily
  [    ]  07:30  Breakfast                10 min  daily
  [    ]  18:00  Evening Walk             30 min  daily
  [    ]  09:00  Vet Checkup              60 min  as-needed
  [    ]  10:00  Flea Treatment            5 min  weekly
  [    ]  11:00  Hairball Meds             5 min  weekly
  [    ]  20:00  Laser Toy                15 min  daily
  [    ]  15:30  Fetch / Play             20 min  daily

==================================================================
  RESCHEDULING — reschedule_completed_tasks()
==================================================================

  Rescheduling Buddy's completed tasks from 2026-06-23 …
    Breakfast               (daily)   →  next_due_date = 2026-06-24
    Flea Treatment          (weekly)  →  next_due_date = 2026-06-30

  Rescheduling Luna's completed tasks from 2026-06-23 …
    Hairball Meds           (weekly)  →  next_due_date = 2026-06-30

==================================================================
  TOMORROW'S PLAN  (2026-06-24)
==================================================================

Date: 2026-06-24 | Scheduled: 6 | Skipped: 0 | Time used: 85 min

Scheduled:
  [REQUIRED]    09:00  Litter Box                5 min
  [REQUIRED]    07:45  Breakfast                 5 min
  [REQUIRED]    07:30  Breakfast                10 min
  [REQUIRED]    18:00  Evening Walk             30 min
  [optional]    20:00  Laser Toy                15 min
  [optional]    15:30  Fetch / Play             20 min

==================================================================
  CONFLICT DETECTION DEMO
==================================================================

Task schedule (time-ordered):
  Task                  Pet     Window          Freq
  ----------------------------------------------------
  Morning Walk          Rex     07:00–07:30     daily
  Breakfast             Rex     07:15–07:25     daily    ← overlaps Morning Walk
  Grooming              Rex     09:00–09:20     daily
  Litter Box            Mochi   09:10–09:25     daily    ← overlaps Grooming
  Evening Walk          Rex     18:00–18:30     daily
  Dinner                Mochi   18:45–18:50     daily    ← no overlap (gap)

Running detect_conflicts() on all tasks …

  2 conflict(s) found:
  ! CONFLICT: [Rex] 'Morning Walk' 07:00–07:30  overlaps  [Rex] 'Breakfast' 07:15–07:25
  ! CONFLICT: [Rex] 'Grooming' 09:00–09:20  overlaps  [Mochi] 'Litter Box' 09:10–09:25

Generating plan — conflicts also appear in plan.warnings …

  plan.warnings (2 total):
  ! CONFLICT: [Rex] 'Breakfast' 07:15–07:25  overlaps  [Rex] 'Morning Walk' 07:00–07:30
  ! CONFLICT: [Mochi] 'Litter Box' 09:10–09:25  overlaps  [Rex] 'Grooming' 09:00–09:20
==================================================================
```

---

## Testing

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
| **Task lifecycle** | Marking complete flips `completed` to `True`; adding tasks increments the pet's task count |
| **Chronological sort** | `sort_by_time()` returns tasks in ascending `start_time` order; ties broken by shortest duration first |
| **Recurrence — daily** | `get_next_occurrence()` returns a copy with `next_due_date` set to the following day |
| **Recurrence — reschedule** | `reschedule_completed_tasks()` removes the completed task and appends the fresh copy |
| **Recurrence — as-needed** | Completed as-needed tasks are removed without replacement; nothing rescheduled |
| **Conflict detection** | Same `start_time` triggers a warning; partial overlap triggers a warning; adjacent tasks (end == start) do not |

### Test run output

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

**Confidence: ★★★★☆ (4/5)** — Core scheduling logic is well-covered. The remaining gap is `generate_plan()`'s end-to-end greedy fit and `is_due_today()` for the weekly 6-day-vs-7-day boundary, which would bring it to 5/5.

---

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->


## Sample output

```
Date: 2026-06-23 | Scheduled: 7 | Skipped: 1 | Time used: 75 min

Scheduled tasks:
  [Pending] Breakfast (feeding)       |  5 min | Priority: HIGH   | Required: True  | daily
  [Pending] Litter Box (grooming)     |  5 min | Priority: HIGH   | Required: True  | daily
  [Pending] Breakfast (feeding)       | 10 min | Priority: HIGH   | Required: True  | daily
  [Pending] Morning Walk (walk)       | 30 min | Priority: HIGH   | Required: True  | daily
  [Pending] Flea Treatment (meds)     |  5 min | Priority: MEDIUM | Required: True  | weekly
  [Pending] Hairball Meds (meds)      |  5 min | Priority: MEDIUM | Required: True  | weekly
  [Pending] Laser Toy (enrichment)    | 15 min | Priority: LOW    | Required: False | daily

Skipped (not enough time remaining):
  [Pending] Fetch / Play (enrichment) | 20 min | Priority: LOW    | Required: False | daily
```
