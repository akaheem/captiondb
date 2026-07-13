"""
Unit tests for the LocalStorageAdapter, demonstrating infrastructure testing.
"""
import pytest
from pathlib import Path
from app.infrastructure.storage.local import LocalStorageAdapter
from app.core.exceptions import StorageException


@pytest.mark.asyncio
async def test_local_storage_save_and_read(temp_storage_dir: Path):
    """Verifies the adapter can save and read bytes."""
    adapter = LocalStorageAdapter(base_path=str(temp_storage_dir))
    
    logical_path = "videos/test_vid.mp4"
    content = b"fake video bytes"
    
    saved_path = await adapter.save(logical_path, content)
    assert saved_path == logical_path
    
    retrieved_content = await adapter.read(logical_path)
    assert retrieved_content == content


@pytest.mark.asyncio
async def test_local_storage_path_traversal_prevention(temp_storage_dir: Path):
    """Verifies the adapter strictly prevents directory traversal attacks."""
    adapter = LocalStorageAdapter(base_path=str(temp_storage_dir))
    
    malicious_path = "../../../etc/passwd"
    
    with pytest.raises(StorageException, match="Path traversal attempt detected"):
        await adapter.save(malicious_path, b"hack")
