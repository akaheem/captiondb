from sqlalchemy.schema import CreateTable
from app.infrastructure.database.models.video import VideoORM
from app.infrastructure.database.models.scene import SceneORM
from app.infrastructure.database.models.caption import CaptionORM

def test_metadata_compiles():
    """Verify SQLAlchemy mappings compile down to schemas without error."""
    assert CreateTable(VideoORM.__table__).compile()
    assert CreateTable(SceneORM.__table__).compile()
    assert CreateTable(CaptionORM.__table__).compile()

def test_relationship_bindings():
    """Verify relationships and foreign keys are intact."""
    assert "video_id" in SceneORM.__table__.c
    assert "scene_id" in CaptionORM.__table__.c
    
    # Ensure foreign keys are attached
    assert len(SceneORM.__table__.c.video_id.foreign_keys) == 1
    assert len(CaptionORM.__table__.c.scene_id.foreign_keys) == 1
