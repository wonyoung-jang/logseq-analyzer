"""Tests for LogseqFileSummarizer."""

import pytest

from logseq_analyzer.analysis.summarizers import LogseqFileSummarizer


@pytest.fixture
def logseq_file_summarizer() -> LogseqFileSummarizer:
    """Fixture for LogseqFileSummarizer instance."""
    return LogseqFileSummarizer()
