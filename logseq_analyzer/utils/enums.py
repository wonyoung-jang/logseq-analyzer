"""
Enums for the Logseq Analyzer.
"""

from enum import Enum

__all__ = [
    "Arguments",
    "CacheKeys",
    "Config",
    "Constants",
    "Core",
    "Criteria",
    "FileTypes",
    "Format",
    "Moved",
    "Nodes",
    "Output",
    "OutputDir",
    "SummaryFiles",
]


class Arguments(Enum):
    """Arguments for the Logseq Analyzer."""

    GEOMETRY = "geometry"
    GLOBAL_CONFIG = "global_config"
    GRAPH_CACHE = "graph_cache"
    GRAPH_FOLDER = "graph_folder"
    MOVE_ALL = "move_all"
    MOVE_BAK = "move_bak"
    MOVE_RECYCLE = "move_recycle"
    MOVE_UNLINKED_ASSETS = "move_unlinked_assets"
    REPORT_FORMAT = "report_format"
    WRITE_GRAPH = "write_graph"


class CacheKeys(Enum):
    """Cache keys for the Logseq Analyzer."""

    INDEX = "index"
    MOD_TRACKER = "mod_tracker"


class Config(Enum):
    """Configuration settings for the Logseq Analyzer."""

    DIR_ASSETS = "DIR_ASSETS"
    DIR_BAK = "DIR_BAK"
    DIR_DRAWS = "DIR_DRAWS"
    DIR_JOURNALS = "DIR_JOURNALS"
    DIR_PAGES = "DIR_PAGES"
    DIR_RECYCLE = "DIR_RECYCLE"
    DIR_WHITEBOARDS = "DIR_WHITEBOARDS"


class Constants(Enum):
    """Constants used in the Logseq Analyzer."""

    CACHE_FILE = "logseq-analyzer-cache"
    CONFIG_INI_FILE = "logseq_analyzer/config/configuration/config.ini"
    CONFIG_USER_INI_FILE = "logseq_analyzer/config/configuration/user_config.ini"
    LOG_FILE = "logseq-analyzer-output/logseq_analyzer.log"
    OUTPUT_DIR = "logseq-analyzer-output"
    TO_DELETE_ASSETS_DIR = "to-delete/assets"
    TO_DELETE_BAK_DIR = "to-delete/bak"
    TO_DELETE_DIR = "to-delete"
    TO_DELETE_RECYCLE_DIR = "to-delete/.recycle"


class Core(Enum):
    """Core components of the Logseq Analyzer."""

    DATE_ORDINAL_SUFFIX = "o"
    HLS_PREFIX = "hls__"
    NS_CONFIG_LEGACY = ":legacy"
    NS_CONFIG_TRIPLE_LOWBAR = ":triple-lowbar"
    NS_FILE_SEP_LEGACY = "%2F"
    NS_FILE_SEP_TRIPLE_LOWBAR = "___"
    NS_SEP = "/"


class Criteria(Enum):
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
    ALIASES = "aliases"
    ANY_LINKS = "any_links"
    ASSETS = "assets"
    BLOCK_EMBEDS = "block_embeds"
    BLOCK_REFERENCES = "block_references"
    BLOCKQUOTES = "blockquotes"
    BOLD = "bold"
    CALC_BLOCKS = "calc_blocks"
    CARDS = "cards"
    CLOZES = "clozes"
    DRAWS = "draws"
    DYNAMIC_VARIABLES = "dynamic_variables"
    EMB_LINK_ASSET = "embedded_links_asset"
    EMB_LINK_INTERNET = "embedded_links_internet"
    EMB_LINK_OTHER = "embedded_links_other"
    EMBED_TWITTER_TWEETS = "embed_twitter_tweets"
    EMBED_VIDEO_URLS = "embed_video_urls"
    EMBED_YOUTUBE_TIMESTAMPS = "embed_youtube_timestamps"
    EMBEDS = "embeds"
    EXT_LINK_ALIAS = "external_links_alias"
    EXT_LINK_INTERNET = "external_links_internet"
    EXT_LINK_OTHER = "external_links_other"
    FLASHCARDS = "flashcards"
    INLINE_CODE_BLOCKS = "inline_code_blocks"
    MACROS = "macros"
    MULTILINE_CODE_BLOCKS = "multiline_code_blocks"
    MULTILINE_CODE_LANGS = "multiline_code_langs"
    NAMESPACE_QUERIES = "namespace_queries"
    PAGE_EMBEDS = "page_embeds"
    PAGE_REFERENCES = "page_references"
    PROP_BLOCK_BUILTIN = "properties_block_builtin"
    PROP_BLOCK_USER = "properties_block_user"
    PROP_PAGE_BUILTIN = "properties_page_builtin"
    PROP_PAGE_USER = "properties_page_user"
    PROP_VALUES = "properties_values"
    QUERY_FUNCTIONS = "query_functions"
    REFERENCES_GENERAL = "references_general"
    RENDERERS = "renderers"
    SIMPLE_QUERIES = "simple_queries"
    TAGGED_BACKLINKS = "tagged_backlinks"
    TAGS = "tags"


class FileTypes(Enum):
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


class Format(Enum):
    """File formats used in the Logseq Analyzer."""

    CSV = ".csv"
    GIF = ".gif"
    HTML = ".html"
    JPEG = ".jpeg"
    JPG = ".jpg"
    JSON = ".json"
    MD = ".md"
    ORG = ".org"
    PNG = ".png"
    SVG = ".svg"
    TSV = ".tsv"
    TXT = ".txt"


class Moved(Enum):
    """Moved files and directories in the Logseq Analyzer."""

    ASSETS = "moved_assets"
    BAK = "moved_bak"
    RECYCLE = "moved_recycle"
    SIMULATED_PREFIX = "======== Simulated only ========"


class Nodes(Enum):
    """Node types for the Logseq Analyzer."""

    BRANCH = "branch"
    LEAF = "leaf"
    ORPHAN_GRAPH = "orphan_graph"
    ORPHAN_NAMESPACE = "orphan_namespace"
    ORPHAN_NAMESPACE_TRUE = "orphan_namespace_true"
    ORPHAN_TRUE = "orphan_true"
    OTHER = "other"
    ROOT = "root"


class Output(Enum):
    """Output types for the Logseq Analyzer."""

    ALL_DANGLING_LINKS = "all_dangling_links"
    ALL_LINKED_REFERENCES = "all_linked_references"
    ARGUMENTS = "arguments"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
    COMPLETE_TIMELINE = "complete_timeline"
    CONFIG_GLOBAL = "config_global"
    CONFIG_MERGED = "config_merged"
    CONFIG_USER = "config_user"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    DANGLING_JOURNALS = "dangling_journals"
    DANGLING_LINKS = "dangling_links"
    FILES = "files"
    GRAPH_CONTENT = "content_bullets"
    GRAPH_DATA = "data"
    HASH_TO_FILE = "hash_to_file"
    HLS_ASSET_MAPPING = "hls_asset_mapping"
    HLS_ASSET_NAMES = "hls_asset_names"
    HLS_BACKLINKED = "hls_backlinked"
    HLS_FORMATTED_BULLETS = "hls_formatted_bullets"
    HLS_NOT_BACKLINKED = "hls_not_backlinked"
    MISSING_JOURNALS = "missing_journals"
    MOVED_FILES = "moved_files"
    NAME_TO_FILES = "name_to_files"
    NAMESPACE_DATA = "namespace_data"
    NAMESPACE_DETAILS = "namespace_details"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    NAMESPACE_PARTS = "namespace_parts"
    NAMESPACE_QUERIES = "namespace_queries"
    PATH_TO_FILE = "path_to_file"
    PROCESSED_JOURNALS = "processed_journals"
    TIMELINE_STATS = "timeline_stats"
    UNIQUE_LINKED_REFERENCES = "unique_linked_references"
    UNIQUE_LINKED_REFERENCES_NS = "unique_linked_references_ns"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"


class OutputDir(Enum):
    """Output directories for the Logseq Analyzer."""

    JOURNALS = "journals"
    META = "_meta"
    MOVED_FILES = "moved_files"
    NAMESPACES = "namespaces"
    SUMMARY_CONTENT = "summary_content"
    SUMMARY_FILES = "summary_files"
    TEST = "test"


class SummaryFiles(Enum):
    """Summary files for the Logseq Analyzer."""

    FILE_EXTS = "file_extensions_dict"
    FILETYPE_ASSET = "filetype_asset"
    FILETYPE_DRAW = "filetype_draw"
    FILETYPE_JOURNAL = "filetype_journal"
    FILETYPE_OTHER = "filetype_other"
    FILETYPE_PAGE = "filetype_page"
    FILETYPE_SUB_ASSET = "filetype_sub_asset"
    FILETYPE_SUB_DRAW = "filetype_sub_draw"
    FILETYPE_SUB_JOURNAL = "filetype_sub_journal"
    FILETYPE_SUB_PAGE = "filetype_sub_page"
    FILETYPE_SUB_WHITEBOARD = "filetype_sub_whiteboard"
    FILETYPE_WHITEBOARD = "filetype_whiteboard"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_BACKLINKED = "is_backlinked"
    IS_BACKLINKED_BY_NS_ONLY = "is_backlinked_by_ns_only"
    IS_HLS = "is_hls"
    NODE_BRANCH = "node_branch"
    NODE_LEAF = "node_leaf"
    NODE_ORPHAN_GRAPH = "node_orphan_graph"
    NODE_ORPHAN_NAMESPACE = "node_orphan_namespace"
    NODE_ORPHAN_NAMESPACE_TRUE = "node_orphan_namespace_true"
    NODE_ORPHAN_TRUE = "node_orphan_true"
    NODE_OTHER = "node_other"
    NODE_ROOT = "node_root"
