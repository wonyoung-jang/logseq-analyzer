"""Enums for the Logseq Analyzer."""

from enum import StrEnum


class Core(StrEnum):
    """Core components of the Logseq Analyzer."""

    DATE_ORDINAL_SUFFIX = "o"
    HLS_PREFIX = "hls__"
    NS_CONFIG_LEGACY = ":legacy"
    NS_CONFIG_TRIPLE_LOWBAR = ":triple-lowbar"
    NS_FILE_SEP_LEGACY = "%2F"
    NS_FILE_SEP_TRIPLE_LOWBAR = "___"
    NS_SEP = "/"


class Crit:
    """Criteria for Logseq Analyzer."""

    class Content(StrEnum):
        """Content criteria."""

        ALIASES = "content_aliases"
        ANY_LINKS = "content_any_link"
        ASSETS = "content_asset"
        BLOCKQUOTES = "content_blockquote"
        DRAW = "content_draw"
        DYNAMIC_VAR = "content_dynamic_variable"
        FLASHCARD = "content_flashcard"
        PAGE_REF = "content_page_reference"
        TAG = "content_tag"
        TAGGED_BACKLINK = "content_tagged_backlink"

    class Prop(StrEnum):
        """Criteria for properties in Logseq."""

        BLOCK_BUILTIN = "property_block_builtin"
        BLOCK_USER = "property_block_user"
        PAGE_BUILTIN = "property_page_builtin"
        PAGE_USER = "property_page_user"
        VALUES = "property_values"

    class Code(StrEnum):
        """Criteria for code blocks in Logseq."""

        INLINE = "code_inline"
        ML_ALL = "code_multiline"
        ML_CALC = "code_multiline_calc"
        ML_LANG = "code_multiline_lang"

    class AdvCmd(StrEnum):
        """Criteria for advanced commands in Logseq."""

        ALL = "adv_cmd"
        CAUTION = "adv_cmd_caution"
        CENTER = "adv_cmd_center"
        COMMENT = "adv_cmd_comment"
        EXAMPLE = "adv_cmd_example"
        EXPORT = "adv_cmd_export"
        EXPORT_ASCII = "adv_cmd_export_ascii"
        EXPORT_LATEX = "adv_cmd_export_latex"
        IMPORTANT = "adv_cmd_important"
        NOTE = "adv_cmd_note"
        PINNED = "adv_cmd_pinned"
        QUERY = "adv_cmd_query"
        QUOTE = "adv_cmd_quote"
        TIP = "adv_cmd_tip"
        VERSE = "adv_cmd_verse"
        WARNING = "adv_cmd_warning"

    class DblCurly(StrEnum):
        """Criteria for double curly brackets in Logseq."""

        ALL = "double_curly_all_or_macros"
        BLOCK_EMBED = "double_curly_block_embeds"
        CARD = "double_curly_cards"
        CLOZE = "double_curly_clozes"
        EMBED = "double_curly_embeds"
        NAMESPACE_QUERY = "double_curly_namespace_queries"
        PAGE_EMBED = "double_curly_page_embeds"
        QUERY_FUNCTION = "double_curly_query_functions"
        RENDERER = "double_curly_renderers"
        SIMPLE_QUERY = "double_curly_simple_queries"
        EMBED_TWITTER_TWEET = "double_curly_twitter_tweets"
        EMBED_VIDEO_URL = "double_curly_video_urls"
        YOUTUBE_TIMESTAMP = "double_curly_youtube_timesteps"

    class DblParen(StrEnum):
        """Criteria for double parentheses in Logseq."""

        ALL_REFS = "double_parentheses_all_refs"
        BLOCK_REFS = "double_parentheses_block_refs"

    class Emb(StrEnum):
        """Criteria for embedded links in Logseq."""

        ASSET = "embedded_link_asset"
        INTERNET = "embedded_link_internet"
        OTHER = "embedded_link_other"

    class Ext(StrEnum):
        """Criteria for file extensions in Logseq."""

        ALIAS = "external_link_alias"
        INTERNET = "external_link_internet"
        OTHER = "external_link_other"


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

    MD = "md"
    TXT = "txt"


class TargetDir(StrEnum):
    """Target directories for the Logseq Analyzer."""

    ASSET = "assets"
    DRAW = "draws"
    JOURNAL = "journals"
    PAGE = "pages"
    WHITEBOARD = "whiteboards"


class Output:
    """Output types for the Logseq Analyzer."""

    class Dir(StrEnum):
        """Output directories for the Logseq Analyzer."""

        GRAPH = "graph"
        INDEX = "index"
        JOURNALS = "journals"
        META = "_meta"
        MOVED_FILES = "moved_files"
        ASSETS = "assets"
        NAMESPACES = "namespaces"
        SUMMARY = "summary"
        SUMMARY_CONTENT = "summary/content"
        SUMMARY_FILE_GENERAL = "summary/file_general"

    class File(StrEnum):
        """Output types for the Logseq Analyzer."""

        ARGUMENTS = "arguments"
        ASSETS_BACKLINKED = "assets_backlinked"
        ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
        GRAPH_ALL_DANGLING_LINKS = "graph_all_dangling_links"
        GRAPH_ALL_LINKED_REFERENCES = "graph_all_linked_references"
        GRAPH_BULLETS = "graph_content_bullets"
        GRAPH_CONTENT = "graph_content"
        GRAPH_DATA = "graph_content_data"
        GRAPH_DANGLING_LINKS = "graph_dangling_links"
        GRAPH_UNIQUE_ALIASES = "graph_unique_aliases"
        GRAPH_UNIQUE_LINKED_REFERENCES = "graph_unique_linked_references"
        GRAPH_UNIQUE_LINKED_REFERENCES_NS = "graph_unique_linked_references_ns"
        HLS_ASSET_MAPPING = "hls_asset_mapping"
        HLS_BACKLINKED = "hls_backlinked"
        HLS_FORMATTED_BULLETS = "hls_formatted_bullets"
        HLS_NOT_BACKLINKED = "hls_not_backlinked"
        IDX_FILES = "index_files"
        IDX_NAME_TO_FILES = "index_name_to_files"
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
        NS_DETAILS = "ns_details"
        NS_HIERARCHY = "ns_hierarchy"
        NS_PARTS = "ns_parts"
        NS_QUERIES = "ns_queries"
        NS_UNIQUE_PARTS = "ns_unique_parts"
        NS_UNIQUE_PER_LEVEL = "ns_unique_per_level"
        SUMMARY_BACKLINKED = "backlinked"
        SUMMARY_BACKLINKED_NS_ONLY = "backlinked_ns_only"
        SUMMARY_HAS_BACKLINKS = "has_backlinks"
        SUMMARY_HAS_CONTENT = "has_content"
        SUMMARY_IS_HLS = "is_hls"
        SUMMARY_FILE_FILETYPE = "file_filetype"
        SUMMARY_FILE_NODETYPE = "file_nodetype"
        SUMMARY_FILE_EXTENSION = "file_extension"
        SUMMARY_CONTENT_INFO = "content_info"


BACKLINK_CRITERIA: frozenset[str] = frozenset(
    (*Crit.Prop, Crit.Content.PAGE_REF, Crit.Content.TAGGED_BACKLINK, Crit.Content.TAG)
)
