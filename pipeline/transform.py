import pandas as pd
import numpy as np
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.connection import engine, SessionLocal
from db.schema import (
    DimAgency, DimFiscalYear, DimObjectCode,
    DimExpenseClass, FactBudgetAllocation
)


# ---------------------------------------------------------------------------
# 1. load staged data into a DataFrame for transformation
# ---------------------------------------------------------------------------

def load_staged_data(source_file: str) -> pd.DataFrame:
    """
    Pull unprocessed rows from the staging table into a DataFrame.
    Only loads rows where is_processed = False.
    """
    query = text("""
        SELECT
            id,
            fiscal_year,
            department_code,
            department_name,
            agency_code,
            agency_name,
            program_name,
            project_name,
            expense_class,
            object_code,
            object_name,
            authorized_appropriation
        FROM stg_budget_allocations
        WHERE source_file = :source_file
          AND is_processed = FALSE
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"source_file": source_file})

    print(f"Loaded {len(df):,} unprocessed rows from staging.")
    return df


# ---------------------------------------------------------------------------
# 2. clean and coerce types
# ---------------------------------------------------------------------------

def clean_staged_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce types, convert amounts, and flag problematic rows.
    Does not drop any rows — flags them for downstream decisions.
    """
    df = df.copy()

    # convert amount from string to numeric, coerce errors to NaN
    df["authorized_appropriation"] = pd.to_numeric(
        df["authorized_appropriation"], errors="coerce"
    )

    # amounts are in thousands of pesos — convert to actual pesos
    df["authorized_appropriation"] = df["authorized_appropriation"] * 1000

    # flag null-amount rows rather than dropping them
    df["has_null_amount"] = df["authorized_appropriation"].isna()

    # standardize string columns — strip, uppercase for codes
    df["department_code"] = df["department_code"].str.strip().str.upper()
    df["agency_code"] = df["agency_code"].str.strip().str.upper()
    df["object_code"] = df["object_code"].str.strip().str.upper()
    df["expense_class"] = df["expense_class"].str.strip().str.upper()

    # normalize agency and department names — title case, strip extra spaces
    df["agency_name"] = df["agency_name"].str.strip().str.title()
    df["department_name"] = df["department_name"].str.strip().str.title()

    # fill null amounts with 0 for fact table — flagged rows are still traceable
    df["authorized_appropriation"] = df["authorized_appropriation"].fillna(0)

    null_count = df["has_null_amount"].sum()
    print(f"Rows with null amounts (set to 0, flagged): {null_count:,}")
    print(f"Rows after cleaning: {len(df):,}")

    return df


# ---------------------------------------------------------------------------
# 3. populate dim_fiscal_year
# ---------------------------------------------------------------------------

def load_fiscal_year_dimension(fiscal_years: list[str]) -> dict[str, int]:
    """
    Insert fiscal year records and return a mapping of year -> fiscal_year_id.
    """
    mapping = {}

    with SessionLocal() as session:
        for fy in fiscal_years:
            fy_int = int(fy)
            stmt = (
                pg_insert(DimFiscalYear)
                .values(
                    fiscal_year=fy_int,
                    label=f"FY{fy_int}",
                    is_current=(fy_int == 2021),
                    start_date=f"{fy_int}-01-01",
                    end_date=f"{fy_int}-12-31",
                )
                .on_conflict_do_nothing(index_elements=["fiscal_year"])
                .returning(DimFiscalYear.fiscal_year_id, DimFiscalYear.fiscal_year)
            )
            result = session.execute(stmt)
            session.commit()

        # fetch all fiscal years to build mapping
        rows = session.execute(
            text("SELECT fiscal_year_id, fiscal_year FROM dim_fiscal_year")
        ).fetchall()
        mapping = {str(row.fiscal_year): row.fiscal_year_id for row in rows}

    print(f"Fiscal year dimension loaded: {mapping}")
    return mapping


# ---------------------------------------------------------------------------
# 4. populate dim_agency
# ---------------------------------------------------------------------------

def load_agency_dimension(df: pd.DataFrame) -> dict[str, int]:
    """
    Extract unique agency combinations from staged data,
    insert into dim_agency, and return a mapping of agency_code -> agency_id.
    """
    agencies = (
        df[["department_code", "department_name", "agency_code", "agency_name"]]
        .drop_duplicates(subset=["department_code", "agency_code"])
        .dropna(subset=["agency_code"])
        .reset_index(drop=True)
    )

    print(f"Unique agencies found: {len(agencies):,}")

    with SessionLocal() as session:
        for _, row in agencies.iterrows():
            stmt = (
                pg_insert(DimAgency)
                .values(
                    department_code=row["department_code"],
                    department_name=row["department_name"],
                    agency_code=row["agency_code"],
                    agency_name=row["agency_name"],
                )
                .on_conflict_do_nothing(
                    constraint="uq_agency_dept_code"
                )
            )
            session.execute(stmt)
        session.commit()

        rows = session.execute(
            text("SELECT agency_id, agency_code, department_code FROM dim_agency")
        ).fetchall()

    # build composite key mapping: (dept_code, agency_code) -> agency_id
    mapping = {
        (row.department_code, row.agency_code): row.agency_id
        for row in rows
    }

    print(f"Agency dimension records: {len(mapping):,}")
    return mapping


# ---------------------------------------------------------------------------
# 5. populate dim_object_code
# ---------------------------------------------------------------------------

def load_object_code_dimension(df: pd.DataFrame) -> dict[str, int]:
    """
    Extract unique sub-object codes, link to expense class,
    insert into dim_object_code, and return object_code -> object_code_id mapping.
    """
    # UACS expense class codes from the source file map to our
    # standardized short codes in dim_expense_class.
    # The UACS code prefix determines the expense class:
    #   5010... = Personnel Services (PS)
    #   5020... = Maintenance and Other Operating Expenses (MOOE)
    #   5060... = Capital Outlay (CO)
    #   5030... = Financial Expenses (FE)
    EXPENSE_CLASS_CODE_MAP = {
        "1": "PS",
        "2": "MOOE",
        "3": "FE",
        "6": "CO",
    }


    def resolve_expense_class_code(raw_code) -> str | None:
        if pd.isna(raw_code):
            return None
        return EXPENSE_CLASS_CODE_MAP.get(str(raw_code).strip())

    # Fetch expense class id mapping using short codes
    with SessionLocal() as session:
        ec_rows = session.execute(
            text("SELECT expense_class_id, expense_class_code FROM dim_expense_class")
        ).fetchall()
    ec_map = {row.expense_class_code: row.expense_class_id for row in ec_rows}

    object_codes = (
        df[["object_code", "object_name", "expense_class"]]
        .drop_duplicates(subset=["object_code"])
        .dropna(subset=["object_code"])
        .reset_index(drop=True)
    )

    print(f"Unique object codes found: {len(object_codes):,}")

    with SessionLocal() as session:
        for _, row in object_codes.iterrows():
            # Resolve the short expense class code from the UACS prefix
            short_code = resolve_expense_class_code(row["expense_class"])
            ec_id = ec_map.get(short_code) if short_code else None

            stmt = (
                pg_insert(DimObjectCode)
                .values(
                    object_code=row["object_code"],
                    object_name=row["object_name"],
                    expense_class_id=ec_id,
                )
                .on_conflict_do_update(
                    constraint="uq_object_code",
                    set_={"expense_class_id": ec_id},
                )
            )
            session.execute(stmt)
        session.commit()

        rows = session.execute(
            text("SELECT object_code_id, object_code FROM dim_object_code")
        ).fetchall()

    mapping = {row.object_code: row.object_code_id for row in rows}
    print(f"Object code dimension records: {len(mapping):,}")
    return mapping


# ---------------------------------------------------------------------------
# 6. load fact table
# ---------------------------------------------------------------------------

def load_fact_table(
    df: pd.DataFrame,
    agency_map: dict,
    fy_map: dict,
    object_code_map: dict,
    chunk_size: int = 10_000,
) -> int:
    """
    Resolve surrogate keys from dimension mappings and insert
    rows into fact_budget_allocation.
    """
    df = df.copy()

    # resolve agency_id using composite key
    df["agency_id"] = df.apply(
        lambda r: agency_map.get((r["department_code"], r["agency_code"])),
        axis=1,
    )

    # resolve fiscal_year_id
    df["fiscal_year_id"] = df["fiscal_year"].map(fy_map)

    # resolve object_code_id
    df["object_code_id"] = df["object_code"].map(object_code_map)

    # resolve expense_class_id via object_code dimension
    with engine.connect() as conn:
        ec_rows = conn.execute(
            text("""
                SELECT oc.object_code_id, oc.expense_class_id
                FROM dim_object_code oc
            """)
        ).fetchall()
    ec_id_map = {row.object_code_id: row.expense_class_id for row in ec_rows}
    df["expense_class_id"] = df["object_code_id"].map(ec_id_map)

    # drop rows where agency_id could not be resolved
    unresolved = df["agency_id"].isna().sum()
    if unresolved > 0:
        print(f"WARNING: {unresolved:,} rows could not be resolved to an agency_id. Dropping.")
        df = df.dropna(subset=["agency_id"])

    # compute derived measures
    # utilization_rate = obligations / appropriation (obligations are 0 here — appropriation only)
    # disbursement_rate = disbursements / obligations (same — placeholders for execution data)
    df["utilization_rate"] = None
    df["disbursement_rate"] = None

    # Select only the columns the fact table needs
    fact_cols = [
        "agency_id", "fiscal_year_id", "expense_class_id", "object_code_id",
        "program_name", "project_name",
        "authorized_appropriation",
        "utilization_rate", "disbursement_rate",
        "id",  # staging row id for lineage
    ]
    fact_df = df[fact_cols].rename(columns={"id": "source_staging_id"})

    # convert agency_id and fiscal_year_id to int safely
    # Convert integer FK columns safely — pandas upcasts to float when NaN
    # is present in mapped columns, so must convert back explicitly
    int_cols = ["agency_id", "fiscal_year_id"]
    # Convert all integer FK columns safely.
# pandas upcasts any column with NaN to float64 automatically.
# Int64 (capital I) is pandas nullable integer — holds NaN without float cast.
    for col in ["agency_id", "fiscal_year_id"]:
        fact_df[col] = fact_df[col].astype(int)

    for col in ["object_code_id", "expense_class_id", "source_staging_id"]:
        fact_df[col] = pd.array(
           pd.to_numeric(fact_df[col], errors="coerce"),
           dtype="Int64"
    )

    # replace NaN with None for nullable columns
    fact_df = fact_df.where(pd.notna(fact_df), other=None)

    # insert in chunks
    total_inserted = 0
    total_chunks = (len(fact_df) // chunk_size) + 1

    with engine.begin() as conn:
        for i in range(0, len(fact_df), chunk_size):
            chunk = fact_df.iloc[i: i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            conn.execute(
                FactBudgetAllocation.__table__.insert(),
                chunk.to_dict(orient="records"),
            )
            total_inserted += len(chunk)
            print(f"  Fact chunk {chunk_num}/{total_chunks}: {total_inserted:,} rows", end="\r")

    print()
    return total_inserted


# ---------------------------------------------------------------------------
# 7. mark staging rows as processed
# ---------------------------------------------------------------------------

def mark_staging_processed(source_file: str) -> None:
    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE stg_budget_allocations
                SET is_processed = TRUE
                WHERE source_file = :source_file
            """),
            {"source_file": source_file},
        )
        conn.commit()
    print(f"Marked staging rows as processed for: {source_file}")


# ---------------------------------------------------------------------------
# ORCHESTRATOR that run all transformation steps in order
# ---------------------------------------------------------------------------

def run_transformation(source_file: str) -> dict:
    print(f"\n--- Starting transformation for: {source_file} ---\n")

    df = load_staged_data(source_file)
    df = clean_staged_data(df)

    fiscal_years = df["fiscal_year"].dropna().unique().tolist()
    fy_map = load_fiscal_year_dimension(fiscal_years)
    agency_map = load_agency_dimension(df)
    object_code_map = load_object_code_dimension(df)

    rows_inserted = load_fact_table(df, agency_map, fy_map, object_code_map)
    mark_staging_processed(source_file)

    summary = {
        "source_file": source_file,
        "staged_rows": len(df),
        "fact_rows_inserted": rows_inserted,
    }

    print(f"\n--- Transformation complete ---")
    print(f"Fact rows inserted: {rows_inserted:,}")
    return summary