"""
Caption ORM Model.
"""
import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.base import Base


class CaptionORM(Base):
    __tablename__ = "captions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    tone: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(String)

    # Relationships
    scene: Mapped["SceneORM"] = relationship("SceneORM", back_populates="captions")
