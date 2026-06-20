# =============================================================================
# database.py
# -----------------------------------------------------------------------------
# This file sets up our database connection using SQLAlchemy (an ORM, which
# means we can talk to the database using Python objects instead of raw SQL).
# We use SQLite, which stores the whole database in a single file (reviews.db).
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# -----------------------------------------------------------------------------
# Where the SQLite database file lives.
# We build an absolute path so it works the same locally and on Render.
# -----------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "reviews.db")

# -----------------------------------------------------------------------------
# The "engine" is the core connection to the database.
# check_same_thread=False is needed so Flask (which can use multiple threads)
# is allowed to share the SQLite connection.
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# -----------------------------------------------------------------------------
# SessionLocal is a "factory" that creates new database sessions.
# A session is like a temporary workspace where we add/query/delete rows,
# then commit (save) the changes.
# -----------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------------------------------------------------------
# Base is the parent class that all of our database models inherit from.
# SQLAlchemy uses it to keep track of every table we define.
# -----------------------------------------------------------------------------
Base = declarative_base()


def init_db():
    """Create all database tables (only creates them if they don't exist yet)."""
    # Import models here so SQLAlchemy knows about every table before creating.
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
