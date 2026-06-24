from datetime import date, timedelta
from pawpal_system import CareTask, Pet, Owner, Scheduler, Priority

# ── timedelta crash-course (printed so you can see the values) ────────────
TODAY      = date(2026, 6, 23)
TOMORROW   = TODAY + timedelta(days=1)     # daily  → +1 day
NEXT_WEEK  = TODAY + timedelta(weeks=1)    # weekly → +7 days

print("timedelta examples")
print(f"  today      = {TODAY}")
print(f"  + 1 day    = {TOMORROW}   ← timedelta(days=1)")
print(f"  + 1 week   = {NEXT_WEEK}  ← timedelta(weeks=1)")

# ── Helpers ────────────────────────────────────────────────────────────────
SEP = "-" * 66

def print_tasks(label: str, tasks: list) -> None:
    print(f"\n{label}")
    print(SEP)
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        done = "done" if t.completed else "    "
        due  = f"next→{t.next_due_date}" if t.next_due_date else "          "
        print(
            f"  [{done}]  {t.start_time}  {t.name:<22}"
            f"  {t.duration:>3} min  {t.frequency:<9}  {due}"
        )

# ── Owner & pets ───────────────────────────────────────────────────────────
alex  = Owner(name="Alex", available_time=90)
buddy = Pet(name="Buddy", species="Dog", breed="Golden Retriever", age=3, energy_level="high")
luna  = Pet(name="Luna",  species="Cat", breed="Siamese",          age=5, energy_level="medium")

# Tasks added OUT OF ORDER by start_time on purpose
buddy.add_task(CareTask("Evening Walk",   duration=30, priority=Priority.HIGH,   category="walk",       required=True,  frequency="daily",     start_time="18:00"))
buddy.add_task(CareTask("Breakfast",      duration=10, priority=Priority.HIGH,   category="feeding",    required=True,  frequency="daily",     start_time="07:30"))
buddy.add_task(CareTask("Flea Treatment", duration=5,  priority=Priority.MEDIUM, category="medication", required=True,  frequency="weekly",    start_time="10:00"))
buddy.add_task(CareTask("Fetch / Play",   duration=20, priority=Priority.LOW,    category="enrichment", required=False, frequency="daily",     start_time="15:30"))
buddy.add_task(CareTask("Vet Checkup",    duration=60, priority=Priority.HIGH,   category="medication", required=True,  frequency="as-needed", start_time="09:00"))

luna.add_task(CareTask("Laser Toy",       duration=15, priority=Priority.LOW,    category="enrichment", required=False, frequency="daily",     start_time="20:00"))
luna.add_task(CareTask("Litter Box",      duration=5,  priority=Priority.HIGH,   category="grooming",   required=True,  frequency="daily",     start_time="09:00"))
luna.add_task(CareTask("Hairball Meds",   duration=5,  priority=Priority.MEDIUM, category="medication", required=True,  frequency="weekly",    start_time="11:00"))
luna.add_task(CareTask("Breakfast",       duration=5,  priority=Priority.HIGH,   category="feeding",    required=True,  frequency="daily",     start_time="07:45"))

alex.add_pet(buddy)
alex.add_pet(luna)

scheduler = Scheduler(owner=alex)

# ── BEFORE: all tasks as added ─────────────────────────────────────────────
print("\n" + "=" * 66)
print("  BEFORE — tasks as added (no sort, nothing completed yet)")
print("=" * 66)

all_tasks = alex.get_all_tasks(exclude_completed=False)
print_tasks("Buddy", buddy.tasks)
print_tasks("Luna",  luna.tasks)

# ── Sort demos ────────────────────────────────────────────────────────────
print("\n" + "=" * 66)
print("  SORTING DEMO")
print("=" * 66)
print_tasks("All tasks — sorted by START TIME  (sort_by_time)",
            scheduler.sort_by_time(all_tasks))
print_tasks("All tasks — sorted by PRIORITY   (sort_tasks)",
            scheduler.sort_tasks(all_tasks))

# ── Mark tasks complete ────────────────────────────────────────────────────
TODAY_STR = str(TODAY)   # "2026-06-23"

buddy.tasks[1].mark_complete(TODAY_STR)   # Breakfast    (daily)
buddy.tasks[2].mark_complete(TODAY_STR)   # Flea Treat   (weekly)
buddy.tasks[4].mark_complete(TODAY_STR)   # Vet Checkup  (as-needed)
luna.tasks[2].mark_complete(TODAY_STR)    # Hairball Meds (weekly)

print("\n" + "=" * 66)
print("  AFTER mark_complete() — before rescheduling")
print("=" * 66)
all_tasks = alex.get_all_tasks(exclude_completed=False)
print_tasks("All tasks (completed ones visible)", all_tasks)

# ── Filter demo ────────────────────────────────────────────────────────────
print("\n" + "=" * 66)
print("  FILTER DEMO")
print("=" * 66)
print_tasks("Pending only  →  filter_tasks(status='pending')",
            scheduler.filter_tasks(all_tasks, status="pending"))
print_tasks("Completed only  →  filter_tasks(status='completed')",
            scheduler.filter_tasks(all_tasks, status="completed"))
print_tasks("Buddy only  →  filter_tasks(pet_name='Buddy')",
            scheduler.filter_tasks(all_tasks, pet_name="Buddy"))

# ── Reschedule completed tasks ─────────────────────────────────────────────
print("\n" + "=" * 66)
print("  RESCHEDULING — reschedule_completed_tasks()")
print("=" * 66)
print(f"\n  Rescheduling Buddy's completed tasks from {TODAY_STR} …")
buddy_new = scheduler.reschedule_completed_tasks(buddy, TODAY_STR)
for t in buddy_new:
    print(f"    {t.name:<22}  ({t.frequency})  →  next_due_date = {t.next_due_date}")

print(f"\n  Rescheduling Luna's completed tasks from {TODAY_STR} …")
luna_new = scheduler.reschedule_completed_tasks(luna, TODAY_STR)
for t in luna_new:
    print(f"    {t.name:<22}  ({t.frequency})  →  next_due_date = {t.next_due_date}")

print_tasks("\nAll tasks AFTER rescheduling (next_due_date column shows new dates)",
            alex.get_all_tasks(exclude_completed=False))

# ── Generate tomorrow's plan ───────────────────────────────────────────────
TOMORROW_STR = str(TOMORROW)
print("\n" + "=" * 66)
print(f"  TOMORROW'S PLAN  ({TOMORROW_STR})")
print("=" * 66)

plan = scheduler.generate_plan(date=TOMORROW_STR)

if plan.warnings:
    print("\nWarnings:")
    for w in plan.warnings:
        print(f"  ! {w}")

print(f"\n{plan.get_summary()}")
print("\nScheduled:")
for t in plan.scheduled_tasks:
    tag = "[REQUIRED]" if t.required else "[optional]"
    print(f"  {tag:<12}  {t.start_time}  {t.name:<22}  {t.duration:>3} min")

if plan.skipped_tasks:
    print("\nSkipped (not enough time):")
    for t in plan.skipped_tasks:
        print(f"  - {t.name} ({t.duration} min)")

print("=" * 66)

# ══════════════════════════════════════════════════════════════════
#  CONFLICT DETECTION DEMO
#  Fresh owner "Sam" with deliberately overlapping tasks so the
#  output is clean and independent of the rescheduling demo above.
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 66)
print("  CONFLICT DETECTION DEMO")
print("=" * 66)

sam   = Owner(name="Sam", available_time=180)
rex   = Pet(name="Rex",   species="Dog", breed="Labrador", age=2, energy_level="high")
mochi = Pet(name="Mochi", species="Cat", breed="Mixed",    age=4, energy_level="low")

# ── Scenario 1: same pet, overlapping tasks ───────────────────────────────
# Rex: Morning Walk  07:00–07:30  (30 min)
# Rex: Breakfast     07:15–07:25  (10 min)  ← starts inside Morning Walk
rex.add_task(CareTask("Morning Walk", duration=30, priority=Priority.HIGH,
                      category="walk",    required=True,  frequency="daily", start_time="07:00"))
rex.add_task(CareTask("Breakfast",    duration=10, priority=Priority.HIGH,
                      category="feeding", required=True,  frequency="daily", start_time="07:15"))

# ── Scenario 2: different pets, overlapping tasks ─────────────────────────
# Rex:   Grooming    09:00–09:20  (20 min)
# Mochi: Litter Box  09:10–09:25  (15 min)  ← straddles end of Grooming
rex.add_task(CareTask("Grooming",   duration=20, priority=Priority.MEDIUM,
                      category="grooming",   required=True, frequency="daily", start_time="09:00"))
mochi.add_task(CareTask("Litter Box", duration=15, priority=Priority.HIGH,
                        category="grooming", required=True, frequency="daily", start_time="09:10"))

# ── Non-conflicting tasks (should produce no warnings) ────────────────────
# Rex:   Evening Walk  18:00–18:30  (30 min)
# Mochi: Dinner        18:45–18:50  (5 min)  ← gap between them, no overlap
rex.add_task(CareTask("Evening Walk", duration=30, priority=Priority.HIGH,
                      category="walk",    required=True, frequency="daily", start_time="18:00"))
mochi.add_task(CareTask("Dinner",     duration=5,  priority=Priority.HIGH,
                        category="feeding", required=True, frequency="daily", start_time="18:45"))

sam.add_pet(rex)
sam.add_pet(mochi)

conflict_scheduler = Scheduler(owner=sam)
all_conflict_tasks = sam.get_all_tasks(exclude_completed=False)

# Print the task schedule so the overlaps are visible
print("\nTask schedule (time-ordered):")
print(f"  {'Task':<20}  {'Pet':<6}  {'Window':<14}  Freq")
print("  " + "-" * 52)
task_to_pet_name = {
    id(task): pet.name
    for pet in sam.pets
    for task in pet.tasks
}
for t in conflict_scheduler.sort_by_time(all_conflict_tasks):
    from pawpal_system import _hhmm_to_minutes, _minutes_to_hhmm
    end = _minutes_to_hhmm(_hhmm_to_minutes(t.start_time) + t.duration)
    pet_label = task_to_pet_name.get(id(t), "?")
    print(f"  {t.name:<20}  {pet_label:<6}  {t.start_time}–{end:<8}  {t.frequency}")

# ── Call detect_conflicts() directly ─────────────────────────────────────
print("\nRunning detect_conflicts() on all tasks …")
warnings = conflict_scheduler.detect_conflicts(all_conflict_tasks)

if warnings:
    print(f"\n  {len(warnings)} conflict(s) found:")
    for w in warnings:
        print(f"  ! {w}")
else:
    print("  No conflicts found.")

# ── generate_plan() picks them up automatically ───────────────────────────
print("\nGenerating plan — conflicts should also appear in plan.warnings …")
conflict_plan = conflict_scheduler.generate_plan(date="2026-06-23")

if conflict_plan.warnings:
    print(f"\n  plan.warnings ({len(conflict_plan.warnings)} total):")
    for w in conflict_plan.warnings:
        print(f"  ! {w}")
else:
    print("  plan.warnings is empty.")

print("=" * 66)
