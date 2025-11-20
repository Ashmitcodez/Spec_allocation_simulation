import sys
import pathlib

# make repo root importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from allocation import generate_random_students


def test_generated_gpas_are_on_grid():
    n_students = 10
    gpa_min = 0.0
    gpa_max = 9.0
    seed = 123

    df = generate_random_students(
        n_students=n_students,
        specs=["Software", "Mechanical"],
        n_prefs=2,
        gpa_min=gpa_min,
        gpa_max=gpa_max,
        seed=seed,
        mean=6.0,
        std=1.25,
        sampling_with_replacement=True,
    )

    # compute expected grid values rounded to 3 decimals (storage rounding in generator)
    step = (gpa_max - gpa_min) / 63.0
    grid = {round(gpa_min + i * step, 3) for i in range(64)}

    gpas = list(df["gpa"])
    # all generated GPAs should be members of the grid
    assert all(g in grid for g in gpas)
