from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup / from a migration script."""
    from .models import (  # noqa: F401  (import so Base.metadata knows about them)
        user, business, dataset, business_data, simulation, insight, notification,
    )
    Base.metadata.create_all(bind=engine)

    # Lightweight backward-compatible migration for existing PostgreSQL installs.
    # create_all() does not add newly introduced columns to existing tables.
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("business_data")}
    if "dataset_id" not in columns:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE business_data ADD COLUMN dataset_id INTEGER "
                "REFERENCES datasets(id) ON DELETE CASCADE"
            ))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_business_data_dataset_id ON business_data(dataset_id)"))
