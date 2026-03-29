from sqlalchemy import (
    Column, Integer, String, Numeric, Text,
    ForeignKey, DateTime, Boolean, Index,
    UniqueConstraint
)
from sqlalchemy.sql import func
from db.connection import Base


# ---------------------------------------------------------------------------
# STAGING LAYER
# Raw data lands here first — no transformations, minimal constraints.
# Column names mirror the source CSV headers as closely as possible.
# ---------------------------------------------------------------------------

class StagingBudgetAllocation(Base):
    __tablename__ = "stg_budget_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Source file metadata — critical for debugging and reprocessing
    source_file = Column(String(255), nullable=False)
    fiscal_year = Column(String(10))

    # Agency / department identifiers as they appear in the raw file
    department_code = Column(String(50))
    department_name = Column(Text)
    agency_code = Column(String(50))
    agency_name = Column(Text)

    # Program / project identifiers
    program_name = Column(Text)
    project_name = Column(Text)

    # Budget classification
    expense_class = Column(String(100))  # PS, MOOE, CO, etc.
    object_code = Column(String(50))
    object_name = Column(Text)

    # Financial figures — stored as Numeric for precision
    authorized_appropriation = Column(Numeric(20, 2))
    allotment = Column(Numeric(20, 2))
    obligations = Column(Numeric(20, 2))
    disbursements = Column(Numeric(20, 2))

    # Pipeline bookkeeping
    is_processed = Column(Boolean, default=False, nullable=False)
    loaded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_stg_budget_source_file", "source_file"),
        Index("ix_stg_budget_fiscal_year", "fiscal_year"),
        Index("ix_stg_budget_is_processed", "is_processed"),
    )


# ---------------------------------------------------------------------------
# DIMENSION TABLES
# Descriptive context for facts. Each has a surrogate key (integer PK)
# and a natural key (the original code from the source) for deduplication.
# ---------------------------------------------------------------------------

class DimAgency(Base):
    __tablename__ = "dim_agency"

    agency_id = Column(Integer, primary_key=True, autoincrement=True)

    # Natural keys from source — used for deduplication on upsert
    department_code = Column(String(50))
    department_name = Column(Text)
    agency_code = Column(String(50))
    agency_name = Column(Text, nullable=False)

    # Derived grouping — assigned during transformation
    sector = Column(String(100))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("department_code", "agency_code", name="uq_agency_dept_code"),
        Index("ix_dim_agency_code", "agency_code"),
    )


class DimExpenseClass(Base):
    __tablename__ = "dim_expense_class"

    expense_class_id = Column(Integer, primary_key=True, autoincrement=True)
    expense_class_code = Column(String(20), nullable=False, unique=True)
    expense_class_name = Column(String(100), nullable=False)
    description = Column(Text)

    # PS = Personnel Services
    # MOOE = Maintenance and Other Operating Expenses
    # CO = Capital Outlay
    # FE = Financial Expenses


class DimObjectCode(Base):
    __tablename__ = "dim_object_code"

    object_code_id = Column(Integer, primary_key=True, autoincrement=True)
    object_code = Column(String(50), nullable=False)
    object_name = Column(Text)
    expense_class_id = Column(Integer, ForeignKey("dim_expense_class.expense_class_id"))

    __table_args__ = (
        UniqueConstraint("object_code", name="uq_object_code"),
        Index("ix_dim_object_code", "object_code"),
    )


class DimFiscalYear(Base):
    __tablename__ = "dim_fiscal_year"

    fiscal_year_id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year = Column(Integer, nullable=False, unique=True)
    label = Column(String(20))          # e.g. "FY2022"
    is_current = Column(Boolean, default=False)
    start_date = Column(String(10))     # "YYYY-01-01"
    end_date = Column(String(10))       # "YYYY-12-31"


# ---------------------------------------------------------------------------
# FACT TABLE
# One row per measurable budget event.
# All foreign keys reference dimension tables — no raw strings here.
# Financial columns use Numeric(20, 2) to avoid floating point errors.
# ---------------------------------------------------------------------------

class FactBudgetAllocation(Base):
    __tablename__ = "fact_budget_allocation"

    allocation_id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys to dimensions
    agency_id = Column(
        Integer,
        ForeignKey("dim_agency.agency_id", ondelete="RESTRICT"),
        nullable=False
    )
    fiscal_year_id = Column(
        Integer,
        ForeignKey("dim_fiscal_year.fiscal_year_id", ondelete="RESTRICT"),
        nullable=False
    )
    expense_class_id = Column(
        Integer,
        ForeignKey("dim_expense_class.expense_class_id", ondelete="RESTRICT")
    )
    object_code_id = Column(
        Integer,
        ForeignKey("dim_object_code.object_code_id", ondelete="RESTRICT")
    )

    # Program / project descriptor (denormalized intentionally — low cardinality)
    program_name = Column(Text)
    project_name = Column(Text)

    # The four core budget execution measures
    authorized_appropriation = Column(Numeric(20, 2), default=0)
    allotment = Column(Numeric(20, 2), default=0)
    obligations = Column(Numeric(20, 2), default=0)
    disbursements = Column(Numeric(20, 2), default=0)

    # Derived measures — computed during transformation, stored for query speed
    utilization_rate = Column(Numeric(8, 4))    # obligations / appropriation
    disbursement_rate = Column(Numeric(8, 4))   # disbursements / obligations

    # Lineage — which staging row produced this fact
    source_staging_id = Column(Integer, ForeignKey("stg_budget_allocations.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_fact_agency_id", "agency_id"),
        Index("ix_fact_fiscal_year_id", "fiscal_year_id"),
        Index("ix_fact_expense_class_id", "expense_class_id"),
        # Composite index for the most common analytical query pattern
        Index("ix_fact_agency_year", "agency_id", "fiscal_year_id"),
    )