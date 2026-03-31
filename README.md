# PhilGAA Analytics Pipeline

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=flat-square&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=flat-square&logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Complete-2ea88a?style=flat-square)

> An end-to-end data pipeline built on real Philippine government budget data from the FY2021 General Appropriations Act (GAA), published by the Department of Budget and Management (DBM). The pipeline ingests 498,342 raw budget line items, models a Kimball-style dimensional warehouse in PostgreSQL, and serves budget intelligence through an interactive multi-page Streamlit dashboard.

---

## Table of Contents

- [Screenshots](#screenshots)
- [Project Overview](#project-overview)
- [Data Model](#data-model)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Dataset](#dataset)
- [Real Data Challenges](#real-data-challenges)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [Analytics and Dashboard](#analytics-and-dashboard)
- [Key Results](#key-results)
- [What This Demonstrates](#what-this-demonstrates)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Screenshots

### Landing Page

![Landing Page](docs/images/screenshots/01_landing.png)

> Hero section with project title, key stats, and data source context.

---

### Overview — KPI Cards and Budget Composition

![Overview Page](docs/images/screenshots/02_overview.png)
![Overview Page](docs/images/screenshots/02_overview1.png)
![Overview Page](docs/images/screenshots/02_overview2.png)

> Four KPI cards showing total appropriation, agencies, departments, and programs. Donut chart showing budget composition by expense class (PS, MOOE, CO, FE).

---

### Agencies — Budget Rankings

![Agencies Page](docs/images/screenshots/03_agencies.png)
![Agencies Page](docs/images/screenshots/03_agencies1.png)

> Interactive horizontal bar chart ranking top agencies by authorized appropriation. Slider controls the number of agencies displayed.

---

### Departments — Budget Distribution

![Departments Page](docs/images/screenshots/04_departments.png)
![Departments Page](docs/images/screenshots/04_departments1.png)
![Departments Page](docs/images/screenshots/04_departments2.png)

> Treemap and horizontal bar chart showing budget distribution aggregated at the department level. Includes agency count and percentage share per department.

---

### Expense Classes — Breakdown

![Expense Classes Page](docs/images/screenshots/05_expense_classes.png)
![Expense Classes Page](docs/images/screenshots/05_expense_classes1.png)

> Side-by-side donut and bar chart breaking down appropriations by Personnel Services, MOOE, Capital Outlay, and Financial Expenses.

---

### Programs — Top by Budget

![Programs Page](docs/images/screenshots/06_programs.png)
![Programs Page](docs/images/screenshots/06_programs1.png)

> Top programs by authorized appropriation with parent agency context. Slider controls the number of programs displayed.

---

## Project Overview

PhilGAA Analytics Pipeline transforms raw government appropriations data into an analytics-ready dimensional warehouse and interactive dashboard. The project follows a classic **Extract → Stage → Transform → Model → Serve** architecture that mirrors production data engineering workflows.

The domain is intentionally practical: government budget data is publicly available, structurally complex, and analytically meaningful — making it a stronger portfolio subject than synthetic or toy datasets.

**Key metrics from the FY2021 dataset:**

| Metric | Value |
|---|---|
| Raw rows ingested | 498,342 |
| Total authorized appropriation | PHP 4.506 trillion |
| Government agencies modeled | 375 |
| Departments modeled | 37 |
| Unique programs | 32,461 |
| Expense sub-object codes | 361 |

---

## Data Model

![PhilGAA Data Model — ERD](docs/images/data_model.png)

> Kimball-style star schema: four dimension tables surrounding a central fact table. All foreign keys are integer surrogate keys. `source_staging_id` provides full lineage back to the raw staging row.

---

## Architecture

![PhilGAA Analytics Pipeline Architecture](docs/images/architecture.png)

> End-to-end pipeline: raw Excel source → chunked ingestion → staging table → dimensional transformation → PostgreSQL warehouse → analytics module → Streamlit dashboard.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Core ETL and transformation logic |
| Database | PostgreSQL 18 | Primary warehouse storage |
| ORM | SQLAlchemy 2.0 | Schema definition and query execution |
| DB Driver | psycopg2-binary | PostgreSQL adapter |
| Data Processing | Pandas 2.2, NumPy | Cleaning, aggregation, transformation |
| Dashboard | Streamlit 1.35 | Interactive multi-page frontend |
| Visualization | Plotly 5.22 | Charts and visualizations |
| Config | python-dotenv | Environment variable management |
| Excel Parsing | openpyxl | Reading .xlsx source files |
| Version Control | Git | feature branches |

---

## Dataset

**Source:** Department of Budget and Management (DBM), Republic of the Philippines
**Document:** Republic Act No. 11518 — General Appropriations Act FY2021, Volume I-A
**URL:** https://www.dbm.gov.ph/index.php/budget-documents/2021

**What the GAA is:** The General Appropriations Act is the annual law that authorizes the Philippine national government's expenditure program for the fiscal year. It specifies the authorized appropriation for every agency, program, and expense item across all departments.

**What the data contains:** One row per agency-program-expense sub-object combination, with the authorized appropriation amount in thousands of Philippine pesos. The file covers all national government agencies across all 37 departments and 375 agencies.

**What the data does not contain:** Budget execution figures (obligations, disbursements) are published separately by DBM as Budget Execution Reports (BERs). The schema is designed to accommodate execution data when it becomes available — `obligations` and `disbursements` columns exist in the fact table as nullable fields.

---

## Real Data Challenges

This project was built on real government data, not a clean synthetic dataset. The following issues were encountered, diagnosed, and resolved during development — each one is authentic to working with public sector open data.

---

### 1. Truncated Column Name in File Preview

**What happened:** The Excel column preview in the spreadsheet application showed `UACS_AG` as the agency name column header. The ingestion pipeline was built with this mapping and failed validation on the first run.

**Actual column name:** `UACS_AGY_DSC`

**Error:**
```
ValueError: Source file is missing required columns: {'UACS_AG'}
Found columns: ['DEPARTMENT', 'UACS_DPT_DSC', 'AGENCY', 'UACS_AGY_DSC', ...]
```

**Resolution:** Diagnosed by reading the actual column list from the validation error output. Updated `COLUMN_MAP` in `pipeline/ingest.py` with the correct header. Added a comment noting the truncation for future maintainers.

**Lesson:** Never assume column names from a visual preview. Always validate against the actual file headers programmatically.

---

### 2. Amounts Denominated in Thousands of Pesos

**What happened:** Row 1 of the Excel file contained the note `(In Thousand Pesos)` — not a header row, but a unit annotation. All `AMT` values in the file represent thousands of pesos, not actual pesos.

**Impact:** Without conversion, PHP 695 billion would be stored as PHP 695 million — a 1,000x error in all financial figures.

**Resolution:** Applied in `pipeline/transform.py` during the cleaning step:

```python
df["authorized_appropriation"] = pd.to_numeric(
    df["authorized_appropriation"], errors="coerce"
)
df["authorized_appropriation"] = df["authorized_appropriation"] * 1000
```

Conversion is intentionally applied in the transformation layer, not ingestion — the staging table preserves the source values exactly as they appear in the file.

**Verification:** Total appropriation after conversion: PHP 4.506 trillion — consistent with publicly reported FY2021 national budget figures.

---

### 3. Null Amounts on 3,206 Rows (0.64%)

**What happened:** Post-load validation revealed 3,206 rows with no `AMT` value — approximately 0.64% of all rows.

**Root cause:** These rows correspond to program description entries and subtotal markers in the GAA structure that carry no direct peso appropriation value. They serve as organizational labels in the source document.

**Resolution:** Flagged rather than dropped. An `has_null_amount` flag was added during transformation and null amounts were set to zero. This preserves all rows in the staging table for lineage and audit purposes while preventing null propagation in the fact table.

```python
df["has_null_amount"] = df["authorized_appropriation"].isna()
df["authorized_appropriation"] = df["authorized_appropriation"].fillna(0)
```

**Lesson:** Never silently drop null rows without understanding why they exist. In government data, nulls often have structural explanations.

---

### 4. Expense Class Stored as Numeric Codes

**What happened:** The `UACS_EXP_CD` column — expected to contain UACS expense class identifiers — contained simple numeric codes (`1`, `2`, `3`, `6`) instead of the expected string codes (`PS`, `MOOE`, `CO`, `FE`) or UACS prefix strings (`5010...`).

**Impact:** The initial prefix-based mapping logic produced zero matches, leaving all 361 object code records with null `expense_class_id`. The expense class breakdown query returned zero rows.

**Diagnosis:** Inspected the staging table directly in psql:

```sql
SELECT DISTINCT expense_class FROM stg_budget_allocations LIMIT 20;
-- Result: 1, 2, 3, 6
```

**Resolution:** Replaced the prefix map with a direct numeric code map:

```python
EXPENSE_CLASS_CODE_MAP = {
    "1": "PS",    # Personnel Services
    "2": "MOOE",  # Maintenance and Other Operating Expenses
    "3": "FE",    # Financial Expenses
    "6": "CO",    # Capital Outlay
}
```

**Lesson:** Always inspect actual column values before writing mapping logic. Documentation and column names do not always match what the data contains.

---

### 5. Pandas Float Upcast on Nullable Integer Foreign Keys

**What happened:** After resolving surrogate keys via `.map()`, integer FK columns (`object_code_id`, `expense_class_id`, `source_staging_id`) were silently upcast to `float64` by pandas — because `.map()` on a Series containing any `NaN` values promotes the dtype automatically. PostgreSQL's `INTEGER` type does not accept float values.

**Error:**
```
psycopg2.errors.NumericValueOutOfRange: integer out of range
[parameters: {'object_code_id__0': 1.0, 'expense_class_id__0': 1.0, ...}]
```

**Resolution:** Used pandas nullable integer dtype (`Int64` with capital I) which holds `NaN` without float promotion:

```python
for col in ["object_code_id", "expense_class_id", "source_staging_id"]:
    fact_df[col] = pd.array(
        pd.to_numeric(fact_df[col], errors="coerce"),
        dtype="Int64"
    )
```

**Lesson:** Pandas `int64` and `Int64` behave differently. Lowercase `int64` cannot hold NaN and will upcast to float. Uppercase `Int64` is the nullable integer extension type.

---

### 6. PostgreSQL 15+ Public Schema Permissions

**What happened:** Schema initialization failed with a permissions error when creating tables under `budget_user`.

**Error:**
```
psycopg2.errors.InsufficientPrivilege: permission denied for schema public
```

**Root cause:** PostgreSQL 15 revoked the default `CREATE` privilege on the public schema that all users had in earlier versions. This is a known breaking change introduced as a security hardening measure.

**Resolution:**
```sql
GRANT ALL ON SCHEMA public TO budget_user;
GRANT ALL PRIVILEGES ON DATABASE ph_gov_budget TO budget_user;
ALTER DATABASE ph_gov_budget OWNER TO budget_user;
```

**Lesson:** PostgreSQL version matters. Behavior that works on PostgreSQL 14 may break on 15+. Always check release notes when upgrading or setting up on a new version.

---

### 7. Structural GAA Data Quirk — "Office Of The Secretary" as Top Agency

**What happened:** The top agency by appropriation is consistently "Office Of The Secretary" across multiple departments — DPWH, DepEd, DOH — rather than the department names themselves.

**Root cause:** This is authentic GAA structure, not a pipeline error. Philippine government agencies consolidate their entire budget allocation under the Office of the Secretary as the parent organizational unit, rather than distributing it across individual bureaus or offices in the appropriations document.

**Impact on analytics:** Department-level aggregation (`budget_by_department`) gives a more accurate picture of sectoral spending than agency-level queries. This is documented in the dashboard under each relevant page.

---

## Project Structure

```
philgaa-analytics-pipeline/
│
├── .env                        # DB credentials — never committed
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml              # Editable install for module resolution
│
├── data/
│   ├── raw/                    # Original source files — gitignored
│   └── processed/              # Intermediate cache — gitignored
│
├── docs/
│   └── images/
│       ├── architecture.png    # Pipeline architecture diagram
│       ├── data_model.png      # ERD / dimensional model diagram
│       └── screenshots/        # Dashboard page screenshots
│           ├── 01_landing.png
│           ├── 02_overview.png
│           ├── 03_agencies.png
│           ├── 04_departments.png
│           ├── 05_expense_classes.png
│           └── 06_programs.png
│
├── pipeline/
│   ├── __init__.py
│   ├── ingest.py               # Raw file ingestion into staging
│   ├── transform.py            # ETL, normalization, dimensional load
│   └── analytics.py            # Reusable query functions
│
├── db/
│   ├── __init__.py
│   ├── connection.py           # SQLAlchemy engine and session factory
│   ├── schema.py               # All table definitions via ORM
│   └── schema_init.py          # Table creation and static seed data
│
├── dashboard/
│   ├── app.py                  # Streamlit entry point and global styles
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── formatters.py       # Peso formatting and label helpers
│   │   └── charts.py           # Reusable Plotly chart functions
│   └── pages/
│       ├── 1_Overview.py
│       ├── 2_Agencies.py
│       ├── 3_Departments.py
│       ├── 4_Expense_Classes.py
│       └── 5_Programs.py
│
├── scripts/
│   ├── run_pipeline.py         # Orchestrates full ingestion + transformation
│   └── test_analytics.py       # Smoke test for all analytics functions
│
└── tests/
    ├── test_ingest.py
    └── test_transform.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15 or 18
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/credough/philgaa-analytics-pipeline.git
cd philgaa-analytics-pipeline
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Create the PostgreSQL Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE ph_gov_budget;
CREATE USER budget_user WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL ON SCHEMA public TO budget_user;
GRANT ALL PRIVILEGES ON DATABASE ph_gov_budget TO budget_user;
ALTER DATABASE ph_gov_budget OWNER TO budget_user;
\q
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ph_gov_budget
DB_USER=budget_user
DB_PASSWORD=your_password_here
```

### 6. Initialize the Database Schema

```bash
python -m db.schema_init
```

Expected output:
```
Database connection verified.
Creating tables...
Schema initialized successfully.
Static dimension data seeded.
```

### 7. Download the Source Data

Download the FY2021 GAA Excel file from the DBM website:

```
https://www.dbm.gov.ph/index.php/budget-documents/2021
```

Rename the file to `2021-GAA.xlsx` and place it in `data/raw/`:

```
data/
└── raw/
    └── 2021-GAA.xlsx
```

### 8. Run the Pipeline

```bash
python -m scripts.run_pipeline
```

Expected output:
```
Reading file: 2021-GAA.xlsx
Fiscal year: 2021
Raw rows read: 498,342
  Chunk 50/50: 498,342 rows inserted
Ingestion complete: 498,342 rows inserted.

Validation Report:
  total_rows: 498342
  null_agency_name: 0
  null_amt: 3206
  null_amt_pct: 0.64

--- Starting transformation for: 2021-GAA.xlsx ---
Unique agencies found: 375
Agency dimension records: 375
Unique object codes found: 361
Fact rows inserted: 498,342
--- Transformation complete ---
```

### 9. Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Navigate to `http://localhost:8501`

---

## Pipeline Walkthrough

### Ingestion (`pipeline/ingest.py`)

Reads the raw GAA Excel file, validates that all required columns are present, strips whitespace, replaces empty strings with NULL, adds pipeline metadata (`source_file`, `fiscal_year`, `is_processed`), and inserts rows into `stg_budget_allocations` in chunks of 10,000 rows. The staging table is a column-for-column mirror of the source file with no transformations applied.

Idempotency is enforced by deleting all existing rows for the source file before each load — re-running the pipeline produces identical results.

### Transformation (`pipeline/transform.py`)

Loads unprocessed staging rows, applies type coercion (string to numeric), converts amounts from thousands to actual pesos, standardizes text fields (uppercase codes, title-case names), maps expense class numeric codes to surrogate keys, resolves all dimensional foreign keys, and inserts into the fact table. Staging rows are marked `is_processed = TRUE` on completion.

### Analytics (`pipeline/analytics.py`)

Five parameterized query functions return pandas DataFrames. All functions accept `fiscal_year` as a parameter for forward compatibility with additional years of data. A central `_query` helper handles all SQL execution.

---


## Analytics and Dashboard

### Analytics Module

| Function | Description | Key Parameters |
|---|---|---|
| `total_budget_by_agency` | Top N agencies by appropriation with window-function rank | `fiscal_year`, `top_n` |
| `budget_by_expense_class` | PS/MOOE/CO/FE breakdown with percentage share | `fiscal_year` |
| `budget_by_department` | Department-level aggregation with agency count | `fiscal_year`, `top_n` |
| `top_programs_by_budget` | Top N programs with parent agency context | `fiscal_year`, `top_n` |
| `budget_summary_kpis` | Headline KPI dict composing results from other functions | `fiscal_year` |

### Dashboard Pages

| Page | Chart Types | Interactive Controls |
|---|---|---|
| Overview | KPI cards, donut chart | None |
| Agencies | Horizontal bar chart, data table | Top N slider (5–30) |
| Departments | Treemap, horizontal bar chart, data table | None |
| Expense Classes | Donut chart, horizontal bar chart, data table | None |
| Programs | Horizontal bar chart, data table | Top N slider (5–25) |

---

## Key Results

**Total FY2021 Authorized Appropriation: PHP 4.506 trillion**

Budget breakdown by expense class:

| Expense Class | Total (PHP) | Share |
|---|---|---|
| Maintenance and Other Operating Expenses | 1.74 trillion | 38.7% |
| Personnel Services | 1.30 trillion | 28.8% |
| Capital Outlay | 928.8 billion | 20.6% |
| Financial Expenses | 532.7 billion | 11.8% |

Top 5 agencies by appropriation:

| Rank | Agency | Department | Appropriation |
|---|---|---|---|
| 1 | Office Of The Secretary | DPWH | PHP 695.67B |
| 2 | Internal Revenue Allotment | Automatic Appropriations | PHP 695.49B |
| 3 | Office Of The Secretary | DepEd | PHP 594.11B |
| 4 | Debt Interest Payments | Automatic Appropriations | PHP 531.54B |
| 5 | Philippine National Police | DILG | PHP 191.47B |

---

## What This Demonstrates

| Skill | Implementation |
|---|---|
| Data ingestion engineering | Chunked insert, structural validation, idempotent staging |
| Data quality management | Null flagging, type coercion, source value preservation |
| Dimensional modeling | Kimball fact/dimension schema, surrogate keys, foreign key integrity |
| ETL pipeline design | Staged transformation, pipeline state tracking, lineage columns |
| Analytical SQL | Window functions, multi-table joins, aggregation across 498K rows |
| Python data engineering | Pandas, SQLAlchemy ORM, psycopg2, environment management |
| Data product delivery | Streamlit multi-page dashboard, Plotly interactive charts |
| Real data problem solving | Six documented data issues diagnosed and resolved on live data |

---

## Future Improvements

- Add FY2022 and FY2023 GAA data to enable year-over-year appropriation trend analysis
- Ingest DBM Budget Execution Reports to populate `obligations` and `disbursements` columns and compute actual `utilization_rate` and `disbursement_rate`
- Add PhilGEPS procurement contract data as a second fact table for procurement analytics
- Implement a full test suite covering ingestion validation, transformation logic, and analytics query output
- Add Docker Compose for one-command local deployment of PostgreSQL and the Streamlit dashboard
- Schedule pipeline runs with Apache Airflow or Prefect for automated data refresh

---

## License

MIT License. See `LICENSE` for details.

---

*Data source: Department of Budget and Management, Republic of the Philippines.
Republic Act No. 11518 — General Appropriations Act FY2021, Volume I-A.
All financial figures in Philippine Peso (PHP).*
