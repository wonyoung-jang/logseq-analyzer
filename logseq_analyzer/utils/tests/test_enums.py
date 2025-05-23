"""
Test the Criteria enum class.
"""

from ..enums import (
    Constants,
    Format,
    Core,
    Output,
    SummaryFiles,
    Criteria,
    OutputDir,
    Moved,
    Arguments,
    Nodes,
    FileTypes,
    Config,
)


# Constants
def test_constants_values():
    expected = {
        "CONFIG_INI_FILE": "logseq_analyzer/config/configuration/config.ini",
        "CONFIG_USER_INI_FILE": "logseq_analyzer/config/configuration/user_config.ini",
        "CACHE_FILE": "logseq-analyzer-cache",
        "OUTPUT_DIR": "logseq-analyzer-output",
        "LOG_FILE": "logseq-analyzer-output/logseq_analyzer.log",
        "TO_DELETE_DIR": "to-delete",
        "TO_DELETE_BAK_DIR": "to-delete/bak",
        "TO_DELETE_RECYCLE_DIR": "to-delete/.recycle",
        "TO_DELETE_ASSETS_DIR": "to-delete/assets",
    }
    for member_name, string_value in expected.items():
        assert getattr(Constants, member_name).value == string_value


def test_constants_member_count():
    assert len(Constants) == 9


# Format
def test_format_values():
    expected = {
        "TXT": ".txt",
        "JSON": ".json",
        "CSV": ".csv",
        "TSV": ".tsv",
        "HTML": ".html",
        "MD": ".md",
        "PNG": ".png",
        "JPG": ".jpg",
        "JPEG": ".jpeg",
        "GIF": ".gif",
        "SVG": ".svg",
        "ORG": ".org",
    }
    for member_name, string_value in expected.items():
        assert getattr(Format, member_name).value == string_value


def test_format_member_count():
    assert len(Format) == 12


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
        "DATE_ORDINAL_SUFFIX": "o",
        "HLS_PREFIX": "hls__",
        "NS_SEP": "/",
        "NS_FILE_SEP_LEGACY": "%2F",
        "NS_FILE_SEP_TRIPLE_LOWBAR": "___",
        "NS_CONFIG_LEGACY": ":legacy",
        "NS_CONFIG_TRIPLE_LOWBAR": ":triple-lowbar",
    }
    for member_name, string_value in expected.items():
        assert getattr(Core, member_name).value == string_value


def test_core_member_count():
    assert len(Core) == 7


# Output
def test_output_values():
    expected = {
        "ALL_LINKED_REFERENCES": "all_linked_references",
        "ALL_DANGLING_LINKS": "all_dangling_links",
        "ASSETS_BACKLINKED": "assets_backlinked",
        "ASSETS_NOT_BACKLINKED": "assets_not_backlinked",
        "COMPLETE_TIMELINE": "complete_timeline",
        "CONFIG_MERGED": "config_merged",
        "CONFIG_USER": "config_user",
        "CONFIG_GLOBAL": "config_global",
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
        "HLS_ASSET_MAPPING": "hls_asset_mapping",
        "HLS_ASSET_NAMES": "hls_asset_names",
        "HLS_FORMATTED_BULLETS": "hls_formatted_bullets",
        "HLS_NOT_BACKLINKED": "hls_not_backlinked",
        "HLS_BACKLINKED": "hls_backlinked",
        "NAME_TO_FILES": "name_to_files",
        "UNIQUE_LINKED_REFERENCES": "unique_linked_references",
        "UNIQUE_LINKED_REFERENCES_NS": "unique_linked_references_ns",
        "MISSING_KEYS": "missing_keys",
        "MOD_TRACKER": "mod_tracker",
        "MOVED_FILES": "moved_files",
        "NAMESPACE_DATA": "namespace_data",
        "NAMESPACE_DETAILS": "namespace_details",
        "NAMESPACE_HIERARCHY": "namespace_hierarchy",
        "NAMESPACE_PARTS": "namespace_parts",
        "NAMESPACE_QUERIES": "namespace_queries",
        "PATH_TO_FILE": "path_to_file",
        "PROCESSED_KEYS": "processed_keys",
        "TIMELINE_STATS": "timeline_stats",
        "UNIQUE_NAMESPACE_PARTS": "unique_namespace_parts",
        "UNIQUE_NAMESPACES_PER_LEVEL": "unique_namespaces_per_level",
    }
    for member_name, string_value in expected.items():
        assert getattr(Output, member_name).value == string_value


def test_output_member_count():
    assert len(Output) == 41


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
        "ADV_CMD_CAUTION": "adv_cmd_caution",
        "ADV_CMD_CENTER": "adv_cmd_center",
        "ADV_CMD_COMMENT": "adv_cmd_comment",
        "ADV_CMD_EXAMPLE": "adv_cmd_example",
        "ADV_CMD_EXPORT_ASCII": "adv_cmd_export_ascii",
        "ADV_CMD_EXPORT_LATEX": "adv_cmd_export_latex",
        "ADV_CMD_EXPORT": "adv_cmd_export",
        "ADV_CMD_IMPORTANT": "adv_cmd_important",
        "ADV_CMD_NOTE": "adv_cmd_note",
        "ADV_CMD_PINNED": "adv_cmd_pinned",
        "ADV_CMD_QUERY": "adv_cmd_query",
        "ADV_CMD_QUOTE": "adv_cmd_quote",
        "ADV_CMD_TIP": "adv_cmd_tip",
        "ADV_CMD_VERSE": "adv_cmd_verse",
        "ADV_CMD_WARNING": "adv_cmd_warning",
        "ADV_CMD": "adv_cmd",
        "ALIASES": "aliases",
        "ANY_LINKS": "any_links",
        "ASSETS": "assets",
        "BOLD": "bold",
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
    assert len(Criteria) == 57


def test_args_values():
    expected = {
        "GRAPH_FOLDER": "graph_folder",
        "GLOBAL_CONFIG": "global_config",
        "MOVE_ALL": "move_all",
        "MOVE_UNLINKED_ASSETS": "move_unlinked_assets",
        "MOVE_BAK": "move_bak",
        "MOVE_RECYCLE": "move_recycle",
        "WRITE_GRAPH": "write_graph",
        "GRAPH_CACHE": "graph_cache",
        "REPORT_FORMAT": "report_format",
        "GEOMETRY": "geometry",
    }
    for member_name, string_value in expected.items():
        assert getattr(Arguments, member_name).value == string_value


def test_args_member_count():
    assert len(Arguments) == 10


def test_nodes_values():
    expected = {
        "BRANCH": "branch",
        "LEAF": "leaf",
        "ROOT": "root",
        "ORPHAN_GRAPH": "orphan_graph",
        "ORPHAN_NAMESPACE": "orphan_namespace",
        "ORPHAN_NAMESPACE_TRUE": "orphan_namespace_true",
        "ORPHAN_TRUE": "orphan_true",
        "OTHER": "other",
    }
    for member_name, string_value in expected.items():
        assert getattr(Nodes, member_name).value == string_value


def test_nodes_member_count():
    assert len(Nodes) == 8


def test_file_types_values():
    expected = {
        "ASSET": "asset",
        "DRAW": "draw",
        "JOURNAL": "journal",
        "PAGE": "page",
        "WHITEBOARD": "whiteboard",
        "SUB_ASSET": "sub_asset",
        "SUB_DRAW": "sub_draw",
        "SUB_JOURNAL": "sub_journal",
        "SUB_PAGE": "sub_page",
        "SUB_WHITEBOARD": "sub_whiteboard",
        "OTHER": "other",
    }
    for member_name, string_value in expected.items():
        assert getattr(FileTypes, member_name).value == string_value


def test_file_types_member_count():
    assert len(FileTypes) == 11


def test_config_values():
    expected = {
        "DIR_ASSETS": "DIR_ASSETS",
        "DIR_DRAWS": "DIR_DRAWS",
        "DIR_JOURNALS": "DIR_JOURNALS",
        "DIR_PAGES": "DIR_PAGES",
        "DIR_WHITEBOARDS": "DIR_WHITEBOARDS",
        "DIR_BAK": "DIR_BAK",
        "DIR_RECYCLE": "DIR_RECYCLE",
    }
    for member_name, string_value in expected.items():
        assert getattr(Config, member_name).value == string_value


def test_config_member_count():
    assert len(Config) == 7
