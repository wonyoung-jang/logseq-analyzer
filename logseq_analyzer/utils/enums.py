"""
Enums for the Logseq Analyzer.
"""

from enum import StrEnum

__all__ = [
    "ConfigEdnReport",
    "Constant",
    "Core",
    "Criteria",
    "Edn",
    "FileType",
    "Format",
    "LogseqGraphStructure",
    "Moved",
    "Node",
    "Output",
    "OutputDir",
    "TargetDir",
]


class ConfigEdnReport(StrEnum):
    """Configuration EDN reports for the Logseq Analyzer."""

    CONFIG_EDN = "config_edns"
    EDN_DEFAULT = "edn_default"
    EDN_USER = "edn_user"
    EDN_GLOBAL = "edn_global"
    EDN_CONFIG = "edn_config"


class Constant(StrEnum):
    """Constants used in the Logseq Analyzer."""

    CACHE_FILE = "logseq-analyzer-cache"
    LOG_FILE = "logseq_analyzer.log"
    OUTPUT_DIR = "logseq-analyzer-output"
    TO_DELETE_ASSETS_DIR = "to-delete/assets"
    TO_DELETE_BAK_DIR = "to-delete/bak"
    TO_DELETE_DIR = "to-delete"
    TO_DELETE_RECYCLE_DIR = "to-delete/.recycle"


class Core(StrEnum):
    """Core components of the Logseq Analyzer."""

    DATE_ORDINAL_SUFFIX = "o"
    HLS_PREFIX = "hls__"
    NS_CONFIG_LEGACY = ":legacy"
    NS_CONFIG_TRIPLE_LOWBAR = ":triple-lowbar"
    NS_FILE_SEP_LEGACY = "%2F"
    NS_FILE_SEP_TRIPLE_LOWBAR = "___"
    NS_SEP = "/"


class Criteria(StrEnum):
    """Criteria for filtering files."""

    ADV_CMD = "adv_cmd"
    ADV_CMD_CAUTION = "adv_cmd_caution"
    ADV_CMD_CENTER = "adv_cmd_center"
    ADV_CMD_COMMENT = "adv_cmd_comment"
    ADV_CMD_EXAMPLE = "adv_cmd_example"
    ADV_CMD_EXPORT = "adv_cmd_export"
    ADV_CMD_EXPORT_ASCII = "adv_cmd_export_ascii"
    ADV_CMD_EXPORT_LATEX = "adv_cmd_export_latex"
    ADV_CMD_IMPORTANT = "adv_cmd_important"
    ADV_CMD_NOTE = "adv_cmd_note"
    ADV_CMD_PINNED = "adv_cmd_pinned"
    ADV_CMD_QUERY = "adv_cmd_query"
    ADV_CMD_QUOTE = "adv_cmd_quote"
    ADV_CMD_TIP = "adv_cmd_tip"
    ADV_CMD_VERSE = "adv_cmd_verse"
    ADV_CMD_WARNING = "adv_cmd_warning"
    COD_INLINE = "code_inline"
    COD_ML_ALL = "code_multiline"
    COD_ML_CALC = "code_multiline_calc"
    COD_ML_LANG = "code_multiline_lang"
    CON_ALIASES = "content_aliases"
    CON_ANY_LINKS = "content_any_links"
    CON_ASSETS = "content_assets"
    CON_BLOCKQUOTES = "content_blockquotes"
    # CON_BOLD = "content_bold"
    CON_DRAW = "content_draws"
    CON_DYNAMIC_VAR = "content_dynamic_variables"
    CON_FLASHCARD = "content_flashcards"
    CON_PAGE_REF = "content_page_references"
    CON_TAG = "content_tags"
    CON_TAGGED_BACKLINK = "content_tagged_backlinks"
    DBC_ALL = "double_curly_all_or_macros"
    DBC_BLOCK_EMBEDS = "double_curly_block_embeds"
    DBC_CARDS = "double_curly_cards"
    DBC_CLOZES = "double_curly_clozes"
    DBC_EMBEDS = "double_curly_embeds"
    DBC_NAMESPACE_QUERIES = "double_curly_namespace_queries"
    DBC_PAGE_EMBEDS = "double_curly_page_embeds"
    DBC_QUERY_FUNCTIONS = "double_curly_query_functions"
    DBC_RENDERERS = "double_curly_renderers"
    DBC_SIMPLE_QUERIES = "double_curly_simple_queries"
    DBC_TWITTER_TWEETS = "double_curly_twitter_tweets"
    DBC_VIDEO_URLS = "double_curly_video_urls"
    DBC_YOUTUBE_TIMESTAMPS = "double_curly_youtube_timesteps"
    DBP_ALL_REFS = "double_parentheses_all_refs"
    DBP_BLOCK_REFS = "double_parentheses_block_refs"
    EMB_LINK_ASSET = "embedded_links_asset"
    EMB_LINK_INTERNET = "embedded_links_internet"
    EMB_LINK_OTHER = "embedded_links_other"
    EXT_LINK_ALIAS = "external_links_alias"
    EXT_LINK_INTERNET = "external_links_internet"
    EXT_LINK_OTHER = "external_links_other"
    PROP_BLOCK_BUILTIN = "property_block_builtin"
    PROP_BLOCK_USER = "property_block_user"
    PROP_PAGE_BUILTIN = "property_page_builtin"
    PROP_PAGE_USER = "property_page_user"
    PROP_VALUES = "property_values"


class Edn(StrEnum):
    """
    Enum for EDN data types.
    """

    FILE_NAME_FORMAT = ":journal/file-name-format"
    FILE_NAME_FORMAT_DEFAULT = "yyyy_MM_dd"
    JOURNALS_DIR = ":journals-directory"
    NS_FILE = ":file/name-format"
    PAGE_TITLE_FORMAT = ":journal/page-title-format"
    PAGE_TITLE_FORMAT_DEFAULT = "MMM do, yyyy"
    PAGES_DIR = ":pages-directory"
    PROP_PAGES = ":property-pages/enabled?"
    WHITEBOARDS_DIR = ":whiteboards-directory"


class FileType(StrEnum):
    """File types for the Logseq Analyzer."""

    ASSET = "asset"
    DRAW = "draw"
    JOURNAL = "journal"
    OTHER = "other"
    PAGE = "page"
    SUB_ASSET = "sub_asset"
    SUB_DRAW = "sub_draw"
    SUB_JOURNAL = "sub_journal"
    SUB_PAGE = "sub_page"
    SUB_WHITEBOARD = "sub_whiteboard"
    WHITEBOARD = "whiteboard"


class Format(StrEnum):
    """File formats used in the Logseq Analyzer."""

    HTML = "html"
    JSON = "json"
    MD = "md"
    ORG = "org"
    TXT = "txt"


class LogseqGraphStructure(StrEnum):
    """Logseq graph structure components."""

    BAK = "bak"
    CONFIG_EDN = "config.edn"
    LOGSEQ = "logseq"
    RECYCLE = ".recycle"


class Moved(StrEnum):
    """Moved files and directories in the Logseq Analyzer."""

    ASSETS = "assets"
    BAK = "bak"
    RECYCLE = "recycle"
    SIMULATED_PREFIX = "======== Simulated only ========"


class Node(StrEnum):
    """Node types for the Logseq Analyzer."""

    BRANCH = "branch"
    LEAF = "leaf"
    ORPHAN_GRAPH = "orphan_graph"
    ORPHAN_NAMESPACE = "orphan_namespace"
    ORPHAN_NAMESPACE_TRUE = "orphan_namespace_true"
    ORPHAN_TRUE = "orphan_true"
    OTHER = "other"
    ROOT = "root"


class Output(StrEnum):
    """Output types for the Logseq Analyzer."""

    ARGUMENTS = "arguments"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
    GRAPH_ALL_DANGLING_LINKS = "graph_all_dangling_links"
    GRAPH_ALL_LINKED_REFERENCES = "graph_all_linked_references"
    GRAPH_BULLETS = "graph_content_bullets"
    GRAPH_CONTENT = "graph_content"
    GRAPH_CONTENT_DATA = "graph_content_data"
    GRAPH_DANGLING_LINKS = "graph_dangling_links"
    GRAPH_DATA = "graph_data"
    GRAPH_UNIQUE_ALIASES = "graph_unique_aliases"
    GRAPH_UNIQUE_LINKED_REFERENCES = "graph_unique_linked_references"
    GRAPH_UNIQUE_LINKED_REFERENCES_NS = "graph_unique_linked_references_ns"
    HLS_ASSET_MAPPING = "hls_asset_mapping"
    HLS_BACKLINKED = "hls_backlinked"
    HLS_FORMATTED_BULLETS = "hls_formatted_bullets"
    HLS_NOT_BACKLINKED = "hls_not_backlinked"
    IDX_FILES = "index_files"
    IDX_NAME_TO_FILES = "index_name_to_files"
    IDX_PATH_TO_FILE = "index_path_to_file"
    JOURNALS_ALL = "journals_all"
    JOURNALS_DANGLING = "journals_dangling"
    JOURNALS_EXISTING = "journals_existing"
    JOURNALS_MISSING = "journals_missing"
    JOURNALS_TIMELINE = "journals_timeline"
    JOURNALS_TIMELINE_STATS = "journals_timeline_stats"
    MOVED_FILES = "moved_files"
    NS_CONFLICTS_DANGLING = "ns_conflicts_dangling"
    NS_CONFLICTS_NON_NAMESPACE = "ns_conflicts_non_namespace"
    NS_CONFLICTS_PARENT_DEPTH = "ns_conflicts_parent_depth"
    NS_CONFLICTS_PARENT_UNIQUE = "ns_conflicts_parent_unique"
    NS_DATA = "ns_data"
    NS_DETAILS = "ns_details"
    NS_HIERARCHY = "ns_hierarchy"
    NS_PARTS = "ns_parts"
    NS_QUERIES = "ns_queries"
    NS_UNIQUE_PARTS = "ns_unique_parts"
    NS_UNIQUE_PER_LEVEL = "ns_unique_per_level"


class OutputDir(StrEnum):
    """Output directories for the Logseq Analyzer."""

    GRAPH = "graph"
    INDEX = "index"
    JOURNALS = "journals"
    META = "_meta"
    MOVED_FILES = "moved_files"
    MOVED_FILES_ASSETS = "moved_files/assets"
    MOVED_FILES_HLS_ASSETS = "moved_files/hls_assets"
    NAMESPACES = "namespaces"
    SUMMARY_CONTENT = "summary_content"
    SUMMARY_FILES_FILE = "summary_files/file_types"
    SUMMARY_FILES_GENERAL = "summary_files/general"
    SUMMARY_FILES_NODE = "summary_files/node_types"
    SUMMARY_FILES_EXTENSIONS = "summary_files/extensions"


class TargetDir(StrEnum):
    """Target directories for the Logseq Analyzer."""

    ASSET = "assets"
    DRAW = "draws"
    JOURNAL = "journals"
    PAGE = "pages"
    WHITEBOARD = "whiteboards"
