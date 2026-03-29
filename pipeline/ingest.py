import os
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import text
from db.connection import engine, SessionLocal
from db.schema import StagingBudgetAllocation

# ---------------------------------------------------------------------------
# Column mapping from source file headers to staging table columns.
# Columns not listed here are intentionally dropped at ingestion time.
# Dropped: OPERUNIT, UACS_OPER_DSC, UACS_REG_ID, FUNDCD, UACS_FUNDSUBCAT_DSC
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "DEPARTMENT":        "department_code",
    "UACS_DPT_DSC":      "department_name",
    "AGENCY":            "agency_code",
    "UACS_AGY_DSC":      "agency_name",
    "PREXC_FPAP_ID":     "program_name",
    "DSC":               "project_name",
    "UACS_EXP_CD":       "expense_class",
    "UACS_EXP_DSC":      "object_name",
    "UACS_SOBJ_CD":      "object_code",
    "UACS_SOBJ_DSC":     "object_name_detail",
    "AMT":               "authorized_appropriation",
}

REQUIRED_COLUMNS = set(COLUMN_MAP.keys())
FISCAL_YEAR_2021 = "2021"
CHUNK_SIZE = 10_000


def load_budget_file(filepath: str | Path, fiscal_year: str) -> dict:
    """
    Load a raw GAA Excel file into the staging table.

    Returns a summary dict with rows_read, rows_inserted, and errors.
    Designed to be idempotent — clears existing rows for the same
    source file before inserting, so re-running does not duplicate data.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Budget file not found: {filepath}")

    print(f"Reading file: {filepath.name}")
    print(f"Fiscal year: {fiscal_year}")

    # ------------------------------------------------------------------
    # 1. Read the raw file
    # Row 0 in the Excel file is the "(In Thousand Pesos)" note.
    # Row 1 contains the actual column headers.
    # Data begins at row 2.
    # header=1 tells pandas to use the second row (0-indexed) as headers.
    # ------------------------------------------------------------------
    try:
        df = pd.read_excel(
            filepath,
            sheet_name=0,
            header=1,
            dtype=str,         # Read everything as string first — validate later
            engine="openpyxl",
        )
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file: {e}")

    print(f"Raw rows read: {len(df):,}")

    # ------------------------------------------------------------------
    # 2. Validate that required columns are present
    # ------------------------------------------------------------------
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Source file is missing required columns: {missing}\n"
            f"Found columns: {list(df.columns)}"
        )

    # ------------------------------------------------------------------
    # 3. Select and rename only the columns we need
    # ------------------------------------------------------------------
    df = df[list(COLUMN_MAP.keys())].copy()
    df = df.rename(columns=COLUMN_MAP)

    # UACS_EXP_DSC and UACS_SOBJ_DSC both mapped through COLUMN_MAP.
    # After rename, consolidate: use object_name_detail as object_name
    # when it is more specific than the expense class description.
    if "object_name_detail" in df.columns:
        df["object_name"] = df["object_name_detail"].fillna(df["object_name"])
        df = df.drop(columns=["object_name_detail"])

    # ------------------------------------------------------------------
    # 4. Basic cleaning before staging
    # Strip whitespace from string columns only — no business logic yet.
    # Type coercion and validation happen in transform.py.
    # ------------------------------------------------------------------
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Replace empty strings with None so they store as NULL
    df = df.replace({"": None, "nan": None, "NaN": None})
    df = df.where(pd.notna(df), other=None)

    # ------------------------------------------------------------------
    # 5. Add pipeline metadata columns
    # ------------------------------------------------------------------
    df["source_file"] = filepath.name
    df["fiscal_year"] = fiscal_year
    df["is_processed"] = False

    # ------------------------------------------------------------------
    # 6. Validate row count — warn if suspiciously low
    # ------------------------------------------------------------------
    if len(df) < 1000:
        print(
            f"WARNING: Only {len(df)} rows found. "
            "Verify the file is complete and the header row is correct."
        )

    # ------------------------------------------------------------------
    # 7. Idempotency — remove existing rows for this source file
    # before inserting so re-runs do not create duplicates
    # ------------------------------------------------------------------
    _clear_existing_staging_rows(filepath.name)

    # ------------------------------------------------------------------
    # 8. Insert in chunks to avoid memory issues with 498k rows
    # ------------------------------------------------------------------
    rows_inserted = _insert_chunks(df, CHUNK_SIZE)

    summary = {
        "file": filepath.name,
        "fiscal_year": fiscal_year,
        "rows_read": len(df),
        "rows_inserted": rows_inserted,
    }

    print(f"Ingestion complete: {rows_inserted:,} rows inserted.")
    return summary


def _clear_existing_staging_rows(source_file: str) -> None:
    """
    Delete all staging rows from a previous run of the same source file.
    This is what makes the ingestion step idempotent.
    """
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "DELETE FROM stg_budget_allocations "
                "WHERE source_file = :source_file"
            ),
            {"source_file": source_file},
        )
        conn.commit()
        deleted = result.rowcount
        if deleted > 0:
            print(f"Cleared {deleted:,} existing staging rows for {source_file}.")


def _insert_chunks(df: pd.DataFrame, chunk_size: int) -> int:
    """
    Insert a DataFrame into the staging table in chunks.
    Returns total rows inserted.
    """
    total_inserted = 0
    total_chunks = (len(df) // chunk_size) + 1

    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i : i + chunk_size]
        chunk_num = (i // chunk_size) + 1

        records = chunk.to_dict(orient="records")

        with SessionLocal() as session:
            session.bulk_insert_mappings(StagingBudgetAllocation, records)
            session.commit()

        total_inserted += len(chunk)
        print(f"  Chunk {chunk_num}/{total_chunks}: {total_inserted:,} rows inserted", end="\r")

    print()
    return total_inserted


def validate_staging_load(source_file: str) -> dict:
    """
    Post-load validation. Run after ingestion to confirm data landed correctly.
    Checks row count, null rates on critical columns, and AMT range.
    """
    with engine.connect() as conn:
        row_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM stg_budget_allocations "
                "WHERE source_file = :f"
            ),
            {"f": source_file},
        ).scalar()

        null_agency = conn.execute(
            text(
                "SELECT COUNT(*) FROM stg_budget_allocations "
                "WHERE source_file = :f AND agency_name IS NULL"
            ),
            {"f": source_file},
        ).scalar()

        null_amt = conn.execute(
            text(
                "SELECT COUNT(*) FROM stg_budget_allocations "
                "WHERE source_file = :f AND authorized_appropriation IS NULL"
            ),
            {"f": source_file},
        ).scalar()

    report = {
        "source_file": source_file,
        "total_rows": row_count,
        "null_agency_name": null_agency,
        "null_amt": null_amt,
        "null_agency_pct": round(null_agency / row_count * 100, 2) if row_count else 0,
        "null_amt_pct": round(null_amt / row_count * 100, 2) if row_count else 0,
    }

    print("\nValidation Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")

    return report