"""
Video ORM Model.
"""
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.infrastructure.database.base import Base


class VideoORM(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String)
    logical_path: Mapped[str] = mapped_column(String)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Embedded JSON mapping for VideoMetadata 
    # (Dimensions, format, codec, fps, etc.)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Flattened State mapping for high performance querying
    state_status: Mapped[str] = mapped_column(String(50), index=True)
    state_progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    state_current_stage: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state_error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    state_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    scenes: Mapped[List["SceneORM"]] = relationship(
        "SceneORM", 
        back_populates="video", 
        cascade="all, delete-orphan", 
        lazy="selectin"
    )
