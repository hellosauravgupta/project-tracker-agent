"""
Module: database.py

This module configures the SQLAlchemy database connection engine, session factory,
and base declarative class. It provides the `SessionLocal` factory for dependency injection
in FastAPI routes, and `Base` as the declarative base for model definitions.

Attributes:
    engine (sqlalchemy.Engine): Database engine bound to the configured connection string.
    SessionLocal (sqlalchemy.orm.sessionmaker): Factory for creating new database sessions.
    Base (sqlalchemy.ext.declarative.api.Base): Declarative base used for defining ORM models.

"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .constant import DATABASE_URL

# ---------------------------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------------------------

# SQLAlchemy engine tied to the configured database URL.
# This sets up the core connection functionality for issuing queries.
engine = create_engine(DATABASE_URL)

# SessionLocal provides scoped sessions for each request/thread.
# autocommit and autoflush are disabled to give explicit control over
# transactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the declarative base class used to define ORM models.
Base = declarative_base()
