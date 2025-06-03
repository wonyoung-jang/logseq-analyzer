"""
Tests for LogseqContentSummarizer
"""

import pytest

from ..summarizers import LogseqContentSummarizer


@pytest.fixture
def logseq_content_summarizer():
    return LogseqContentSummarizer()


def test_singleton(logseq_content_summarizer):
    another_instance = LogseqContentSummarizer()
    assert logseq_content_summarizer is another_instance
