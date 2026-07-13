"""
SQLAlchemy Declarative Base.
Strictly confined to infrastructure. Do NOT import into the Domain layer.
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Provides the core metadata registry for Alembic.
    """
    pass
