"""
Tests for LogseqBullets class.
"""

from pathlib import Path
from tempfile import TemporaryFile
import pytest

from ..bullets import LogseqBullets


@pytest.fixture
def temp_file():
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"Test content")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_bullets(temp_file):
    """Fixture to create a LogseqBullets object using a temporary file."""
    bullet_obj = LogseqBullets(Path(temp_file))
    return bullet_obj


def test_logseq_bullets(logseq_bullets, temp_file):
    """Test the LogseqBullets functionality."""
    assert logseq_bullets.file_path == Path(temp_file)
    assert logseq_bullets.content == ""
    assert logseq_bullets.primary_bullet == ""
    assert logseq_bullets.stats.char_count == 0
    assert logseq_bullets.stats.bullet_count == 0
    assert logseq_bullets.stats.bullet_count_empty == 0
    assert logseq_bullets.stats.bullet_density == 0.0
    assert logseq_bullets.stats.has_page_properties is False
