import logging
import re
from typing import Dict, Pattern


def compile_regex_patterns() -> Dict[str, Pattern]:
    """
    Compile and return a dictionary of frequently used regex patterns.

    Returns:
        Dict[str, Pattern]: A dictionary mapping descriptive names to compiled regex patterns.
    """
    logging.info("Compiling regex patterns")
    patterns = {
        "bullet": re.compile(r"(?:^|\s)-", re.M | re.I),
        "page_reference": re.compile(r"(?<!#)\[\[(.+?)\]\]", re.I),
        "tagged_backlink": re.compile(r"\#\[\[([^\]]+)\]\](?=\s+|\])", re.I),
        "tag": re.compile(r"\#(?!\[\[)(\w+)(?=\s+|\b])", re.I),
        "property": re.compile(r"^(?!\s*-\s)([A-Za-z0-9_-]+)(?=::)", re.M | re.I),
        "asset": re.compile(r"\.\./assets/(.*)", re.I),
        "draw": re.compile(r"(?<!#)\[\[draws/(.+?).excalidraw\]\]", re.I),
        "external_link": re.compile(r"(?<!!)\[.*?\]\(.*?\)", re.I),
        "external_link_internet": re.compile(r"(?<!!)\[.*?\]\(http.*?\)", re.I),
        "external_link_alias": re.compile(r"(?<!!)\[.*?\]\([\[\[|\(\(].*?[\]\]|\)\)].*?\)", re.I),
        "embedded_link": re.compile(r"!\[.*?\]\(.*\)", re.I),
        "embedded_link_internet": re.compile(r"!\[.*?\]\(http.*\)", re.I),
        "embedded_link_asset": re.compile(r"!\[.*?\]\(\.\./assets/.*\)", re.I),
        "blockquote": re.compile(r"(?:^|\s)- >.*", re.M | re.I),
        "flashcard": re.compile(r"(?:^|\s)- .*\#card|\[\[card\]\].*", re.M | re.I),
        "multiline_code_block": re.compile(r"```.*?```", re.S | re.I),
        "calc_block": re.compile(r"```calc.*?```", re.S | re.I),
        "multiline_code_lang": re.compile(r"```\w+.*?```", re.S | re.I),
        "reference": re.compile(r"(?<!\{\{embed )\(\(.*?\)\)", re.I),
        "block_reference": re.compile(r"(?<!\{\{embed )\(\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\)\)", re.I),
        "embed": re.compile(r"\{\{embed .*?\}\}", re.I),
        "page_embed": re.compile(r"\{\{embed \[\[.*?\]\]\}\}", re.I),
        "block_embed": re.compile(r"\{\{embed \(\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\)\)\}\}", re.I),
        "namespace_queries": re.compile(r"\{\{namespace .*?\}\}", re.I),
        "cloze": re.compile(r"\{\{cloze .*?\}\}", re.I),
        "simple_queries": re.compile(r"\{\{query .*?\}\}", re.I),
        "query_functions": re.compile(r"\{\{function .*?\}\}", re.I),
        "advanced_command": re.compile(r"\#\+BEGIN_.*\#\+END_.*", re.S | re.I),
    }
    return patterns
