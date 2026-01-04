"""Tests for LogseqContentSummarizer."""

import pytest

from logseq_analyzer.analysis.summarizers import LogseqContentSummarizer


@pytest.fixture
def logseq_content_summarizer() -> LogseqContentSummarizer:
    """Fixture for LogseqContentSummarizer instance."""
    return LogseqContentSummarizer()
