"""
Test the Criteria enum class.
"""

import pytest
from ..enums import Core, Phase, Output, SummaryFiles, Criteria, OutputDir, Moved


# Moved
def test_moved_values():
    expected = {
        "ASSETS": "moved_assets",
        "RECYCLE": "moved_recycle",
        "BAK": "moved_bak",
    }
    for member_name, string_value in expected.items():
        assert getattr(Moved, member_name).value == string_value


def test_moved_member_count():
    assert len(Moved) == 3


# OutputDir
def test_output_dir_values():
    expected = {
        "META": "_meta",
        "JOURNALS": "journals",
        "NAMESPACES": "namespaces",
        "SUMMARY_FILES": "summary_files",
        "SUMMARY_CONTENT": "summary_content",
        "MOVED_FILES": "moved_files",
        "TEST": "test",
    }
    for member_name, string_value in expected.items():
        assert getattr(OutputDir, member_name).value == string_value


def test_output_dir_member_count():
    assert len(OutputDir) == 7


# Core
def test_core_values():
    expected = {
        "FMT_TXT": ".txt",
        "FMT_JSON": ".json",
        "HLS_PREFIX": "hls__",
        "NS_SEP": "/",
        "NS_FILE_SEP_LEGACY": "%2F",
        "NS_FILE_SEP_TRIPLE_LOWBAR": "___",
    }
    for member_name, string_value in expected.items():
        assert getattr(Core, member_name).value == string_value


def test_core_member_count():
    assert len(Core) == 6


# Phase
def test_phase_values():
    expected = {
        "GUI_INSTANCE": "gui_instance",
    }
    for member_name, string_value in expected.items():
        assert getattr(Phase, member_name).value == string_value


def test_phase_member_count():
    assert len(Phase) == 1


# Output
def test_output_values():
    expected = {
        "ALL_REFS": "all_linked_references",
        "ASSETS_BACKLINKED": "assets_backlinked",
        "ASSETS_NOT_BACKLINKED": "assets_not_backlinked",
        "COMPLETE_TIMELINE": "complete_timeline",
        "CONFIG_DATA": "ls_config",
        "CONFLICTS_DANGLING": "conflicts_dangling",
        "CONFLICTS_NON_NAMESPACE": "conflicts_non_namespace",
        "CONFLICTS_PARENT_DEPTH": "conflicts_parent_depth",
        "CONFLICTS_PARENT_UNIQUE": "conflicts_parent_unique",
        "DANGLING_JOURNALS": "dangling_journals",
        "DANGLING_JOURNALS_FUTURE": "dangling_journals_future",
        "DANGLING_JOURNALS_PAST": "dangling_journals_past",
        "DANGLING_LINKS": "dangling_links",
        "GRAPH_CONTENT": "content_bullets",
        "GRAPH_DATA": "data",
        "FILES": "files",
        "HASH_TO_FILE": "hash_to_file",
        "NAME_TO_FILES": "name_to_files",
        "UNIQUE_LINKED_REFERENCES": "unique_linked_references",
        "UNIQUE_LINKED_REFERENCES_NS": "unique_linked_references_ns",
        "MISSING_KEYS": "missing_keys",
        "MOVED_FILES": "moved_files",
        "NAMESPACE_DATA": "namespace_data",
        "NAMESPACE_DETAILS": "namespace_details",
        "NAMESPACE_HIERARCHY": "namespace_hierarchy",
        "NAMESPACE_PARTS": "namespace_parts",
        "NAMESPACE_QUERIES": "namespace_queries",
        "PROCESSED_KEYS": "processed_keys",
        "TIMELINE_STATS": "timeline_stats",
        "UNIQUE_NAMESPACE_PARTS": "unique_namespace_parts",
        "UNIQUE_NAMESPACES_PER_LEVEL": "unique_namespaces_per_level",
    }
    for member_name, string_value in expected.items():
        assert getattr(Output, member_name).value == string_value


def test_output_member_count():
    assert len(Output) == 31


# SummaryFiles
def test_summary_files_values():
    expected = {
        "FILE_EXTS": "file_extensions_dict",
        "FILETYPE_ASSET": "filetype_asset",
        "FILETYPE_DRAW": "filetype_draw",
        "FILETYPE_JOURNAL": "filetype_journal",
        "FILETYPE_PAGE": "filetype_page",
        "FILETYPE_WHITEBOARD": "filetype_whiteboard",
        "FILETYPE_SUB_ASSET": "filetype_sub_asset",
        "FILETYPE_SUB_DRAW": "filetype_sub_draw",
        "FILETYPE_SUB_JOURNAL": "filetype_sub_journal",
        "FILETYPE_SUB_PAGE": "filetype_sub_page",
        "FILETYPE_SUB_WHITEBOARD": "filetype_sub_whiteboard",
        "FILETYPE_OTHER": "filetype_other",
        "HAS_BACKLINKS": "has_backlinks",
        "HAS_CONTENT": "has_content",
        "IS_BACKLINKED": "is_backlinked",
        "IS_BACKLINKED_BY_NS_ONLY": "is_backlinked_by_ns_only",
        "IS_HLS": "is_hls",
        "NODE_BRANCH": "node_branch",
        "NODE_LEAF": "node_leaf",
        "NODE_ORPHAN_GRAPH": "node_orphan_graph",
        "NODE_ORPHAN_NAMESPACE": "node_orphan_namespace",
        "NODE_ORPHAN_NAMESPACE_TRUE": "node_orphan_namespace_true",
        "NODE_ORPHAN_TRUE": "node_orphan_true",
        "NODE_OTHER": "node_other",
        "NODE_ROOT": "node_root",
    }
    for member_name, string_value in expected.items():
        assert getattr(SummaryFiles, member_name).value == string_value


def test_summary_files_member_count():
    assert len(SummaryFiles) == 25


# Criteria
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
    assert len(Criteria) == 56
