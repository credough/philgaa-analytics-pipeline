from pathlib import Path
from pipeline.ingest import load_budget_file, validate_staging_load
from pipeline.transform import run_transformation

DATA_DIR = Path("data/raw")

FILES = [
    {"filename": "2021-GAA.xlsx", "fiscal_year": "2021"},
]

if __name__ == "__main__":
    for entry in FILES:
        filepath = DATA_DIR / entry["filename"]

        # Stage
        load_budget_file(filepath, entry["fiscal_year"])
        validate_staging_load(entry["filename"])

        # Transform
        run_transformation(entry["filename"])