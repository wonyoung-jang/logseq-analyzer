"""
LogseqFile class to process Logseq files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator


from ._global_objects import ANALYZER_CONFIG, PATTERNS
from .process_content_data import (
    find_all_lower,
    process_aliases,
    process_embedded_links,
    process_external_links,
    split_builtin_user_properties,
)
from .logseq_bullets import LogseqBullets
from .logseq_filestats import LogseqFilestats
from .logseq_filename import LogseqFilename

NS_SEP = ANALYZER_CONFIG.get("CONST", "NAMESPACE_SEP")


class LogseqFile:
    """A class to represent a Logseq file."""

    def __init__(self, file_path: Path):
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path = file_path
        self.content = ""
        self.data = {}
        self.primary_bullet = ""
        self.content_bullets = []
        self.file_type = ""
        self.has_content = False
        self.has_backlinks = False
        self.filename = LogseqFilename(self.file_path)
        self.filestats = LogseqFilestats(self.file_path)
        self.bullets = LogseqBullets(self.file_path)
        self.hash = LogseqFileHash(self.filename)
        self.get_single_file_metadata()
        self.process_content_data()

    def __repr__(self) -> str:
        return f"LogseqFile(name={self.filename.name}, path={self.file_path})"

    def get_single_file_metadata(self):
        """
        Extract metadata from a file.
        """
        self.uri = self.filename.uri
        if self.filename.logseq_url:
            self.logseq_url = self.filename.logseq_url

        self.has_content = self.filestats.size > 0
        self.file_type = self.determine_file_type()

        self.bullets.get_content()
        self.bullets.get_char_count()
        self.bullets.get_bullet_content()
        self.bullets.get_primary_bullet()
        self.bullets.get_bullet_density()
        self.content = self.bullets.content
        self.content_bullets = self.bullets.content_bullets
        self.primary_bullet = self.bullets.primary_bullet

        for attr, value in self.filename.__dict__.items():
            setattr(self, attr, value)
        for attr, value in self.filestats.__dict__.items():
            setattr(self, attr, value)
        for attr, value in self.bullets.__dict__.items():
            if attr not in ("content", "content_bullets", "all_bullets", "primary_bullet"):
                setattr(self, attr, value)

    def determine_file_type(self) -> str:
        """
        Helper function to determine the file type based on the directory structure.
        """
        return {
            ANALYZER_CONFIG.config["TARGET_DIRS"]["DIR_ASSETS"]: "asset",
            ANALYZER_CONFIG.config["TARGET_DIRS"]["DIR_DRAWS"]: "draw",
            ANALYZER_CONFIG.config["TARGET_DIRS"]["DIR_JOURNALS"]: "journal",
            ANALYZER_CONFIG.config["TARGET_DIRS"]["DIR_PAGES"]: "page",
            ANALYZER_CONFIG.config["TARGET_DIRS"]["DIR_WHITEBOARDS"]: "whiteboard",
        }.get(self.filename.parent, "other")

    def process_content_data(self):
        """
        Process content data to extract various elements like backlinks, tags, and properties.
        """
        # If no content, return
        if not self.bullets.content:
            return

        # Extract basic self.data
        primary_data = {
            # Advanced commands
            "advanced_commands": find_all_lower(PATTERNS.advcommand["_all"], self.bullets.content),
            "advanced_commands_export": find_all_lower(PATTERNS.advcommand["export"], self.bullets.content),
            "advanced_commands_export_ascii": find_all_lower(PATTERNS.advcommand["export_ascii"], self.bullets.content),
            "advanced_commands_export_latex": find_all_lower(PATTERNS.advcommand["export_latex"], self.bullets.content),
            "advanced_commands_caution": find_all_lower(PATTERNS.advcommand["caution"], self.bullets.content),
            "advanced_commands_center": find_all_lower(PATTERNS.advcommand["center"], self.bullets.content),
            "advanced_commands_comment": find_all_lower(PATTERNS.advcommand["comment"], self.bullets.content),
            "advanced_commands_example": find_all_lower(PATTERNS.advcommand["example"], self.bullets.content),
            "advanced_commands_important": find_all_lower(PATTERNS.advcommand["important"], self.bullets.content),
            "advanced_commands_note": find_all_lower(PATTERNS.advcommand["note"], self.bullets.content),
            "advanced_commands_pinned": find_all_lower(PATTERNS.advcommand["pinned"], self.bullets.content),
            "advanced_commands_query": find_all_lower(PATTERNS.advcommand["query"], self.bullets.content),
            "advanced_commands_quote": find_all_lower(PATTERNS.advcommand["quote"], self.bullets.content),
            "advanced_commands_tip": find_all_lower(PATTERNS.advcommand["tip"], self.bullets.content),
            "advanced_commands_verse": find_all_lower(PATTERNS.advcommand["verse"], self.bullets.content),
            "advanced_commands_warning": find_all_lower(PATTERNS.advcommand["warning"], self.bullets.content),
            # Basic content
            "assets": find_all_lower(PATTERNS.content["asset"], self.bullets.content),
            "block_references": find_all_lower(PATTERNS.content["block_reference"], self.bullets.content),
            "blockquotes": find_all_lower(PATTERNS.content["blockquote"], self.bullets.content),
            "draws": find_all_lower(PATTERNS.content["draw"], self.bullets.content),
            "flashcards": find_all_lower(PATTERNS.content["flashcard"], self.bullets.content),
            "page_references": find_all_lower(PATTERNS.content["page_reference"], self.bullets.content),
            "references_general": find_all_lower(PATTERNS.content["reference"], self.bullets.content),
            "tagged_backlinks": find_all_lower(PATTERNS.content["tagged_backlink"], self.bullets.content),
            "tags": find_all_lower(PATTERNS.content["tag"], self.bullets.content),
            "dynamic_variables": find_all_lower(PATTERNS.content["dynamic_variable"], self.bullets.content),
            # Code family (escapes others)
            "multiline_code_blocks": find_all_lower(PATTERNS.code["multiline_code_block"], self.bullets.content),
            "multiline_code_langs": find_all_lower(PATTERNS.code["multiline_code_lang"], self.bullets.content),
            "calc_blocks": find_all_lower(PATTERNS.code["calc_block"], self.bullets.content),
            "inline_code_blocks": find_all_lower(PATTERNS.code["inline_code_block"], self.bullets.content),
            # Double curly braces family
            "macros": find_all_lower(PATTERNS.dblcurly["macro"], self.bullets.content),
            "embeds": find_all_lower(PATTERNS.dblcurly["embed"], self.bullets.content),
            "page_embeds": find_all_lower(PATTERNS.dblcurly["page_embed"], self.bullets.content),
            "block_embeds": find_all_lower(PATTERNS.dblcurly["block_embed"], self.bullets.content),
            "namespace_queries": find_all_lower(PATTERNS.dblcurly["namespace_query"], self.bullets.content),
            "cards": find_all_lower(PATTERNS.dblcurly["card"], self.bullets.content),
            "clozes": find_all_lower(PATTERNS.dblcurly["cloze"], self.bullets.content),
            "simple_queries": find_all_lower(PATTERNS.dblcurly["simple_query"], self.bullets.content),
            "query_functions": find_all_lower(PATTERNS.dblcurly["query_function"], self.bullets.content),
            "embed_video_urls": find_all_lower(PATTERNS.dblcurly["embed_video_url"], self.bullets.content),
            "embed_twitter_tweets": find_all_lower(PATTERNS.dblcurly["embed_twitter_tweet"], self.bullets.content),
            "embed_youtube_timestamps": find_all_lower(
                PATTERNS.dblcurly["embed_youtube_timestamp"], self.bullets.content
            ),
            "renderers": find_all_lower(PATTERNS.dblcurly["renderer"], self.bullets.content),
        }

        # Extract all properties: values pairs
        properties_values = {}
        property_value_all = PATTERNS.content["property_value"].findall(self.bullets.content)
        for prop, value in property_value_all:
            properties_values.setdefault(prop, value)

        aliases = properties_values.get("alias")
        if aliases:
            aliases = process_aliases(aliases)

        # Extract page/block properties
        page_properties = []
        if self.is_primary_bullet_page_properties():
            page_properties = find_all_lower(PATTERNS.content["property"], self.bullets.primary_bullet)
            self.bullets.content = "\n".join(self.bullets.content_bullets)
        block_properties = find_all_lower(PATTERNS.content["property"], self.bullets.content)

        properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties)
        properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties)

        # Process external and embedded links
        external_links = find_all_lower(PATTERNS.ext_links["external_link"], self.bullets.content)
        embedded_links = find_all_lower(PATTERNS.emb_links["embedded_link"], self.bullets.content)
        ext_links_other, ext_links_internet, ext_links_alias = process_external_links(external_links)
        emb_links_other, emb_links_internet, emb_links_asset = process_embedded_links(embedded_links)

        primary_data.update(
            {
                "aliases": aliases,
                "properties_block_builtin": properties_block_builtin,
                "properties_block_user": properties_block_user,
                "properties_page_builtin": properties_page_builtin,
                "properties_page_user": properties_page_user,
                "properties_values": properties_values,
                "external_links_alias": ext_links_alias,
                "external_links_internet": ext_links_internet,
                "external_links_other": ext_links_other,
                "embedded_links_asset": emb_links_asset,
                "embedded_links_internet": emb_links_internet,
                "embedded_links_other": emb_links_other,
            }
        )

        for key, value in primary_data.items():
            if value:
                self.data.setdefault(key, value)
                if not self.has_backlinks:
                    if key in ("page_references", "tags", "tagged_backlinks") or "properties" in key:
                        self.has_backlinks = True

    def is_primary_bullet_page_properties(self) -> bool:
        """
        Process primary bullet data.
        """
        bullet = self.primary_bullet.strip()
        if not bullet or bullet.startswith("#"):
            return False
        return True

    def determine_node_type(self) -> str:
        """Helper function to determine node type based on summary data."""
        return {
            (True, True, True, True): "branch",
            (True, True, False, True): "branch",
            (True, True, True, False): "leaf",
            (True, True, False, False): "leaf",
            (False, True, True, False): "leaf",
            (False, True, False, False): "leaf",
            (True, False, True, True): "root",
            (True, False, False, True): "root",
            (True, False, True, False): "orphan_namespace",
            (False, False, True, False): "orphan_namespace_true",
            (True, False, False, False): "orphan_graph",
            (False, False, False, False): "orphan_true",
        }.get((self.has_content, self.is_backlinked, self.is_backlinked_by_ns_only, self.has_backlinks), "other")


@dataclass
class LogseqFileHash:
    """A class to represent a Logseq file hash."""

    filename: LogseqFilename

    def __repr__(self):
        """
        Return the string representation of the LogseqFileHash object.
        """
        return f"LogseqFileHash(key={self.__key()}, hash={self.__hash__()})"

    def __key(self):
        """
        Return the key for the LogseqFileHash object.
        """
        return (self.filename.name, self.filename.parent, self.filename.suffix)

    def __hash__(self):
        """
        Return the hash of the LogseqFileHash object.
        """
        return hash(self.__key())

    def __eq__(self, other):
        """
        Check if two LogseqFileHash objects are equal.
        """
        if isinstance(other, LogseqFileHash):
            return self.__key() == other.__key()
        return NotImplemented
