import re
from typing import Dict, Pattern

def compile_regex_patterns() -> Dict[str, Pattern]:
    '''
    Compile and return a dictionary of frequently used regex patterns.

    Returns:
        Dict[str, Pattern]: A dictionary mapping descriptive names to compiled regex patterns.
    '''
    patterns = {
        'bullet'                    : re.compile(r'(?:^|\s)-', re.MULTILINE),
        'page_reference'            : re.compile(r'(?<!#)\[\[(.+?)\]\]'),
        'tagged_backlink'           : re.compile(r'\#\[\[([^\]]+)\]\](?=\s+|\])'),
        'tag'                       : re.compile(r'\#(?!\[\[)(\w+)(?=\s+|\b])'),
        'property'                  : re.compile(r'^(?!\s*-\s)([A-Za-z0-9_-]+)(?=::)', re.MULTILINE),
        'asset'                     : re.compile(r'\.\./assets/(.*)'),
        'draw'                      : re.compile(r'(?<!#)\[\[draws/(.+?).excalidraw\]\]'),
        'external_link'             : re.compile(r'(?<!!)\[.*?\]\(.*?\)'),
        'external_link_internet'    : re.compile(r'(?<!!)\[.*?\]\(http.*?\)'),
        'external_link_alias'       : re.compile(r'(?<!!)\[.*?\]\([\[\[|\(\(].*?[\]\]|\)\)].*?\)'),
        'embedded_link'             : re.compile(r'!\[.*?\]\(.*\)'),
        'embedded_link_internet'    : re.compile(r'!\[.*?\]\(http.*\)'),
        'embedded_link_asset'       : re.compile(r'!\[.*?\]\(\.\./assets/.*\)'),
        'blockquote'                : re.compile(r'(?:^|\s)- >.*', re.MULTILINE),
        'flashcard'                 : re.compile(r'(?:^|\s)- .*\#card|\[\[card\]\].*', re.MULTILINE),
        'multiline_code_block'      : re.compile(r'```.*?```', re.DOTALL),
        'calc_block'                : re.compile(r'```calc.*?```', re.DOTALL),
        'multiline_code_lang'       : re.compile(r'```\w+.*?```', re.DOTALL),
        'reference'                 : re.compile(r'(?<!\{\{embed )\(\(.*?\)\)'),
        'block_reference'           : re.compile(r'(?<!\{\{embed )\(\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\)\)'),
        'embed'                     : re.compile(r'\{\{embed .*?\}\}'),
        'page_embed'                : re.compile(r'\{\{embed \[\[.*?\]\]\}\}'),
        'block_embed'               : re.compile(r'\{\{embed \(\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\)\)\}\}'),
        'namespace_queries'         : re.compile(r'\{\{namespace .*?\}\}'),
        'cloze'                     : re.compile(r'\{\{cloze .*?\}\}'),
        'simple_queries'            : re.compile(r'\{\{query .*?\}\}'),
        'query_functions'           : re.compile(r'\{\{function .*?\}\}'),
        'advanced_command'          : re.compile(r'\#\+BEGIN_.*\#\+END_.*', re.DOTALL),
    }
    return patterns