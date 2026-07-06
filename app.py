import streamlit as st

# Step 1: bring the backend classes into the Streamlit app.
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care based on time and priority.")

# Step 2: persist the Owner across reruns.
# Streamlit reruns the whole script on every interaction, so we keep the
# Owner object in st.session_state and only create it once per session.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)

owner = st.session_state.owner

st.divider()

# --- Owner settings -------------------------------------------------------
st.subheader("Owner")
col_a, col_b = st.columns(2)
with col_a:
    owner.name = st.text_input("Owner name", value=owner.name)
with col_b:
    owner.available_minutes = st.number_input(
        "Time available today (minutes)", min_value=1, max_value=600,
        value=owner.available_minutes,
    )

# One scheduler instance drives sorting, filtering, conflicts, and planning.
scheduler = Scheduler(owner.available_minutes)

st.divider()

# --- Add a pet ------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed (optional)")
    submitted_pet = st.form_submit_button("Add pet")
    if submitted_pet and pet_name.strip():
        # The Owner class method handles the new pet...
        owner.add_pet(Pet(name=pet_name.strip(), species=species, breed=breed.strip()))
        # ...and rerun so the UI reflects the updated pet list.
        st.success(f"Added {pet_name.strip()}!")
        st.rerun()

if not owner.pets:
    st.info("No pets yet. Add one above to get started.")
    st.stop()

# --- Add a task to a pet --------------------------------------------------
st.subheader("Add a Task")
pet_names = [pet.name for pet in owner.pets]
selected_index = pet_names.index(
    st.selectbox("For which pet?", pet_names)
)
selected_pet = owner.pets[selected_index]

with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    col4, col5 = st.columns(2)
    with col4:
        preferred_time = st.text_input("Preferred time (optional, e.g. 08:00)")
    with col5:
        repeat = st.selectbox("Repeat", ["none", "daily", "weekly"])
    submitted_task = st.form_submit_button("Add task")
    if submitted_task and task_title.strip():
        selected_pet.add_task(
            Task(
                name=task_title.strip(),
                duration=int(duration),
                priority=priority,
                preferred_time=preferred_time.strip(),
                recurrence="" if repeat == "none" else repeat,
            )
        )
        st.success(f"Added '{task_title.strip()}' for {selected_pet.name}!")
        st.rerun()

# --- Current tasks: filter + sort + conflict warnings ---------------------
st.markdown("#### Current tasks")
all_tasks = owner.all_tasks()

if not all_tasks:
    st.info("No tasks yet. Add one above.")
else:
    # Filter/sort controls -> driven by Scheduler.filter_tasks / sort_by_time.
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + pet_names)
    with fcol2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    with fcol3:
        sort_choice = st.selectbox("Sort by", ["Time", "Entry order"])

    status_map = {"All": None, "Pending": False, "Completed": True}
    view = scheduler.filter_tasks(
        all_tasks,
        completed=status_map[status_filter],
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )
    if sort_choice == "Time":
        view = scheduler.sort_by_time(view)

    if view:
        st.table(
            [
                {
                    "Pet": task.pet_name,
                    "Task": task.name,
                    "Time": task.preferred_time or "—",
                    "Duration (min)": task.duration,
                    "Priority": task.priority,
                    "Repeats": task.recurrence or "—",
                    "Done": "✅" if task.completed else "",
                }
                for task in view
            ]
        )
    else:
        st.info("No tasks match the current filters.")

    # Conflict detection across ALL tasks (not just the filtered view).
    conflicts = scheduler.detect_conflicts(all_tasks)
    if conflicts:
        st.warning(
            "**⚠️ Scheduling conflict — two tasks share a time slot:**\n\n"
            + "\n".join(f"- {warning}" for warning in conflicts)
            + "\n\nConsider moving one of them to a different time."
        )
    else:
        st.success("No scheduling conflicts — every task time is clear. ✅")

    # --- Mark a task done (recurring tasks auto-roll to the next date) ----
    st.markdown("#### Mark a task done")
    pending = [task for task in all_tasks if not task.completed]
    if not pending:
        st.caption("All tasks are done. 🎉")
    else:
        labels = [
            f"{i + 1}. {task.pet_name}: {task.name}"
            + (f" ({task.preferred_time})" if task.preferred_time else "")
            for i, task in enumerate(pending)
        ]
        chosen = st.selectbox("Which task did you finish?", labels)
        if st.button("Mark done"):
            done_task = pending[labels.index(chosen)]
            pet = next(p for p in owner.pets if p.name == done_task.pet_name)
            spawned = pet.complete_task(done_task)
            if spawned is not None:
                st.success(
                    f"Nice — '{done_task.name}' done! Since it repeats "
                    f"{spawned.recurrence}, the next one is scheduled for "
                    f"{spawned.due_date}."
                )
            else:
                st.success(f"Nice — '{done_task.name}' marked done!")
            st.rerun()

st.divider()

# --- Build the schedule ---------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    plan = scheduler.generate_plan(owner.all_tasks())

    if not plan:
        st.warning("Nothing could be scheduled. Add tasks or increase available time.")
    else:
        used = sum(task.duration for task in plan)
        st.success(
            f"Scheduled {len(plan)} task(s) using {used} of "
            f"{owner.available_minutes} min."
        )
        st.table(
            [
                {
                    "#": i,
                    "Time": task.preferred_time or "—",
                    "Pet": task.pet_name,
                    "Task": task.name,
                    "Duration (min)": task.duration,
                    "Priority": task.priority,
                }
                for i, task in enumerate(plan, start=1)
            ]
        )

    if scheduler.last_skipped:
        st.markdown("**Skipped (not enough time):**")
        for task in scheduler.last_skipped:
            st.write(f"- {task.name} ({task.duration} min, {task.priority})")

    with st.expander("Why this plan?"):
        st.text(scheduler.explain())
