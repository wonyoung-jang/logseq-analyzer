"""
Test the Criteria enum class.
"""

import pytest
from ..enums import Criteria


def test_criteria_values():
    expected = {
        "ADVANCED_COMMANDS_CAUTION": "advanced_commands_caution",
        "ADVANCED_COMMANDS_CENTER": "advanced_commands_center",
        "ADVANCED_COMMANDS_COMMENT": "advanced_commands_comment",
        "ADVANCED_COMMANDS_EXAMPLE": "advanced_commands_example",
        "ADVANCED_COMMANDS_EXPORT_ASCII": "advanced_commands_export_ascii",
        "ADVANCED_COMMANDS_EXPORT_LATEX": "advanced_commands_export_latex",
        "ADVANCED_COMMANDS_EXPORT": "advanced_commands_export",
        "ADVANCED_COMMANDS_IMPORTANT": "advanced_commands_important",
        "ADVANCED_COMMANDS_NOTE": "advanced_commands_note",
        "ADVANCED_COMMANDS_PINNED": "advanced_commands_pinned",
        "ADVANCED_COMMANDS_QUERY": "advanced_commands_query",
        "ADVANCED_COMMANDS_QUOTE": "advanced_commands_quote",
        "ADVANCED_COMMANDS_TIP": "advanced_commands_tip",
        "ADVANCED_COMMANDS_VERSE": "advanced_commands_verse",
        "ADVANCED_COMMANDS_WARNING": "advanced_commands_warning",
        "ADVANCED_COMMANDS": "advanced_commands",
        "ALIASES": "aliases",
        "ANY_LINKS": "any_links",
        "ASSETS": "assets",
        "BLOCK_EMBEDS": "block_embeds",
        "BLOCK_REFERENCES": "block_references",
        "BLOCKQUOTES": "blockquotes",
        "CALC_BLOCKS": "calc_blocks",
        "CARDS": "cards",
        "CLOZES": "clozes",
        "DRAWS": "draws",
        "DYNAMIC_VARIABLES": "dynamic_variables",
        "EMBED_TWITTER_TWEETS": "embed_twitter_tweets",
        "EMBED_VIDEO_URLS": "embed_video_urls",
        "EMBED_YOUTUBE_TIMESTAMPS": "embed_youtube_timestamps",
        "EMBEDDED_LINKS_ASSET": "embedded_links_asset",
        "EMBEDDED_LINKS_INTERNET": "embedded_links_internet",
        "EMBEDDED_LINKS_OTHER": "embedded_links_other",
        "EMBEDS": "embeds",
        "EXTERNAL_LINKS_ALIAS": "external_links_alias",
        "EXTERNAL_LINKS_INTERNET": "external_links_internet",
        "EXTERNAL_LINKS_OTHER": "external_links_other",
        "FLASHCARDS": "flashcards",
        "INLINE_CODE_BLOCKS": "inline_code_blocks",
        "MACROS": "macros",
        "MULTILINE_CODE_BLOCKS": "multiline_code_blocks",
        "MULTILINE_CODE_LANGS": "multiline_code_langs",
        "NAMESPACE_QUERIES": "namespace_queries",
        "PAGE_EMBEDS": "page_embeds",
        "PAGE_REFERENCES": "page_references",
        "PROPERTIES_BLOCK_BUILTIN": "properties_block_builtin",
        "PROPERTIES_BLOCK_USER": "properties_block_user",
        "PROPERTIES_PAGE_BUILTIN": "properties_page_builtin",
        "PROPERTIES_PAGE_USER": "properties_page_user",
        "PROPERTIES_VALUES": "properties_values",
        "QUERY_FUNCTIONS": "query_functions",
        "REFERENCES_GENERAL": "references_general",
        "RENDERERS": "renderers",
        "SIMPLE_QUERIES": "simple_queries",
        "TAGGED_BACKLINKS": "tagged_backlinks",
        "TAGS": "tags",
    }
    for member_name, string_value in expected.items():
        assert getattr(Criteria, member_name).value == string_value


def test_criteria_member_count():
    assert len(Criteria) == 56  # number of expected items in the enum
