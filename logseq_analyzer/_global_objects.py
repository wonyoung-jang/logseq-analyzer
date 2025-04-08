"""
This module initializes global objects used throughout the application.
"""

from .regex_patterns import RegexPatterns
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .logseq_analyzer import LogseqAnalyzer
from .logseq_graph_config import LogseqGraphConfig
from .cache import Cache

PATTERNS = RegexPatterns()
ANALYZER_CONFIG = LogseqAnalyzerConfig()
ANALYZER = LogseqAnalyzer(ANALYZER_CONFIG)
GRAPH_CONFIG = LogseqGraphConfig(ANALYZER_CONFIG, ANALYZER)
CACHE = Cache(ANALYZER_CONFIG, GRAPH_CONFIG)
