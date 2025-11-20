# Spec Allocation Simulator 
Project link: https://spec-allocation-simulator.streamlit.app/

This repository contains a simulator for GPA-based allocation of students into engineering specialisations at UoA. It includes:

- `app.py` : a Streamlit UI to configure capacities, generate synthetic students or upload a CSV, run the allocation, and visualise the algorithm step-by-step.
- `allocation.py` : core logic for generating synthetic students and running the allocation algorithm.
- `data_utils.py` : helper functions to load and validate a CSV of student preferences.
- `sample_students.csv` : an example CSV you can upload to the app.

Below you'll find an explanation of how the simulation works, why the synthetic data looks like it does, and a short guide for using the app.

## Explanation of the logic around key features of the simulation

- Allocation rule (what the program does): 
    - students are first ordered by GPA from highest to lowest. 
    - Each student has an ordered list of preferred specialisations. 
    - The system goes through students one by one and tries to put each student into their top available preference. 
    - If none of their choices has space, the program can (optionally) place them randomly into any remaining specialisation. If the random allocation button is toggled off, the simulation assigns thier spec as `None` and this can be a flag and this can be a flag to manually assign them into remaing specs that are closer to preference after the simulation ends.

- How GPAs and preferences are made for synthetic students:
  When the app creates fake (synthetic) students it follows a simple, repeatable procedure that combines a preference sampling step and a GPA sampling step.

  1. IDs and preferences
    - IDs are sequential integers (1, 2, 3, ...). This just gives each generated student a stable identifier.
  - Preferences: for each student the generator selects `n_prefs` distinct specialisations by sampling without replacement from the available spec list (this is what produces a ranked list like `pref1`, `pref2`, ...).
  - By default these choices are uniform across the specs, so every specialisation is equally likely to appear in a student's list.
  - Popularity weights (optional): you can bias which specialisations are more likely to appear in students' preferences by passing a `pref_weights` mapping (spec name -> weight) to the generator. When provided, preferences are sampled without replacement but according to these weights: the weights are converted to probabilities and renormalised each time a choice is made, so higher-weighted (more "popular") specs appear earlier and more often across generated students. This models real-world popularity differences between programmes.
    - If all weights sum to zero or are invalid the generator falls back to uniform sampling.
    - Missing spec names in the mapping or negative weights are treated as zero.

  2. GPA generation (distributions and bootstrapping)
    - Discrete GPA grid: GPAs are chosen from a small fixed set of allowed values (64 levels) evenly spaced across the chosen GPA range. This keeps the synthetic GPAs simple and comparable.
    - Normal distribution sampling: the generator computes a weight for each allowed GPA value using the Normal (Gaussian) density centred at a chosen mean with a chosen standard deviation. These weights are normalised and used as the probability mass over the discrete grid. In plain terms, GPAs near the centre of the range become more likely, producing a bell-shaped (``normal'') appearance in the generated distribution.
    - Bootstrapping (sampling with replacement — default): by default each student's GPA is drawn independently from the discrete probability distribution. This means the same GPA value can appear for many students. This process is like taking independent samples from a population, which statisticians call bootstrapping. Bootstrapping is useful for producing realistic-looking repeats and for studying variability across repeats.
    - Sampling without replacement (optional): alternatively, the generator can remove chosen grid values as they are used and renormalize the probabilities so subsequent draws prefer the remaining values. This reduces duplicates when you prefer more distinct GPAs.

## Using the app (user guide)

- Start the app (in this project folder):

  ```bash
  streamlit run app.py
  ```

- Step 1: set the specialisations and how many seats each has.
- Step 2: either upload a CSV of students (if you have real data) or ask the app to generate synthetic students. The generator can be configured but sensible defaults are provided.
- Step 3: run the allocation engine.
- Step 4: view the results step-by-step using the slider and the "Previous step" / "Next step" buttons, or jump straight to the final allocation.

This flow is intentionally simple: generate or upload students, run the allocation, then inspect the per-student snapshots.

## Short technical note (if you want more detail)

- The synthetic GPAs are produced by evaluating a Normal (Gaussian) curve over a discrete set of possible GPA values and sampling from that discrete distribution. The Normal curve is the usual "bell curve" - it biases draws toward the centre of the GPA range.
- "Bootstrapping" (sampling with replacement) means each student's GPA is an independent draw from that distribution. So, the same GPA value can appear for multiple students. There is also an option to sample without replacement from the discrete grid if you prefer more distinct GPAs.
- Allocation snapshots are recorded after each student so you can replay the process and see how capacities change over time.

## Example CSV columns

- id, gpa, pref1, pref2, ...

If you prefer to test on your own data, use the included `sample_students.csv` file as an upload to the app.

## Run and test (if you wish to use this project in developer mode)

Install dependencies and run the app locally. A `requirements.txt` file is included so you can install the exact dependencies used here:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then, to run the unit tests:

```bash
pytest -q
```

Note: `watchdog` is recommended for faster Streamlit auto-reload but is optional (listed in `requirements.txt` as a commented suggestion).

