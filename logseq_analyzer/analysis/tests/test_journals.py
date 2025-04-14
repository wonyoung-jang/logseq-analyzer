"""
Tests for LogseqJournals
"""

import pytest

from ..journals import LogseqJournals


@pytest.fixture
def logseq_journals():
    return LogseqJournals()


# TODO Fix this test
@pytest.mark.skip(reason="Need to fix keyerror")
def test_singleton(logseq_journals):
    another_instance = LogseqJournals()
    assert logseq_journals is another_instance
