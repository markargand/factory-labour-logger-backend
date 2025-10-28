# database.py
# Provides a SQLAlchemy Session (get_db) using the DATABASE_URL env var.
# Works on Render with psycopg3.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Expect DATABASE_URL to be set in Render, e.g.:
# postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Helpful message if env var is missing
    raise RuntimeError("DATABASE_URL is not set. Add it in Render → Environment.")

# Create engine and session factory
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # avoid stale connections
    future=True          # SQLAlchemy 2.0 style
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
