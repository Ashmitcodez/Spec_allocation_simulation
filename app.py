import streamlit as st
import pandas as pd

from allocation import generate_random_students, allocation_steps
from data_utils import load_student_csv

st.set_page_config(
    page_title="Spec Allocation Simulator",
    layout="wide"
)

st.title("UoA Engineering Specialisation Allocation Simulator")

st.markdown(
    """
This app simulates GPA based allocation of students into engineering specialisations.
You can set capacities, generate synthetic students or upload your own CSV,
then watch the allocation unfold step by step or jump straight to the final result. 
You can also add a bias to which specialisations are more popular in the generated preference lists.
"""
)

# Step 1: Spec Popularity and Seats
# The UI below collects the list of specs, how popular they are according to the user, and the seat capacity for each.

st.header("Step 1: Set Specialisation Popularity and Seats")

default_specs = [
    "Biomedical",
    "Chemical and Materials",
    "Civil and Environmental",
    "Computer Systems",
    "Electrical and Electronic",
    "Engineering Science",
    "Mechanical",
    "Mechatronics",
    "Software",
    "Structural",
]

# default capacities per specialisation according to the specialisation website (can be adjusted in the UI)
spec_default_seats = {
    "Biomedical": 35,
    "Chemical and Materials": 80,
    "Civil and Environmental": 210,
    "Computer Systems": 100,
    "Electrical and Electronic": 100,
    "Engineering Science": 80,
    "Mechanical": 125,
    "Mechatronics": 105,
    "Software": 125,
    "Structural": 80,
}

with st.expander("Configure capacities", expanded=True):
    spec_capacity = {}
    for spec in default_specs:
        # each specialisation gets a numeric input that sets its seat capacity
        # default value is taken from spec_default_seats if present
        seats = st.number_input(
            f"Seats for {spec}",
            min_value=0,
            max_value=500,
            value=spec_default_seats.get(spec, 50),
            step=1
        )
        spec_capacity[spec] = seats

spec_list = list(spec_capacity.keys())

# Optional: allow the user to indicate popularity weights for each specialisation
with st.expander("Optional: preference popularity weights (make some specs more popular)", expanded=False):
    st.write("Set higher weights for specs you want to be more popular in generated preference lists.")
    # brief two-line helper to explain uniform vs weighted sampling
    st.markdown(
        "**Quick note:** Preferences are sampled per student without replacement.\n"
        "By default every spec is equally likely (uniform = weight 1)."
    )
    # concise example to show the practical effect
    st.markdown(
        "**Example:** if `Mechanical` has weight 5 and `Software` has weight 1,"
        " `Mechanical` will appear as a top preference roughly 5× more often than `Software`."
    )
    pref_weights = {}
    for spec in spec_list:
        w = st.number_input(
            f"Weight for {spec}",
            min_value=0.0,
            max_value=1000.0,
            value=1.0,
            step=0.1,
            format="%.1f",
            help="Higher = more likely to appear in student preferences"
        )
        pref_weights[spec] = float(w)
    # make available to other code paths
    st.session_state["pref_weights"] = pref_weights



# Step 2: Load the Student Data
# Provide two options: generate synthetic students or upload a CSV file.

st.header("Step 2: Choose student data source")

data_option = st.radio(
    "Data source",
    ["Generate synthetic students", "Upload CSV file"],
    horizontal=True
)

df_students = None

if data_option == "Generate synthetic students":
    col_left, col_right = st.columns(2)

    with col_left:
        n_students = st.number_input(
            "Number of students",
            min_value=5,
            max_value=5000,
            value=1000,
            step=5
        )

    with col_right:
        seed_val = st.number_input(
            "Random seed (optional, for reproducibility)",
            min_value=0,
            max_value=10_000,
            value=42,
            step=1
        )
        # allow the user to control the GPA generation range (defaults kept for compatibility)
        gpa_min = st.number_input(
            "GPA minimum for synthetic data",
            min_value=0.0,
            max_value=9.0,
            value=0.75,
            step=0.01,
            format="%.2f"
        )
        gpa_max = st.number_input(
            "GPA maximum for synthetic data",
            min_value=0.0,
            max_value=9.0,
            value=9.0,
            step=0.01,
            format="%.2f"
        )
        # normal distribution parameters for GPA sampling
        st.markdown("**Normal distribution parameters for GPA sampling**")
        gpa_mean = st.number_input(
            "GPA mean",
            min_value=0.0,
            max_value=9.0,
            value=6.0,
            step=0.01,
            format="%.2f"
        )
        gpa_std = st.number_input(
            "GPA standard deviation",
            min_value=0.01,
            max_value=9.0,
            value=1.25,
            step=0.01,
            format="%.2f"
        )
        st.caption("GPAs are sampled from a normal distribution with the mean and standard deviation above, then snapped to the discrete 1/63 GPA grid.")
        # sampling mode: bootstrapping (with replacement) or without replacement
        sampling_with_replacement = st.checkbox(
            "Sample GPAs with replacement (bootstrapping)", value=True
        )
    # generate button is placed after the two input columns so it remains visible
    if st.button("Generate synthetic dataset"):
        # call helper to synthesize a DataFrame of students ordered by GPA
        df_students = generate_random_students(
            n_students,
            specs=spec_list,
            n_prefs=5,
            seed=seed_val,
            gpa_min=gpa_min,
            gpa_max=gpa_max,
            mean=gpa_mean,
            std=gpa_std,
            sampling_with_replacement=sampling_with_replacement,
            pref_weights=st.session_state.get("pref_weights", None),
        )
        # persist in session state so the dataset survives re-renders
        st.session_state["df_students"] = df_students
        st.success("Synthetic data generated.")
        # display a rounded view (2 decimal places) in the UI
        df_display = df_students.copy()
        df_display["gpa"] = df_display["gpa"].round(2)
        st.dataframe(df_display.head(20))

else:
    uploaded = st.file_uploader(
        "Upload CSV with columns id, gpa, pref1, pref2, pref3, pref4, pref5",
        type=["csv"]
    )
    if uploaded is not None:
        try:
            # parse the uploaded CSV and validate required columns
            df_students = load_student_csv(uploaded)
            st.session_state["df_students"] = df_students
            st.success("CSV loaded successfully.")
            # display GPA rounded to 2 dp for readability
            df_display = df_students.copy()
            df_display["gpa"] = df_display["gpa"].round(2)
            st.dataframe(df_display.head(20))
        except Exception as e:
            st.error(f"Error loading CSV: {e}")

# keep data if already in session (survive across interactions)
if df_students is None and "df_students" in st.session_state:
    df_students = st.session_state["df_students"]


# Step 3: run spec allocation
# When the user clicks run, call `allocation_steps` to compute per-student snapshots

if df_students is not None:
    st.header("Step 3: Run allocation")

    col_run, col_opts = st.columns([1, 2])

    with col_run:
        run_clicked = st.button("Run simulator")

    with col_opts:
        random_fallback = st.checkbox(
            "Allow random allocation if all five preferences are full",
            value=True
        )
        seed_alloc = st.number_input(
            "Random seed for allocation fallback",
            min_value=0,
            max_value=10_000,
            value=123,
            step=1
        )

    if run_clicked:
        # produce a list of snapshots; each snapshot records the state after one student
        snapshots = allocation_steps(
            df_students,
            capacity_dict=spec_capacity,
            max_prefs=5,
            random_fallback=random_fallback,
            seed=seed_alloc
        )
        # persist results and reset the step pointer
        st.session_state["snapshots"] = snapshots
        st.session_state["current_step"] = 1
        st.session_state["current_step_val"] = 1
        st.success("Simulation completed.")


# Step 4: Visualise allocation

if "snapshots" in st.session_state:
    st.header("Step 4: Visualise allocation")

    snapshots = st.session_state["snapshots"]
    total_steps = len(snapshots)

    # ensure we always have a valid current step in session state
    if "current_step" not in st.session_state:
        st.session_state["current_step"] = 1

    col_slider, col_buttons = st.columns([3, 1])

    with col_slider:
        # initialize canonical program state if needed
        if "current_step_val" not in st.session_state:
            st.session_state["current_step_val"] = 1

        # slider lets user move through the per-student snapshots; use the
        # canonical `current_step_val` as the slider default. We capture the
        # returned value and write it back into session state when it changes.
        slider_val = st.slider(
            "Step",
            min_value=1,
            max_value=total_steps,
            value=st.session_state["current_step_val"],
        )

        if slider_val != st.session_state["current_step_val"]:
            st.session_state["current_step_val"] = slider_val

    with col_buttons:
        # show current step / total
        st.write(f"Step {st.session_state['current_step_val']} / {total_steps}")

        prev_disabled = st.session_state["current_step_val"] <= 1
        next_disabled = st.session_state["current_step_val"] >= total_steps

        # Previous / Next buttons (disabled at bounds)
        if st.button("Previous step", disabled=prev_disabled):
            if st.session_state["current_step_val"] > 1:
                st.session_state["current_step_val"] -= 1

        if st.button("Next step", disabled=next_disabled):
            if st.session_state["current_step_val"] < total_steps:
                st.session_state["current_step_val"] += 1

        if st.button("Skip to final result"):
            st.session_state["current_step_val"] = total_steps

        if st.button("Back to start"):
            st.session_state["current_step_val"] = 1

        # (Removed Play/Pause and autoplay controls — navigation is manual
        # via the slider and the Previous/Next/Skip/Back buttons.)

    # fetch the snapshot for the selected step (1-indexed UI -> 0-indexed list)
    snap = snapshots[st.session_state["current_step_val"] - 1]

    col_info, col_bar = st.columns(2)

    with col_info:
        # when not on the final step, show the single student processed at this step
        if st.session_state["current_step_val"] < total_steps:
            st.subheader("Student processed at this step")
            st.write(f"Student ID: {snap['student_id']}")
            # display GPA rounded to 2 decimal places in the UI
            st.write(f"GPA: {snap['gpa']:.2f}")
            st.write("Preferences:")
            st.write(" → ".join(snap["prefs"]))
            st.write(f"Allocated to: **{snap['chosen']}**")
        else:
            st.subheader("Final allocation summary")
            st.write(
                "All students have been processed. "
                "Use the assignments table below for a complete view."
            )

        st.markdown("**Assignments so far**")
        # assignments is a mapping student_id -> spec (or None). Convert to DataFrame.
        assignments_df = pd.DataFrame.from_dict(
            snap["assignments"],
            orient="index",
            columns=["Spec"]
        )
        assignments_df.index.name = "student_id"
        st.dataframe(assignments_df)

    with col_bar:
        st.subheader("Remaining seats per specialisation")
        rem_df = pd.DataFrame({
            "Spec": list(snap["remaining"].keys()),
            "Remaining seats": list(snap["remaining"].values())
        })
        st.bar_chart(rem_df, x="Spec", y="Remaining seats")

    st.subheader("Cutoff and stats (final state only)")
    # Compute cutoff stats only when viewing the final snapshot
    if st.session_state["current_step_val"] == total_steps:
        final_assignments = snapshots[-1]["assignments"]
        df_final = df_students.copy()
        df_final["assigned_spec"] = df_final["id"].map(final_assignments)

        cutoff_rows = []
        for spec in spec_list:
            mask = df_final["assigned_spec"] == spec
            if mask.any():
                min_gpa = df_final.loc[mask, "gpa"].min()
                max_gpa = df_final.loc[mask, "gpa"].max()
                cutoff_rows.append({
                    "Spec": spec,
                    "Lowest GPA in spec": min_gpa,
                    "Highest GPA in spec": max_gpa,
                    "Count": int(mask.sum())
                })
        if cutoff_rows:
            cutoff_df = pd.DataFrame(cutoff_rows)
            # round GPA values shown in cutoff table to 2 dp for clarity
            cutoff_df["Lowest GPA in spec"] = cutoff_df["Lowest GPA in spec"].round(2)
            cutoff_df["Highest GPA in spec"] = cutoff_df["Highest GPA in spec"].round(2)
            st.dataframe(cutoff_df)
        else:
            st.write("No students allocated; check capacities and input data.")
