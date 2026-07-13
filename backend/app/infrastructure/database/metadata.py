"""
Alembic Metadata Export.
Centralized location to gather all SQLAlchemy models for Alembic migrations.
"""
from app.infrastructure.database.base import Base

# Import all declarative models here so Alembic can discover them
from app.infrastructure.database.models import *

# Expose metadata for Alembic env.py
target_metadata = Base.metadata
