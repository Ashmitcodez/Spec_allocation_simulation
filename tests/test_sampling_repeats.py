import sys
import pathlib

# make repo root importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from allocation import generate_random_students


def test_sampling_with_replacement_produces_repeats_when_std_small():
    """When sampling with replacement and the normal std is extremely small,
    most draws should hit the same grid point -> duplicates expected even when
    n_students < number of grid levels.
    """
    n_students = 5  # less than the grid size of 64
    specs = ["Software", "Mechanical", "Civil"]

    # Use gpa_min=0.0..gpa_max=9.0 grid, set mean exactly at gpa_min and tiny std
    df = generate_random_students(
        n_students=n_students,
        specs=specs,
        n_prefs=2,
        gpa_min=0.0,
        gpa_max=9.0,
        seed=12345,
        mean=0.0,
        std=1e-6,
    )

    gpas = list(df["gpa"])
    # because std is tiny and sampling is with replacement, expect duplicates
    assert len(set(gpas)) < n_students
