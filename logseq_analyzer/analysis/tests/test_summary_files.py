"""
Tests for LogseqFileSummarizer
"""

import pytest

from ..summarizers import LogseqFileSummarizer


@pytest.fixture
def logseq_file_summarizer():
    return LogseqFileSummarizer()
