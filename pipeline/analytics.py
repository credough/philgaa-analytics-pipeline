import pandas as pd
from sqlalchemy import text
from db.connection import engine


# ---------------------------------------------------------------------------
# CORE QUERY HELPER
# all analytics functions use this to execute SQL and return a DataFrame.
# Centralizing execution makes it easy to add caching or logging.
# ---------------------------------------------------------------------------

def _query(sql: str, params: dict = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


# ---------------------------------------------------------------------------
# analysis 1 — total budget by agency
# ---------------------------------------------------------------------------

def total_budget_by_agency(
    fiscal_year: int = 2021,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Returns the top N agencies by total authorized appropriation
    for a given fiscal year.

    Columns: agency_name, department_name, total_appropriation, rank
    """
    sql = """
        SELECT
            a.agency_name,
            a.department_name,
            SUM(f.authorized_appropriation)        AS total_appropriation,
            RANK() OVER (
                ORDER BY SUM(f.authorized_appropriation) DESC
            )                                      AS rank
        FROM fact_budget_allocation f
        JOIN dim_agency      a  ON f.agency_id      = a.agency_id
        JOIN dim_fiscal_year fy ON f.fiscal_year_id = fy.fiscal_year_id
        WHERE fy.fiscal_year = :fiscal_year
        GROUP BY a.agency_name, a.department_name
        ORDER BY total_appropriation DESC
        LIMIT :top_n
    """
    df = _query(sql, {"fiscal_year": fiscal_year, "top_n": top_n})
    df["total_appropriation"] = pd.to_numeric(df["total_appropriation"])
    return df


# ---------------------------------------------------------------------------
# analysis 2 — budget by expense class
# ---------------------------------------------------------------------------

def budget_by_expense_class(fiscal_year: int = 2021) -> pd.DataFrame:
    """
    Returns total authorized appropriation broken down by expense class
    (PS, MOOE, CO, FE) with percentage share of total.

    Columns: expense_class_name, expense_class_code, total_appropriation,
             pct_of_total
    """
    sql = """
        SELECT
            ec.expense_class_name,
            ec.expense_class_code,
            SUM(f.authorized_appropriation)   AS total_appropriation
        FROM fact_budget_allocation f
        JOIN dim_object_code  oc ON f.object_code_id  = oc.object_code_id
        JOIN dim_expense_class ec ON oc.expense_class_id = ec.expense_class_id
        JOIN dim_fiscal_year  fy ON f.fiscal_year_id  = fy.fiscal_year_id
        WHERE fy.fiscal_year = :fiscal_year
        GROUP BY ec.expense_class_name, ec.expense_class_code
        ORDER BY total_appropriation DESC
    """
    df = _query(sql, {"fiscal_year": fiscal_year})
    df["total_appropriation"] = pd.to_numeric(df["total_appropriation"])
    total = df["total_appropriation"].sum()
    df["pct_of_total"] = (df["total_appropriation"] / total * 100).round(2)
    return df


# ---------------------------------------------------------------------------
# analysis 3 — budget by department
# ---------------------------------------------------------------------------

def budget_by_department(
    fiscal_year: int = 2021,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Returns total authorized appropriation grouped at the department level.
    Useful for sector-level analysis above the agency grain.

    Columns: department_name, department_code, total_appropriation,
             agency_count, pct_of_total
    """
    sql = """
        SELECT
            a.department_name,
            a.department_code,
            SUM(f.authorized_appropriation)   AS total_appropriation,
            COUNT(DISTINCT a.agency_id)        AS agency_count
        FROM fact_budget_allocation f
        JOIN dim_agency      a  ON f.agency_id      = a.agency_id
        JOIN dim_fiscal_year fy ON f.fiscal_year_id = fy.fiscal_year_id
        WHERE fy.fiscal_year = :fiscal_year
        GROUP BY a.department_name, a.department_code
        ORDER BY total_appropriation DESC
        LIMIT :top_n
    """
    df = _query(sql, {"fiscal_year": fiscal_year, "top_n": top_n})
    df["total_appropriation"] = pd.to_numeric(df["total_appropriation"])
    total = df["total_appropriation"].sum()
    df["pct_of_total"] = (df["total_appropriation"] / total * 100).round(2)
    return df


# ---------------------------------------------------------------------------
# analysis 4 — top programs by budget
# ---------------------------------------------------------------------------

def top_programs_by_budget(
    fiscal_year: int = 2021,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Returns the top N programs by total authorized appropriation.
    Programs are identified by project_name and grouped with their
    parent agency for context.

    Columns: project_name, agency_name, total_appropriation, rank
    """
    sql = """
        SELECT
            f.project_name,
            a.agency_name,
            SUM(f.authorized_appropriation)        AS total_appropriation,
            RANK() OVER (
                ORDER BY SUM(f.authorized_appropriation) DESC
            )                                      AS rank
        FROM fact_budget_allocation f
        JOIN dim_agency      a  ON f.agency_id      = a.agency_id
        JOIN dim_fiscal_year fy ON f.fiscal_year_id = fy.fiscal_year_id
        WHERE fy.fiscal_year = :fiscal_year
          AND f.project_name IS NOT NULL
        GROUP BY f.project_name, a.agency_name
        ORDER BY total_appropriation DESC
        LIMIT :top_n
    """
    df = _query(sql, {"fiscal_year": fiscal_year, "top_n": top_n})
    df["total_appropriation"] = pd.to_numeric(df["total_appropriation"])
    return df


# ---------------------------------------------------------------------------
# analysis 5 — KPI summary
# ---------------------------------------------------------------------------

def budget_summary_kpis(fiscal_year: int = 2021) -> dict:
    """
    Returns headline KPI figures for the dashboard summary cards.

    Keys: total_appropriation, total_agencies, total_departments,
          total_programs, largest_agency, largest_agency_budget,
          top_expense_class, fiscal_year
    """
    sql = """
        SELECT
            SUM(f.authorized_appropriation)        AS total_appropriation,
            COUNT(DISTINCT f.agency_id)            AS total_agencies,
            COUNT(DISTINCT a.department_code)      AS total_departments,
            COUNT(DISTINCT f.project_name)         AS total_programs
        FROM fact_budget_allocation f
        JOIN dim_agency      a  ON f.agency_id      = a.agency_id
        JOIN dim_fiscal_year fy ON f.fiscal_year_id = fy.fiscal_year_id
        WHERE fy.fiscal_year = :fiscal_year
    """
    summary = _query(sql, {"fiscal_year": fiscal_year}).iloc[0]

    # Largest single agency
    top_agency_df = total_budget_by_agency(fiscal_year=fiscal_year, top_n=1)
    top_agency = top_agency_df.iloc[0] if not top_agency_df.empty else None

    # Dominant expense class
    ec_df = budget_by_expense_class(fiscal_year=fiscal_year)
    top_ec = ec_df.iloc[0] if not ec_df.empty else None

    return {
        "fiscal_year": fiscal_year,
        "total_appropriation": float(summary["total_appropriation"]),
        "total_agencies": int(summary["total_agencies"]),
        "total_departments": int(summary["total_departments"]),
        "total_programs": int(summary["total_programs"]),
        "largest_agency": top_agency["agency_name"] if top_agency is not None else None,
        "largest_agency_budget": float(top_agency["total_appropriation"]) if top_agency is not None else None,
        "top_expense_class": top_ec["expense_class_name"] if top_ec is not None else None,
        "top_expense_class_pct": float(top_ec["pct_of_total"]) if top_ec is not None else None,
    }