"""
Tests for LogseqContentSummarizer
"""

import pytest

from ..summarizers import LogseqContentSummarizer


@pytest.fixture
def logseq_content_summarizer():
    return LogseqContentSummarizer()
