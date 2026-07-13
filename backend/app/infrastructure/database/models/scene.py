"""
Scene ORM Model.
"""
import uuid
from typing import List, Optional
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.infrastructure.database.base import Base


class SceneORM(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    
    seconds_start: Mapped[float] = mapped_column(Float)
    seconds_end: Mapped[float] = mapped_column(Float)
    
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Store string lists and simple dictionaries as JSONB
    tags: Mapped[list] = mapped_column(JSONB, server_default='[]')
    
    # AI Enrichment
    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    objects: Mapped[list] = mapped_column(JSONB, server_default='[]')
    activities: Mapped[list] = mapped_column(JSONB, server_default='[]')
    colors: Mapped[list] = mapped_column(JSONB, server_default='[]')
    ocr_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_metadata: Mapped[dict] = mapped_column(JSONB, server_default='{}')

    # Relationships
    video: Mapped["VideoORM"] = relationship("VideoORM", back_populates="scenes")
    captions: Mapped[List["CaptionORM"]] = relationship(
        "CaptionORM",
        back_populates="scene",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
