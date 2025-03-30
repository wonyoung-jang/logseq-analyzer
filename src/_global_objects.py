"""
This module initializes global objects used throughout the application.
"""

PATTERNS, CONFIG, ANALYZER, GRAPH, CACHE = (None,) * 5


def init_globals():
    """
    Initialize global objects for the application.
    Import locally to defer the resolution until after the module is fully loaded.
    """
    global PATTERNS, CONFIG, ANALYZER, GRAPH, CACHE

    from .compile_regex import RegexPatterns

    PATTERNS = RegexPatterns()

    from .config_loader import LogseqAnalyzerConfig

    CONFIG = LogseqAnalyzerConfig()

    from .logseq_analyzer import LogseqAnalyzer

    ANALYZER = LogseqAnalyzer()

    from .logseq_graph import LogseqGraph

    GRAPH = LogseqGraph()

    from .cache import Cache

    CACHE = Cache(CONFIG.get("CONSTANTS", "CACHE"))


init_globals()
