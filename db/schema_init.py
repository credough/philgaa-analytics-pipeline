from db.connection import engine, verify_connection
from db import schema


def init_schema(drop_existing: bool = False) -> None:
    if not verify_connection():
        raise RuntimeError("Cannot initialize schema: database connection failed.")

    if drop_existing:
        print("Dropping all existing tables...")
        schema.Base.metadata.drop_all(bind=engine)

    print("Creating tables...")
    schema.Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Schema initialized successfully.")

    _seed_static_dimensions()


def _seed_static_dimensions() -> None:
    """
    Populate dimension tables whose values are known and stable.
    Expense classes do not change — seed them once here.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from db.connection import SessionLocal
    from db.schema import DimExpenseClass

    expense_classes = [
        {"expense_class_code": "PS",   "expense_class_name": "Personnel Services",
         "description": "Salaries, wages, and other compensation of government personnel"},
        {"expense_class_code": "MOOE", "expense_class_name": "Maintenance and Other Operating Expenses",
         "description": "Day-to-day operational costs excluding personnel"},
        {"expense_class_code": "CO",   "expense_class_name": "Capital Outlay",
         "description": "Expenditures for acquisition of long-term assets"},
        {"expense_class_code": "FE",   "expense_class_name": "Financial Expenses",
         "description": "Interest payments and bank charges"},
    ]

    with SessionLocal() as session:
        for ec in expense_classes:
            stmt = (
                pg_insert(DimExpenseClass)
                .values(**ec)
                .on_conflict_do_nothing(index_elements=["expense_class_code"])
            )
            session.execute(stmt)
        session.commit()

    print("Static dimension data seeded.")


if __name__ == "__main__":
    init_schema()