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
    PATTERNS.compile_re_content()
    PATTERNS.compile_re_content_double_curly_brackets()
    PATTERNS.compile_re_content_advanced_command()
    PATTERNS.compile_re_config()

    from .logseq_analyzer_config import LogseqAnalyzerConfig

    ANALYZER_CONFIG = LogseqAnalyzerConfig()
    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.get_built_in_properties()
    ANALYZER_CONFIG.get_datetime_token_map()
    ANALYZER_CONFIG.get_datetime_token_pattern()

    from .logseq_analyzer import LogseqAnalyzer

    ANALYZER = LogseqAnalyzer()  # Requires ANALYZER_CONFIG

    from .logseq_graph_config import LogseqGraphConfig

    GRAPH_CONFIG = LogseqGraphConfig()  # Requires ANALYZER_CONFIG

    from .cache import Cache

    CACHE = Cache(ANALYZER_CONFIG.get("CONSTANTS", "CACHE"))  # Requires ANALYZER_CONFIG, GRAPH_CONFIG


initialize_global_objects()
