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
from .process_summary_data import determine_file_type
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
        self.filename = LogseqFilename(file_path)
        self.filestats = LogseqFilestats(file_path)
        self.bullets = LogseqBullets(file_path)
        self.hash = LogseqFileHash(self.filename)

    def __repr__(self) -> str:
        return f"LogseqFile(name={self.filename.name}, path={self.file_path})"

    def get_single_file_metadata(self):
        """
        Extract metadata from a file.
        """
        self.data["file_path"] = str(self.file_path)

        self.data["id"] = self.filename.id
        self.data["name"] = self.filename.name
        self.data["name_secondary"] = self.filename.name_secondary
        self.data["file_path_suffix"] = self.filename.suffix
        self.data["uri"] = self.filename.uri
        if self.filename.logseq_url:
            self.data["logseq_url"] = self.filename.logseq_url

        self.data["logseq_filename_object"] = self.filename.__dict__
        self.data["logseq_filestats_object"] = self.filestats.__dict__
        self.data["has_content"] = self.filestats.size > 0
        self.data["file_type"] = determine_file_type(self.filename.parent)
        self.bullets.get_content()
        self.bullets.get_char_count()
        self.bullets.get_bullet_content()
        self.bullets.get_primary_bullet()
        self.bullets.get_bullet_density()
        self.content = self.bullets.content
        self.content_bullets = self.bullets.content_bullets
        self.primary_bullet = self.bullets.primary_bullet
        self.data["logseq_bullets_object"] = {
            k: v
            for k, v in self.bullets.__dict__.items()
            if k not in ("content", "content_bullets", "all_bullets", "primary_bullet") and v
        }

    def process_content_data(self):
        """
        Process content data to extract various elements like backlinks, tags, and properties.
        """
        # Process namespaces
        if self.filename.is_namespace:
            for key, value in self.process_content_namespace_data():
                self.data.setdefault(key, value)

        # If no content, return
        if not self.content:
            return

        # Extract basic self.data
        primary_data = {
            # Advanced commands
            "advanced_commands": find_all_lower(PATTERNS.advcommand["_all"], self.content),
            "advanced_commands_export": find_all_lower(PATTERNS.advcommand["export"], self.content),
            "advanced_commands_export_ascii": find_all_lower(PATTERNS.advcommand["export_ascii"], self.content),
            "advanced_commands_export_latex": find_all_lower(PATTERNS.advcommand["export_latex"], self.content),
            "advanced_commands_caution": find_all_lower(PATTERNS.advcommand["caution"], self.content),
            "advanced_commands_center": find_all_lower(PATTERNS.advcommand["center"], self.content),
            "advanced_commands_comment": find_all_lower(PATTERNS.advcommand["comment"], self.content),
            "advanced_commands_example": find_all_lower(PATTERNS.advcommand["example"], self.content),
            "advanced_commands_important": find_all_lower(PATTERNS.advcommand["important"], self.content),
            "advanced_commands_note": find_all_lower(PATTERNS.advcommand["note"], self.content),
            "advanced_commands_pinned": find_all_lower(PATTERNS.advcommand["pinned"], self.content),
            "advanced_commands_query": find_all_lower(PATTERNS.advcommand["query"], self.content),
            "advanced_commands_quote": find_all_lower(PATTERNS.advcommand["quote"], self.content),
            "advanced_commands_tip": find_all_lower(PATTERNS.advcommand["tip"], self.content),
            "advanced_commands_verse": find_all_lower(PATTERNS.advcommand["verse"], self.content),
            "advanced_commands_warning": find_all_lower(PATTERNS.advcommand["warning"], self.content),
            # Basic content
            "assets": find_all_lower(PATTERNS.content["asset"], self.content),
            "block_references": find_all_lower(PATTERNS.content["block_reference"], self.content),
            "blockquotes": find_all_lower(PATTERNS.content["blockquote"], self.content),
            "draws": find_all_lower(PATTERNS.content["draw"], self.content),
            "flashcards": find_all_lower(PATTERNS.content["flashcard"], self.content),
            "page_references": find_all_lower(PATTERNS.content["page_reference"], self.content),
            "references_general": find_all_lower(PATTERNS.content["reference"], self.content),
            "tagged_backlinks": find_all_lower(PATTERNS.content["tagged_backlink"], self.content),
            "tags": find_all_lower(PATTERNS.content["tag"], self.content),
            "dynamic_variables": find_all_lower(PATTERNS.content["dynamic_variable"], self.content),
            # Code family (escapes others)
            "multiline_code_blocks": find_all_lower(PATTERNS.code["multiline_code_block"], self.content),
            "multiline_code_langs": find_all_lower(PATTERNS.code["multiline_code_lang"], self.content),
            "calc_blocks": find_all_lower(PATTERNS.code["calc_block"], self.content),
            "inline_code_blocks": find_all_lower(PATTERNS.code["inline_code_block"], self.content),
            # Double curly braces family
            "macros": find_all_lower(PATTERNS.dblcurly["macro"], self.content),
            "embeds": find_all_lower(PATTERNS.dblcurly["embed"], self.content),
            "page_embeds": find_all_lower(PATTERNS.dblcurly["page_embed"], self.content),
            "block_embeds": find_all_lower(PATTERNS.dblcurly["block_embed"], self.content),
            "namespace_queries": find_all_lower(PATTERNS.dblcurly["namespace_query"], self.content),
            "cards": find_all_lower(PATTERNS.dblcurly["card"], self.content),
            "clozes": find_all_lower(PATTERNS.dblcurly["cloze"], self.content),
            "simple_queries": find_all_lower(PATTERNS.dblcurly["simple_query"], self.content),
            "query_functions": find_all_lower(PATTERNS.dblcurly["query_function"], self.content),
            "embed_video_urls": find_all_lower(PATTERNS.dblcurly["embed_video_url"], self.content),
            "embed_twitter_tweets": find_all_lower(PATTERNS.dblcurly["embed_twitter_tweet"], self.content),
            "embed_youtube_timestamps": find_all_lower(PATTERNS.dblcurly["embed_youtube_timestamp"], self.content),
            "renderers": find_all_lower(PATTERNS.dblcurly["renderer"], self.content),
        }

        # Extract all properties: values pairs
        properties_values = {}
        property_value_all = PATTERNS.content["property_value"].findall(self.content)
        for prop, value in property_value_all:
            properties_values.setdefault(prop, value)

        aliases = properties_values.get("alias")
        if aliases:
            aliases = process_aliases(aliases)

        # Extract page/block properties
        page_properties = []
        if self.is_primary_bullet_page_properties():
            page_properties = find_all_lower(PATTERNS.content["property"], self.primary_bullet)
            self.content = "\n".join(self.content_bullets)
        block_properties = find_all_lower(PATTERNS.content["property"], self.content)

        properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties)
        properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties)

        # Process external and embedded links
        external_links = find_all_lower(PATTERNS.ext_links["external_link"], self.content)
        embedded_links = find_all_lower(PATTERNS.emb_links["embedded_link"], self.content)
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

        self.data.setdefault("has_backlinks", False)
        for key, value in primary_data.items():
            if value:
                self.data.setdefault(key, value)
                if not self.data.get("has_backlinks"):
                    if key in ("page_references", "tags", "tagged_backlinks") or "properties" in key:
                        self.data["has_backlinks"] = True

    def process_content_namespace_data(self) -> Generator[str, str, None]:
        """
        Process namespaces in the data dictionary.
        """
        ns_parts_list = self.filename.name.split(NS_SEP)
        namespace_level = len(ns_parts_list)
        namespace_root = ns_parts_list[0]
        namespace_stem = ns_parts_list[-1]
        namespace_parent = namespace_root
        if namespace_level > 2:
            namespace_parent = ns_parts_list[-2]

        namespace_parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
        namespace_data = {
            "namespace_root": namespace_root,
            "namespace_parent": namespace_parent,
            "namespace_stem": namespace_stem,
            "namespace_parts": namespace_parts,
            "namespace_level": namespace_level,
        }

        for key, value in namespace_data.items():
            if value:
                yield key, value

    def is_primary_bullet_page_properties(self) -> bool:
        """
        Process primary bullet data.
        """
        bullet = self.primary_bullet.strip()
        if not bullet or bullet.startswith("#"):
            return False
        return True


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
