import random
import pandas as pd


def generate_random_students(n_students, specs, n_prefs=5, gpa_min=4.0, gpa_max=9.0, seed=None, mean=None, std=None, sampling_with_replacement=True, pref_weights=None):
    """
    This function generates a synthetic student dataset.

    Parameters:
    n_students : int
        Number of students to create.
    specs : list of str
        Available specialisations.
    n_prefs : int
        Number of ranked preferences per student (default 5).
    pref_weights : dict or None
        Optional mapping {spec: weight} that biases the selection of preferences.
        When provided, preferences for each student are sampled without replacement
        using these weights so more "popular" specialisations appear earlier/more
        frequently in generated preference lists.
    gpa_min, gpa_max : float
        Range for uniform GPA sampling.
    seed : int or None
        Random seed for reproducibility.

    Returns:
    df : pandas.DataFrame
        Columns: id, gpa, pref1, ..., prefN
    """
    # optional reproducibility: seed the RNG so repeated runs produce same students
    if seed is not None:
        random.seed(seed)

    rows = []
    n_prefs = min(n_prefs, len(specs))

    # build the discrete GPA grid using exact 1/63 increments spanning gpa_min..gpa_max
    # this yields 64 levels: gpa_min, gpa_min + step, ..., gpa_max
    step = (gpa_max - gpa_min) / 63.0
    # create all 64 grid levels with reasonable precision
    allowed_gpas = [round(gpa_min + i * step, 6) for i in range(64)]

    # keep only those within the requested min/max range (should all be in range)
    allowed_gpas = [g for g in allowed_gpas if gpa_min <= g <= gpa_max]

    # If mean/std are not provided, default to the center of the range and a reasonable spread
    if mean is None:
        mean = (gpa_min + gpa_max) / 2.0
    if std is None:
        std = (gpa_max - gpa_min) / 6.0  # ~99.7% within range for 6 sigma

    # build weights from a normal PDF evaluated at each discrete GPA grid point
    import math

    def normal_pdf(x, mu, sigma):
        if sigma <= 0:
            return 0.0
        coef = 1.0 / (sigma * math.sqrt(2 * math.pi))
        exp_term = math.exp(-0.5 * ((x - mu) / sigma) ** 2)
        return coef * exp_term

    weights = [normal_pdf(g, mean, std) for g in allowed_gpas]
    total_w = sum(weights)
    if total_w <= 0:
        # fallback to uniform weights if something odd happens
        weights = [1.0 for _ in weights]
        total_w = sum(weights)

    # convert to probabilities (normalized weights)
    probs = [w / total_w for w in weights]

    if not allowed_gpas:
        # fallback: if the discrete grid produced nothing (odd min/max), use the continuous range
        allowed_gpas = [round(random.uniform(gpa_min, gpa_max), 3) for _ in range(max(1, n_students))]

    # Now select GPAs for students according to the probability mass defined by the normal PDF on the grid.
    # Two modes are supported:
    #  1) sampling_with_replacement: sample with replacement (bootstrapping). Each student's GPA
    #    is an independent draw from the discrete distribution (allowed_gpas, probs). This allows repeats.
    #
    #  2) sampling_without_replacement: perform weighted sampling without replacement. Each selected GPA
    #    is removed and probabilities renormalized; useful when you want distinct levels where possible.
    if sampling_with_replacement:
        # Bootstrapping: sample independent draws with replacement according to the grid probabilities
        gpas = random.choices(allowed_gpas, weights=probs, k=n_students)
    else:
        # Weighted sampling without replacement: iteratively select indices according to current probs,
        # remove the chosen item, and renormalize. This is fine for the small fixed grid size (64).
        choices = allowed_gpas.copy()
        choice_probs = probs.copy()

        def weighted_pop(probs_list):
            r = random.random()
            cum = 0.0
            for idx, p in enumerate(probs_list):
                cum += p
                if r <= cum:
                    return idx
            return len(probs_list) - 1

        gpas = []
        for _ in range(min(n_students, len(choices))):
            idx = weighted_pop(choice_probs)
            gpas.append(choices.pop(idx))
            choice_probs.pop(idx)
            s = sum(choice_probs)
            if s > 0:
                choice_probs = [p / s for p in choice_probs]
        # if more students than available choices (unlikely here), fill remaining with replacement draws
        if len(gpas) < n_students:
            extras = random.choices(allowed_gpas, weights=probs, k=n_students - len(gpas))
            gpas.extend(extras)

    for i in range(n_students):
        # take GPA from prepared list and round to 3 decimals for storage
        gpa = round(gpas[i], 3)

        # build preference list. By default sample uniformly without replacement
        # (random.sample). If pref_weights is provided (mapping spec->weight),
        # perform iterative weighted sampling without replacement so popular
        # specs (higher weight) appear more frequently.
        if pref_weights is None:
            prefs = random.sample(specs, k=n_prefs)
        else:
            # prepare choices and probabilities according to provided weights
            choices = specs.copy()
            # if pref_weights contains keys not in specs, they are ignored
            probs = [float(pref_weights.get(s, 0.0)) for s in choices]
            # fallback to uniform if all weights are zero or negative
            if sum(probs) <= 0:
                prefs = random.sample(specs, k=n_prefs)
            else:
                # iterative weighted sampling without replacement
                sel = []
                probs_copy = probs.copy()
                choices_copy = choices.copy()

                def weighted_pop_index(probs_list):
                    r = random.random()
                    cum = 0.0
                    s = sum(probs_list)
                    if s <= 0:
                        # fallback: uniform selection
                        return random.randrange(len(probs_list))
                    for idx, p in enumerate(probs_list):
                        cum += p / s
                        if r <= cum:
                            return idx
                    return len(probs_list) - 1

                for _ in range(min(n_prefs, len(choices_copy))):
                    idx = weighted_pop_index(probs_copy)
                    sel.append(choices_copy.pop(idx))
                    probs_copy.pop(idx)
                # if more prefs requested than choices available (unlikely), fill randomly
                if len(sel) < n_prefs:
                    remaining = [c for c in specs if c not in sel]
                    sel.extend(random.sample(remaining, k=(n_prefs - len(sel))))
                prefs = sel
        row = {"id": i + 1, "gpa": gpa}
        # attach each preference as pref1, pref2, ...
        for j, p in enumerate(prefs):
            row[f"pref{j + 1}"] = p
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values("gpa", ascending=False).reset_index(drop=True)
    return df


def _pref_index(col_name):
    """
    The purpose of this function is to convert a column name like "pref1" into its numeric order.
    """
    try:
        return int(col_name[4:])
    except ValueError:
        return 999


def allocation_steps(df, capacity_dict, max_prefs=5, random_fallback=True, seed=None):
    """
    This function runs a GPA based allocation and records a snapshot after each student.

    The rule used is:
      * Students are sorted by GPA descending.
      * For each student we look at pref1..pref5 (or fewer if not present).
      * We try each preference in order:
          allocate to the first spec with free capacity.
      * If none of the preferences have capacity and random_fallback is True:
          pick a random spec that still has capacity and is not in the preference list.
      * If there is still no capacity anywhere:
          the student remains unallocated (chosen None).

    Parameters:
    df : pandas.DataFrame
        Must contain columns "id", "gpa", and some "prefX" columns.
    capacity_dict : dict
        {spec_name: seat_count}.
    max_prefs : int
        Maximum number of preference columns to respect.
    random_fallback : bool
        Whether to randomly allocate if all preferences are full.
    seed : int or None
        Random seed for reproducibility.

    Returns:
    snapshots : list of dict
        Each snapshot has keys:
        "student_id", "gpa", "prefs", "chosen",
        "remaining" (capacity per spec),
        "assignments" (map id -> spec or None).
    """
    # seed random used for any fallback random allocations
    if seed is not None:
        random.seed(seed)

    # basic validation: dataset must have student id and GPA
    if "id" not in df.columns or "gpa" not in df.columns:
        raise ValueError('DataFrame must contain "id" and "gpa" columns.')

    # process students in descending GPA order (highest priority first)
    df_sorted = df.sort_values("gpa", ascending=False)

    # working copy of remaining capacities, and assignment map
    caps = capacity_dict.copy()
    assignments = {}
    snapshots = []

    # discover preference columns (pref1, pref2, ...) and respect up to max_prefs
    pref_cols = [c for c in df_sorted.columns if c.startswith("pref")]
    pref_cols = sorted(pref_cols, key=_pref_index)[:max_prefs]

    for _, row in df_sorted.iterrows():
        student_id = row["id"]
        gpa = row["gpa"]
        # collect this student's declared preferences in order
        prefs = [row[c] for c in pref_cols if pd.notna(row[c])]

        chosen = None

        # attempt to allocate to the first preferred spec with remaining seats
        for spec in prefs:
            if caps.get(spec, 0) > 0:
                caps[spec] -= 1
                chosen = spec
                break

        # if no preferred spec has space, optionally assign a random spec
        # that still has capacity and was not in the student's preference list
        if chosen is None and random_fallback:
            available_specs = [
                spec for spec, remaining in caps.items()
                if remaining > 0 and spec not in prefs
            ]
            if available_specs:
                chosen = random.choice(available_specs)
                caps[chosen] -= 1

        # record the assignment (or None) and snapshot the current state
        assignments[student_id] = chosen

        snapshots.append({
            "student_id": student_id,
            "gpa": gpa,
            "prefs": prefs,
            "chosen": chosen,
            "remaining": caps.copy(),
            "assignments": assignments.copy()
        })

    return snapshots
