import streamlit as st
from datetime import date as _date
from pawpal_system import Owner, Pet, CareTask, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state vault ────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None       # set when owner form is submitted

if "tasks" not in st.session_state:
    st.session_state.tasks = []         # list of CareTask instances

# ── Section 1: Owner + Pet profile ────────────────────────────────────────
st.subheader("1. Owner & Pet Profile")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Time available today (min)", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Mixed")
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    energy = st.selectbox("Energy level", ["low", "medium", "high"], index=1)

if st.button("Save profile"):
    pet = Pet(name=pet_name, species=species, breed=breed, age=age, energy_level=energy)
    owner = Owner(name=owner_name, available_time=int(available_time))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.tasks = []         # reset tasks when profile changes
    st.success(f"Profile saved! {owner.name} → {pet.get_pet_summary()}")

if st.session_state.owner:
    st.caption(f"Active pet: {st.session_state.owner.pets[0].get_pet_summary()}")

st.divider()

# ── Section 2: Add a Task ──────────────────────────────────────────────────
st.subheader("2. Add a Care Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task name", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"], index=0)

col4, col5, col6, col7, col8 = st.columns(5)
with col4:
    category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
with col5:
    required = st.checkbox("Required", value=True)
with col6:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
with col7:
    preferred_time = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])
with col8:
    start_time = st.text_input("Start time (HH:MM)", value="08:00")

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet profile first.")
    else:
        task = CareTask(
            name=task_title,
            duration=int(duration),
            priority=Priority[priority_str],
            category=category,
            required=required,
            frequency=frequency,
            preferred_time=preferred_time,
            start_time=start_time,
        )
        pet = st.session_state.owner.pets[0]
        try:
            pet.add_task(task)
            st.session_state.tasks = pet.get_tasks()   # keep session list in sync
            st.success(f"Added: {task.get_task_summary()}")
        except ValueError as e:
            st.error(str(e))

if st.session_state.tasks:
    st.write("Current tasks:")

    # ── Filter & sort controls ────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_filter = st.selectbox(
            "Filter by status", ["all", "pending", "completed"], key="status_filter"
        )
    with fc2:
        pet_options = ["all"]
        if st.session_state.owner:
            pet_options += [p.name for p in st.session_state.owner.pets]
        pet_filter = st.selectbox("Filter by pet", pet_options, key="pet_filter")
    with fc3:
        sort_order = st.selectbox(
            "Sort by", ["priority", "start time"], key="sort_order"
        )

    _sched = Scheduler(owner=st.session_state.owner)

    # Filter first, then sort the filtered result
    filtered_tasks = _sched.filter_tasks(
        st.session_state.tasks,
        status=None if status_filter == "all" else status_filter,
        pet_name=None if pet_filter == "all" else pet_filter,
    )
    display_tasks = (
        _sched.sort_by_time(filtered_tasks)
        if sort_order == "start time"
        else _sched.sort_tasks(filtered_tasks)
    )

    if display_tasks:
        st.table([
            {
                "Task": t.name,
                "Start": t.start_time,
                "Duration (min)": t.duration,
                "Priority": t.priority.name,
                "Category": t.category,
                "Frequency": t.frequency,
                "Next Due": t.next_due_date or "—",
                "Time slot": t.preferred_time,
                "Required": t.required,
                "Done": t.completed,
            }
            for t in display_tasks
        ])
    else:
        st.info("No tasks match the current filters.")
else:
    st.info("No tasks yet. Add one above.")

# ── Section 2b: Mark a Task Complete ──────────────────────────────────────
if st.session_state.tasks:
    st.subheader("Mark a Task Complete")

    pending = [t for t in st.session_state.tasks if not t.completed]
    if not pending:
        st.info("All tasks are already done for today.")
    else:
        mc1, mc2 = st.columns([4, 1])
        with mc1:
            task_to_complete = st.selectbox(
                "Select task", [t.name for t in pending], key="task_to_complete"
            )
        with mc2:
            st.write("")   # vertical alignment spacer
            mark_btn = st.button("Mark done")

        if mark_btn:
            today_str = _date.today().isoformat()
            pet = st.session_state.owner.pets[0]

            # Locate the task object, save its frequency before it is removed
            target = next(t for t in pet.tasks if t.name == task_to_complete)
            saved_frequency = target.frequency

            # 1. Mark complete (records the date for recurrence tracking)
            target.mark_complete(today_str)

            # 2. Reschedule — uses timedelta internally to compute next due date
            scheduler = Scheduler(owner=st.session_state.owner)
            rescheduled = scheduler.reschedule_completed_tasks(pet, today_str)

            # 3. Sync session state with the updated pet task list
            st.session_state.tasks = pet.get_tasks()

            if saved_frequency == "as-needed":
                st.success(f"'{task_to_complete}' done and removed (as-needed — no next occurrence).")
            elif rescheduled:
                r = rescheduled[0]
                st.success(
                    f"'{task_to_complete}' done!  "
                    f"Next {r.frequency} occurrence → {r.next_due_date}"
                )

st.divider()

# ── Section 3: Generate Schedule ──────────────────────────────────────────
st.subheader("3. Build Today's Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet profile first.")
    elif not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        plan = scheduler.generate_plan(date="today")

        # Surface any conflict warnings before the summary
        for w in plan.warnings:
            st.error(w)

        st.success(plan.get_summary())

        if plan.scheduled_tasks:
            st.markdown("**Scheduled tasks:**")
            st.table([
                {
                    "Task": t.name,
                    "Duration (min)": t.duration,
                    "Priority": t.priority.name,
                    "Category": t.category,
                    "Frequency": t.frequency,
                    "Time slot": t.preferred_time,
                    "Required": t.required,
                }
                for t in plan.scheduled_tasks
            ])

        if plan.skipped_tasks:
            st.warning("Skipped (not enough time):")
            for t in plan.skipped_tasks:
                st.write(f"  - {t.name} ({t.duration} min)")

        with st.expander("Full explanation"):
            st.text(scheduler.explain_plan())
