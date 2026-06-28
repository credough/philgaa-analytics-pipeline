# PhilGAA Analytics Pipeline
### Data Engineering and Interactive Analysis of the Philippine FY2021 General Appropriations Act

**Final Project Documentation**
BSIT 2-2N — Group 4

> An end-to-end data pipeline built on real Philippine government budget data from the FY2021 General Appropriations Act (GAA), published by the Department of Budget and Management (DBM). The pipeline ingests 498,342 raw budget line items, models a Kimball-style dimensional warehouse in PostgreSQL, and serves budget intelligence through an interactive multi-page Streamlit dashboard.

| | |
|---|---|
| Celindro, Aaron Creed P. | Nepomuceno, Jadelyn Lara G. |
| De Jesus, Johnelle Mae G. | Patungan, Jose Manuel L. |
| Enate, Therese Mykaela V. | Sampiano, Jed Marcuz I. |
| Fernan, Liam Andrei A. | |
| Figuracion, Lowell Stephen D. | |
| Gemoya, Kurt L. | |

**Submitted to:** Ms. Rachel A. Nayre
**Date Submitted:** June 28, 2026

---

## Prerequisites

- Python 3.11+
- PostgreSQL 15 or 18
- Git

---

## Setup

### 1. Download the ZIP file and Open in VS Code or any other software


### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Create the PostgreSQL database

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

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ph_gov_budget
DB_USER=budget_user
DB_PASSWORD=your_password_here
```

### 6. Initialize the database schema

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

### 7. Download the source data

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

---

## Running the Pipeline

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

---

## Launching the Dashboard

```bash
streamlit run dashboard/app.py
```

Navigate to `http://localhost:8501`

---

## License

MIT License. See `LICENSE` for details.

---

*Data source: Department of Budget and Management, Republic of the Philippines.
Republic Act No. 11518 — General Appropriations Act FY2021, Volume I-A.
All financial figures in Philippine Peso (PHP).*