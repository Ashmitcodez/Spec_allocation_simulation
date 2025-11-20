import pandas as pd

REQUIRED_COLUMNS = ["id", "gpa"]

def load_student_csv(file) -> pd.DataFrame:
    """
    Load a student CSV from an uploaded file like a Streamlit uploader object.

    Expected columns:
      id, gpa, pref1, pref2, ... (up to pref5 or more)

    Returns:
    df : pandas.DataFrame
    """
    # read uploaded CSV-like object into a DataFrame
    df = pd.read_csv(file)

    # ensure required columns are present
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    # coerce GPA to numeric and fail early if parsing problems are found
    df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
    if df["gpa"].isna().any():
        raise ValueError("Some GPA values could not be parsed as numbers.")

    # keep original ordering / columns but caller may sort by GPA as needed
    return df
