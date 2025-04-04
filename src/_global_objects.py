"""
This module initializes global objects used throughout the application.
"""

PATTERNS, ANALYZER_CONFIG, ANALYZER, GRAPH_CONFIG, CACHE = (None, None, None, None, None)


def initialize_global_objects():
    """
    Initialize global objects for the application.
    Import locally to defer the resolution until after the module is fully loaded.
    """
    global PATTERNS, ANALYZER_CONFIG, ANALYZER, GRAPH_CONFIG, CACHE

    from .regex_patterns import RegexPatterns

    PATTERNS = RegexPatterns()

    from .logseq_analyzer_config import LogseqAnalyzerConfig

    ANALYZER_CONFIG = LogseqAnalyzerConfig()

    from .logseq_analyzer import LogseqAnalyzer

    ANALYZER = LogseqAnalyzer()  # Requires ANALYZER_CONFIG

    from .logseq_graph_config import LogseqGraphConfig

    GRAPH_CONFIG = LogseqGraphConfig()  # Requires ANALYZER_CONFIG

    from .cache import Cache

    CACHE = Cache(ANALYZER_CONFIG.get("CONSTANTS", "CACHE"))  # Requires ANALYZER_CONFIG, GRAPH_CONFIG


initialize_global_objects()
