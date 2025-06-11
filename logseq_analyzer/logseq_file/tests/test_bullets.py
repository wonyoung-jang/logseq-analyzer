"""
Tests for LogseqBullets class.
"""

import pytest

from ..bullets import LogseqBullets


@pytest.fixture
def logseq_bullets() -> LogseqBullets:
    """Fixture to create a LogseqBullets object using a temporary file."""
    bullet_obj = LogseqBullets("")
    return bullet_obj


def test_logseq_bullets(logseq_bullets) -> None:
    """Test the LogseqBullets functionality."""
    assert logseq_bullets.all_bullets == []
    assert logseq_bullets.content == ""
    assert logseq_bullets.primary == ""
