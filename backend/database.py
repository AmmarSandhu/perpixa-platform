import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------------------------------------
# DATABASE CONFIG
# -------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://perpixa:perpixa@localhost:5432/perpixa"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# -------------------------------------------------
# SESSION DEPENDENCY (FastAPI compatible)
# -------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
