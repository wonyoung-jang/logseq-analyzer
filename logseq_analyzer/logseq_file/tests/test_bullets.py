"""
Tests for LogseqBullets class.
"""

import pytest

from ..bullets import LogseqBullets


@pytest.fixture
def logseq_bullets():
    """Fixture to create a LogseqBullets object using a temporary file."""
    bullet_obj = LogseqBullets()
    return bullet_obj


def test_logseq_bullets(logseq_bullets):
    """Test the LogseqBullets functionality."""
    assert logseq_bullets.all_bullets == []
    assert logseq_bullets.content == ""
    assert logseq_bullets.primary == ""
    assert logseq_bullets.has_page_properties is False
    assert logseq_bullets.stats.char_count == 0
    assert logseq_bullets.stats.bullet_count == 0
    assert logseq_bullets.stats.bullet_count_empty == 0
    assert logseq_bullets.stats.bullet_density == 0.0
