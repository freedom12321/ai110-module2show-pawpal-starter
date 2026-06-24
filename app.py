import re
import streamlit as st
from datetime import date as _date
from pawpal_system import Owner, Pet, CareTask, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")

# ── Session state vault ────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ── Section 1: Owner + Pet profile ────────────────────────────────────────
st.subheader("1. Owner & Pet Profile")

col1, col2 = st.columns(2)
with col1:
    owner_name     = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Time available today (min)", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["dog", "cat", "other"])
    breed    = st.text_input("Breed", value="Mixed")
    age      = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    energy   = st.selectbox("Energy level", ["low", "medium", "high"], index=1)

if st.button("Save profile"):
    pet   = Pet(name=pet_name, species=species, breed=breed, age=int(age), energy_level=energy)
    owner = Owner(name=owner_name, available_time=int(available_time))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.tasks = []
    st.success(f"Profile saved!  **{owner.name}** → {pet.get_pet_summary()}")

if st.session_state.owner:
    st.caption(f"Active: {st.session_state.owner.pets[0].get_pet_summary()}")

st.divider()

# ── Section 2: Add a Task ──────────────────────────────────────────────────
st.subheader("2. Add a Care Task")

c1, c2, c3 = st.columns(3)
with c1:
    task_title   = st.text_input("Task name", value="Morning walk")
with c2:
    duration     = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with c3:
    priority_str = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])

c4, c5, c6, c7, c8 = st.columns(5)
with c4:
    category       = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
with c5:
    required       = st.checkbox("Required", value=True)
with c6:
    frequency      = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
with c7:
    preferred_time = st.selectbox("Preferred time", ["any", "morning", "afternoon", "evening"])
with c8:
    start_time     = st.text_input("Start time (HH:MM)", value="08:00")

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
            st.session_state.tasks = pet.get_tasks()
            st.success(f"Added: **{task.name}** — {task.duration} min, {task.priority.name} priority")
        except ValueError as e:
            st.error(str(e))

# ── Task list with filter + sort ───────────────────────────────────────────
if st.session_state.tasks:
    st.markdown("**Current tasks**")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_filter = st.selectbox("Filter by status", ["all", "pending", "completed"], key="status_filter")
    with fc2:
        pet_options = ["all"] + (
            [p.name for p in st.session_state.owner.pets] if st.session_state.owner else []
        )
        pet_filter = st.selectbox("Filter by pet", pet_options, key="pet_filter")
    with fc3:
        sort_order = st.selectbox("Sort by", ["priority", "start time"], key="sort_order")

    _sched = Scheduler(owner=st.session_state.owner)

    filtered = _sched.filter_tasks(
        st.session_state.tasks,
        status=None if status_filter == "all" else status_filter,
        pet_name=None if pet_filter == "all" else pet_filter,
    )
    display_tasks = (
        _sched.sort_by_time(filtered)
        if sort_order == "start time"
        else _sched.sort_tasks(filtered)
    )

    if display_tasks:
        st.dataframe(
            [
                {
                    "Task":          t.name,
                    "Start":         t.start_time,
                    "Duration (min)":t.duration,
                    "Priority":      t.priority.name,
                    "Category":      t.category,
                    "Freq.":         t.frequency,
                    "Time slot":     t.preferred_time,
                    "Required":      t.required,
                    "Done":          t.completed,
                    "Next due":      t.next_due_date or "—",
                }
                for t in display_tasks
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Required": st.column_config.CheckboxColumn("Required"),
                "Done":     st.column_config.CheckboxColumn("Done"),
            },
        )
    else:
        st.info("No tasks match the current filters.")
else:
    st.info("No tasks yet — add one above.")

# ── Mark a Task Complete ───────────────────────────────────────────────────
if st.session_state.tasks:
    st.subheader("Mark a Task Complete")
    pending = [t for t in st.session_state.tasks if not t.completed]
    if not pending:
        st.info("All tasks are already done for today. 🎉")
    else:
        mc1, mc2 = st.columns([4, 1])
        with mc1:
            task_to_complete = st.selectbox("Select task", [t.name for t in pending], key="task_to_complete")
        with mc2:
            st.write("")
            mark_btn = st.button("Mark done")

        if mark_btn:
            today_str = _date.today().isoformat()
            pet       = st.session_state.owner.pets[0]
            target    = next(t for t in pet.tasks if t.name == task_to_complete)
            saved_freq = target.frequency
            target.mark_complete(today_str)

            scheduler   = Scheduler(owner=st.session_state.owner)
            rescheduled = scheduler.reschedule_completed_tasks(pet, today_str)
            st.session_state.tasks = pet.get_tasks()

            if saved_freq == "as-needed":
                st.success(f"'{task_to_complete}' done and removed (as-needed — no next occurrence).")
            elif rescheduled:
                r = rescheduled[0]
                st.success(f"'{task_to_complete}' done!  Next {r.frequency} occurrence → **{r.next_due_date}**")

st.divider()

# ── Section 3: Generate Schedule ──────────────────────────────────────────
st.subheader("3. Build Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet profile first.")
    elif not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        plan      = scheduler.generate_plan(date="today")

        # ── Summary metrics ────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Date",      plan.date)
        m2.metric("Scheduled", len(plan.scheduled_tasks))
        m3.metric("Skipped",   len(plan.skipped_tasks))
        time_left = st.session_state.owner.available_time - plan.total_time_used
        m4.metric("Time used", f"{plan.total_time_used} min",
                  delta=f"{time_left} min left",
                  delta_color="normal" if time_left >= 0 else "inverse")

        # ── Budget warning (required tasks exceed available time) ──────────
        budget_warnings   = [w for w in plan.warnings if "Required tasks need" in w]
        conflict_warnings = [w for w in plan.warnings if "CONFLICT" in w]

        for w in budget_warnings:
            st.warning(f"**Time budget tight.** {w}\n\n"
                       "💡 _Consider adding more available time or removing a lower-priority required task._")

        # ── Conflict warnings — actionable callouts for each overlap ───────
        if conflict_warnings:
            st.markdown("---")
            st.markdown("### ⚠️ Scheduling Conflicts")
            st.caption(
                "The tasks below have overlapping time windows. "
                "Your pet can't receive both at once — adjust a start time to fix each conflict."
            )
            for w in conflict_warnings:
                # Parse:  "CONFLICT: [PetA] 'Task A' HH:MM–HH:MM  overlaps  [PetB] 'Task B' HH:MM–HH:MM"
                names = re.findall(r"'([^']+)'", w)
                times = re.findall(r"\d{2}:\d{2}–\d{2}:\d{2}", w)
                if len(names) == 2 and len(times) == 2:
                    st.warning(
                        f"**{names[0]}** ({times[0]})  overlaps  **{names[1]}** ({times[1]})\n\n"
                        f"💡 Move one of these tasks to a different start time so they don't overlap."
                    )
                else:
                    st.warning(w)   # fallback: show raw string if parsing fails
            st.markdown("---")

        # ── Scheduled tasks table ──────────────────────────────────────────
        if plan.scheduled_tasks:
            st.markdown("#### ✅ Scheduled tasks")
            st.dataframe(
                [
                    {
                        "Task":          t.name,
                        "Start":         t.start_time,
                        "Duration (min)":t.duration,
                        "Priority":      t.priority.name,
                        "Category":      t.category,
                        "Freq.":         t.frequency,
                        "Required":      t.required,
                    }
                    for t in plan.scheduled_tasks
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Required": st.column_config.CheckboxColumn("Required"),
                },
            )
        else:
            st.info("No tasks could be scheduled today.")

        # ── Skipped tasks table ────────────────────────────────────────────
        if plan.skipped_tasks:
            st.markdown("#### ⏭️ Skipped tasks")
            st.caption("These tasks didn't fit in today's time budget. Consider doing them tomorrow or freeing up time.")
            st.dataframe(
                [
                    {
                        "Task":          t.name,
                        "Duration (min)":t.duration,
                        "Priority":      t.priority.name,
                        "Category":      t.category,
                        "Required":      t.required,
                    }
                    for t in plan.skipped_tasks
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Required": st.column_config.CheckboxColumn("Required"),
                },
            )

        # ── Plain-English explanation ──────────────────────────────────────
        with st.expander("Why did the scheduler choose this order?"):
            st.text(scheduler.explain_plan())
