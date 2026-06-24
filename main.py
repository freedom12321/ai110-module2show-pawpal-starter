from pawpal_system import CareTask, Pet, Owner, Scheduler, Priority

# ── Owner ──────────────────────────────────────────────────────────────────
alex = Owner(name="Alex", available_time=90)  # 90 minutes free today

# ── Pets ───────────────────────────────────────────────────────────────────
buddy = Pet(name="Buddy", species="Dog", breed="Golden Retriever", age=3, energy_level="high")
luna  = Pet(name="Luna",  species="Cat", breed="Siamese",          age=5, energy_level="medium")

# ── Tasks for Buddy ────────────────────────────────────────────────────────
buddy.add_task(CareTask(name="Morning Walk",   duration=30, priority=Priority.HIGH,   category="walk",       required=True,  frequency="daily"))
buddy.add_task(CareTask(name="Breakfast",      duration=10, priority=Priority.HIGH,   category="feeding",    required=True,  frequency="daily"))
buddy.add_task(CareTask(name="Flea Treatment", duration=5,  priority=Priority.MEDIUM, category="medication", required=True,  frequency="weekly"))
buddy.add_task(CareTask(name="Fetch / Play",   duration=20, priority=Priority.LOW,    category="enrichment", required=False, frequency="daily"))

# ── Tasks for Luna ─────────────────────────────────────────────────────────
luna.add_task(CareTask(name="Breakfast",      duration=5,  priority=Priority.HIGH,   category="feeding",    required=True,  frequency="daily"))
luna.add_task(CareTask(name="Litter Box",     duration=5,  priority=Priority.HIGH,   category="grooming",   required=True,  frequency="daily"))
luna.add_task(CareTask(name="Hairball Meds",  duration=5,  priority=Priority.MEDIUM, category="medication", required=True,  frequency="weekly"))
luna.add_task(CareTask(name="Laser Toy",      duration=15, priority=Priority.LOW,    category="enrichment", required=False, frequency="daily"))

# ── Register pets with owner ───────────────────────────────────────────────
alex.add_pet(buddy)
alex.add_pet(luna)

# ── Generate today's plan ──────────────────────────────────────────────────
scheduler = Scheduler(owner=alex)
plan = scheduler.generate_plan(date="2026-06-23")

# ── Print Today's Schedule ─────────────────────────────────────────────────
print("=" * 52)
print("       PawPal+ — Today's Schedule")
print("=" * 52)
print(f"Owner : {alex.name}")
print(f"Pets  : {', '.join(p.name for p in alex.pets)}")
print(f"Budget: {alex.available_time} min available")
print("-" * 52)

print("\nScheduled Tasks:")
for task in plan.scheduled_tasks:
    tag = "[REQUIRED]" if task.required else "[optional]"
    print(f"  {tag:<12} {task.name:<20} {task.duration:>3} min  ({task.category})")

print(f"\n  Total time used: {plan.total_time_used} min / {alex.available_time} min")

if plan.skipped_tasks:
    print("\nSkipped (not enough time):")
    for task in plan.skipped_tasks:
        print(f"  - {task.name} ({task.duration} min)")

print("\n" + "-" * 52)
print(scheduler.explain_plan())
print("=" * 52)
