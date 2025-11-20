import sys
import pathlib
import pandas as pd

# ensure the repository root is on sys.path so tests can import modules in workspace
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from allocation import allocation_steps


def test_gpa_priority_allocation():
    # two students: higher GPA should get the preferred spec if capacity=1
    df = pd.DataFrame([
        {"id": 1, "gpa": 9.0, "pref1": "Software", "pref2": "Mechanical"},
        {"id": 2, "gpa": 8.0, "pref1": "Software", "pref2": "Mechanical"},
    ])

    caps = {"Software": 1, "Mechanical": 1}
    snaps = allocation_steps(df, caps, max_prefs=2, random_fallback=False)

    # after processing both students, Software should have one student (id 1)
    final = snaps[-1]["assignments"]
    assert final[1] == "Software"
    assert final[2] == "Mechanical"


def test_random_fallback_assigns_outside_prefs_with_seed():
    # student lists two prefs that are full, but a different spec has capacity
    df = pd.DataFrame([
        {"id": 1, "gpa": 9.0, "pref1": "Software", "pref2": "Mechanical"},
        {"id": 2, "gpa": 8.5, "pref1": "Software", "pref2": "Mechanical"},
        {"id": 3, "gpa": 7.0, "pref1": "Software", "pref2": "Mechanical"},
    ])

    # fill both preferred specs so the last student must fallback
    caps = {"Software": 1, "Mechanical": 1, "Engineering Science": 1}
    snaps = allocation_steps(df, caps, max_prefs=2, random_fallback=True, seed=42)

    final = snaps[-1]["assignments"]
    # first two should take Software and Mechanical (by GPA)
    assert final[1] == "Software"
    assert final[2] == "Mechanical"
    # last student should be assigned to Engineering Science by random fallback
    assert final[3] == "Engineering Science"
