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
    preferred_time = st.text_input("Preferred time (optional, e.g. 08:00)")
    submitted_task = st.form_submit_button("Add task")
    if submitted_task and task_title.strip():
        selected_pet.add_task(
            Task(
                name=task_title.strip(),
                duration=int(duration),
                priority=priority,
                preferred_time=preferred_time.strip(),
            )
        )
        st.success(f"Added '{task_title.strip()}' for {selected_pet.name}!")
        st.rerun()

# --- Current tasks --------------------------------------------------------
st.markdown("#### Current tasks")
all_tasks = owner.all_tasks()
if all_tasks:
    st.table(
        [
            {
                "Task": task.name,
                "Duration (min)": task.duration,
                "Priority": task.priority,
                "Preferred time": task.preferred_time or "—",
                "Done": "✅" if task.completed else "",
            }
            for task in all_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Build the schedule ---------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner.available_minutes)
    plan = scheduler.generate_plan(owner.all_tasks())

    if not plan:
        st.warning("Nothing could be scheduled. Add tasks or increase available time.")
    else:
        for i, task in enumerate(plan, start=1):
            time = task.preferred_time or "—"
            st.write(f"**{i}. {task.name}** · {task.duration} min · {task.priority} · {time}")

    if scheduler.last_skipped:
        st.markdown("**Skipped (not enough time):**")
        for task in scheduler.last_skipped:
            st.write(f"- {task.name} ({task.duration} min, {task.priority})")

    with st.expander("Why this plan?"):
        st.text(scheduler.explain())
