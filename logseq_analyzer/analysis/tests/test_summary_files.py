"""
Tests for LogseqFileSummarizer
"""

import pytest

from ..summary_files import LogseqFileSummarizer


@pytest.fixture
def logseq_file_summarizer():
    return LogseqFileSummarizer()


def test_singleton(logseq_file_summarizer):
    another_instance = LogseqFileSummarizer()
    assert logseq_file_summarizer is another_instance
