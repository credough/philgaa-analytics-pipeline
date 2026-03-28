import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()


def get_connection_url() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([name, user, password]):
        raise EnvironmentError(
            "Missing required database environment variables. "
            "Check your .env file for DB_NAME, DB_USER, DB_PASSWORD."
        )

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(
    get_connection_url(),
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def verify_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection verified.")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False