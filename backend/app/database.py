from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    from app.models import card  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
    _migrate_analysis_results()


def _migrate_analysis_results():
    """Add columns to analysis_results that may not exist in older DBs."""
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        existing = {col["name"] for col in inspect(engine).get_columns("analysis_results")}
        new_columns = [
            ("card_name",      "VARCHAR"),
            ("card_set",       "VARCHAR"),
            ("card_number",    "VARCHAR"),
            ("price_low",      "FLOAT"),
            ("price_mid",      "FLOAT"),
            ("price_high",     "FLOAT"),
            ("price_currency", "VARCHAR"),
        ]
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE analysis_results ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
