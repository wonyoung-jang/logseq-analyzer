"""
Enums for the Logseq Analyzer.
"""

from enum import Enum


class Config(Enum):
    """Configuration settings for the Logseq Analyzer."""


class Moved(Enum):
    """Moved files and directories in the Logseq Analyzer."""

    ASSETS = "moved_assets"
    RECYCLE = "moved_recycle"
    BAK = "moved_bak"


class Core(Enum):
    """Core components of the Logseq Analyzer."""

    FMT_TXT = ".txt"
    FMT_JSON = ".json"
    HLS_PREFIX = "hls__"
    NS_SEP = "/"
    NS_FILE_SEP_LEGACY = "%2F"
    NS_FILE_SEP_TRIPLE_LOWBAR = "___"


class Phase(Enum):
    """Phase of the application."""

    GUI_INSTANCE = "gui_instance"


class OutputDir(Enum):
    """Output directories for the Logseq Analyzer."""

    META = "_meta"
    JOURNALS = "journals"
    NAMESPACES = "namespaces"
    SUMMARY_FILES = "summary_files"
    SUMMARY_CONTENT = "summary_content"
    MOVED_FILES = "moved_files"
    TEST = "test"


class Output(Enum):
    """Output types for the Logseq Analyzer."""

    ALL_REFS = "all_linked_references"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
    COMPLETE_TIMELINE = "complete_timeline"
    CONFIG_DATA = "ls_config"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    DANGLING_JOURNALS = "dangling_journals"
    DANGLING_JOURNALS_FUTURE = "dangling_journals_future"
    DANGLING_JOURNALS_PAST = "dangling_journals_past"
    DANGLING_LINKS = "dangling_links"
    GRAPH_CONTENT = "content_bullets"
    GRAPH_DATA = "data"
    GRAPH_HASHED_FILES = "hash_to_file_map"
    GRAPH_NAMES_TO_HASHES = "name_to_hashes_map"
    UNIQUE_LINKED_REFERENCES = "unique_linked_references"
    UNIQUE_LINKED_REFERENCES_NS = "unique_linked_references_ns"
    MISSING_KEYS = "missing_keys"
    MOVED_FILES = "moved_files"
    NAMESPACE_DATA = "namespace_data"
    NAMESPACE_DETAILS = "namespace_details"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    NAMESPACE_PARTS = "namespace_parts"
    NAMESPACE_QUERIES = "namespace_queries"
    PROCESSED_KEYS = "processed_keys"
    TIMELINE_STATS = "timeline_stats"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"


class SummaryFiles(Enum):
    """Summary files for the Logseq Analyzer."""

    FILE_EXTS = "file_extensions_dict"
    FILETYPE_ASSET = "filetype_asset"
    FILETYPE_DRAW = "filetype_draw"
    FILETYPE_JOURNAL = "filetype_journal"
    FILETYPE_OTHER = "filetype_other"
    FILETYPE_PAGE = "filetype_page"
    FILETYPE_WHITEBOARD = "filetype_whiteboard"
    FILETYPE_SUB_ASSET = "filetype_sub_asset"
    FILETYPE_SUB_DRAW = "filetype_sub_draw"
    FILETYPE_SUB_JOURNAL = "filetype_sub_journal"
    FILETYPE_SUB_PAGE = "filetype_sub_page"
    FILETYPE_SUB_WHITEBOARD = "filetype_sub_whiteboard"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_HLS = "is_hls"
    IS_BACKLINKED = "is_backlinked"
    IS_BACKLINKED_BY_NS_ONLY = "is_backlinked_by_ns_only"
    NODE_BRANCH = "node_branch"
    NODE_LEAF = "node_leaf"
    NODE_ORPHAN_GRAPH = "node_orphan_graph"
    NODE_ORPHAN_NAMESPACE = "node_orphan_namespace"
    NODE_ORPHAN_NAMESPACE_TRUE = "node_orphan_namespace_true"
    NODE_ORPHAN_TRUE = "node_orphan_true"
    NODE_OTHER = "node_other"
    NODE_ROOT = "node_root"


class Criteria(Enum):
    """Criteria for filtering files."""

    ADVANCED_COMMANDS_CAUTION = "advanced_commands_caution"
    ADVANCED_COMMANDS_CENTER = "advanced_commands_center"
    ADVANCED_COMMANDS_COMMENT = "advanced_commands_comment"
    ADVANCED_COMMANDS_EXAMPLE = "advanced_commands_example"
    ADVANCED_COMMANDS_EXPORT_ASCII = "advanced_commands_export_ascii"
    ADVANCED_COMMANDS_EXPORT_LATEX = "advanced_commands_export_latex"
    ADVANCED_COMMANDS_EXPORT = "advanced_commands_export"
    ADVANCED_COMMANDS_IMPORTANT = "advanced_commands_important"
    ADVANCED_COMMANDS_NOTE = "advanced_commands_note"
    ADVANCED_COMMANDS_PINNED = "advanced_commands_pinned"
    ADVANCED_COMMANDS_QUERY = "advanced_commands_query"
    ADVANCED_COMMANDS_QUOTE = "advanced_commands_quote"
    ADVANCED_COMMANDS_TIP = "advanced_commands_tip"
    ADVANCED_COMMANDS_VERSE = "advanced_commands_verse"
    ADVANCED_COMMANDS_WARNING = "advanced_commands_warning"
    ADVANCED_COMMANDS = "advanced_commands"
    ALIASES = "aliases"
    ANY_LINKS = "any_links"
    ASSETS = "assets"
    BLOCK_EMBEDS = "block_embeds"
    BLOCK_REFERENCES = "block_references"
    BLOCKQUOTES = "blockquotes"
    CALC_BLOCKS = "calc_blocks"
    CARDS = "cards"
    CLOZES = "clozes"
    DRAWS = "draws"
    DYNAMIC_VARIABLES = "dynamic_variables"
    EMBED_TWITTER_TWEETS = "embed_twitter_tweets"
    EMBED_VIDEO_URLS = "embed_video_urls"
    EMBED_YOUTUBE_TIMESTAMPS = "embed_youtube_timestamps"
    EMBEDDED_LINKS_ASSET = "embedded_links_asset"
    EMBEDDED_LINKS_INTERNET = "embedded_links_internet"
    EMBEDDED_LINKS_OTHER = "embedded_links_other"
    EMBEDS = "embeds"
    EXTERNAL_LINKS_ALIAS = "external_links_alias"
    EXTERNAL_LINKS_INTERNET = "external_links_internet"
    EXTERNAL_LINKS_OTHER = "external_links_other"
    FLASHCARDS = "flashcards"
    INLINE_CODE_BLOCKS = "inline_code_blocks"
    MACROS = "macros"
    MULTILINE_CODE_BLOCKS = "multiline_code_blocks"
    MULTILINE_CODE_LANGS = "multiline_code_langs"
    NAMESPACE_QUERIES = "namespace_queries"
    PAGE_EMBEDS = "page_embeds"
    PAGE_REFERENCES = "page_references"
    PROPERTIES_BLOCK_BUILTIN = "properties_block_builtin"
    PROPERTIES_BLOCK_USER = "properties_block_user"
    PROPERTIES_PAGE_BUILTIN = "properties_page_builtin"
    PROPERTIES_PAGE_USER = "properties_page_user"
    PROPERTIES_VALUES = "properties_values"
    QUERY_FUNCTIONS = "query_functions"
    REFERENCES_GENERAL = "references_general"
    RENDERERS = "renderers"
    SIMPLE_QUERIES = "simple_queries"
    TAGGED_BACKLINKS = "tagged_backlinks"
    TAGS = "tags"
