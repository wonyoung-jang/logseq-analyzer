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


class FileType(StrEnum):
    """File types for the Logseq Analyzer."""

    ASSET = "asset"
    DRAW = "draw"
    JOURNAL = "journal"
    PAGE = "page"
    WHITEBOARD = "whiteboard"
    SUB_ASSET = "sub_asset"
    SUB_DRAW = "sub_draw"
    SUB_JOURNAL = "sub_journal"
    SUB_PAGE = "sub_page"
    SUB_WHITEBOARD = "sub_whiteboard"
    OTHER = "other"


class Crit:
    """Criteria for Logseq Analyzer."""

    class Content(StrEnum):
        """Content criteria."""

        ALIAS = "Content_alias"
        ANY_LINK = "Content_any_link"
        ASSET = "Content_asset"
        BLOCKQUOTE = "Content_blockquote"
        DRAW = "Content_draw"
        DYNAMIC_VAR = "Content_dynamic_variable"
        FLASHCARD = "Content_flashcard"
        HLS_BULLET = "Content_hls_bullet"
        PAGE_REF = "Content_page_reference"
        TAG = "Content_tag"
        TAGGED_BACKLINK = "Content_tagged_backlink"
        INLINE_CODE = "Content_inline_code"

    class Prop(StrEnum):
        """Criteria for properties in Logseq."""

        BLOCK_BUILTIN = "PropBlock_builtin"
        BLOCK_USER = "PropBlock_user"
        PAGE_BUILTIN = "PropPage_builtin"
        PAGE_USER = "PropPage_user"
        VALUES = "PropValues"

    class MultLineCode(StrEnum):
        """Criteria for code blocks in Logseq."""

        ALL = "MultLineCode_"
        CALC = "MultLineCode_calc"
        LANGUAGE = "MultLineCode_lang"

    class AdvCmd(StrEnum):
        """Criteria for advanced commands in Logseq."""

        ALL = "AdvCmd_"
        CAUTION = "AdvCmd_caution"
        CENTER = "AdvCmd_center"
        COMMENT = "AdvCmd_comment"
        EXAMPLE = "AdvCmd_example"
        EXPORT = "AdvCmd_export"
        EXPORT_ASCII = "AdvCmd_export_ascii"
        EXPORT_LATEX = "AdvCmd_export_latex"
        IMPORTANT = "AdvCmd_important"
        NOTE = "AdvCmd_note"
        PINNED = "AdvCmd_pinned"
        QUERY = "AdvCmd_query"
        QUOTE = "AdvCmd_quote"
        TIP = "AdvCmd_tip"
        VERSE = "AdvCmd_verse"
        WARNING = "AdvCmd_warning"

    class DblCurly(StrEnum):
        """Criteria for double curly brackets in Logseq."""

        ALL = "DblCurly_"
        BLOCK_EMBED = "DblCurly_block_embed"
        CARD = "DblCurly_card"
        CLOZE = "DblCurly_cloze"
        EMBED = "DblCurly_embed"
        NAMESPACE_QUERY = "DblCurly_namespace_query"
        PAGE_EMBED = "DblCurly_page_embed"
        QUERY_FUNCTION = "DblCurly_query_function"
        RENDERER = "DblCurly_renderer"
        SIMPLE_QUERY = "DblCurly_simple_query"
        EMBED_TWITTER_TWEET = "DblCurly_twitter_tweet"
        EMBED_VIDEO_URL = "DblCurly_video_url"
        YOUTUBE_TIMESTAMP = "DblCurly_youtube_timestep"

    class DblParen(StrEnum):
        """Criteria for double parentheses in Logseq."""

        ALL = "DblParen_"
        BLOCK_REF = "DblParen_block_ref"

    class EmbLink(StrEnum):
        """Criteria for embedded links in Logseq."""

        ALL = "EmbLink_"
        ASSET = "EmbLink_asset"
        INTERNET = "EmbLink_internet"

    class ExtLink(StrEnum):
        """Criteria for file extensions in Logseq."""

        ALL = "ExtLink_"
        ALIAS = "ExtLink_alias"
        INTERNET = "ExtLink_internet"


class Output:
    """Output types for the Logseq Analyzer."""

    class Dir(StrEnum):
        """Output directories for the Logseq Analyzer."""

        GRAPH = "graph"
        INDEX = "index"
        JOURNAL = "journal"
        MOVED = "moved"
        ASSET = "asset"
        NAMESPACE = "namespace"
        SUMMARY = "summary"

    class File(StrEnum):
        """Output types for the Logseq Analyzer."""

        GRAPH_DATA = "graph_data"
        MOVED = "moved"
        SUMMARY_BACKLINKED = "backlinked"
        SUMMARY_BACKLINKED_NS_ONLY = "backlinked_ns_only"
        SUMMARY_HAS_BACKLINK = "has_backlink"
        SUMMARY_HAS_CONTENT = "has_content"
        SUMMARY_IS_HLS = "is_hls"


BACKLINK_CRITERIA: frozenset[str] = frozenset(
    (*Crit.Prop, Crit.Content.PAGE_REF, Crit.Content.TAGGED_BACKLINK, Crit.Content.TAG)
)
