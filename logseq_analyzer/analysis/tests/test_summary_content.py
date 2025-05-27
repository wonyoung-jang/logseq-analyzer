"""
Tests for LogseqContentSummarizer
"""

import pytest

from ..index import FileIndex
from ..summary_content import LogseqContentSummarizer


@pytest.fixture
def logseq_content_summarizer():
    return LogseqContentSummarizer(FileIndex())


def test_singleton(logseq_content_summarizer):
    another_instance = LogseqContentSummarizer(FileIndex())
    assert logseq_content_summarizer is another_instance
