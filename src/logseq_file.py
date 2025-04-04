"""
LogseqFile class to process Logseq files.
"""

import logging
from pathlib import Path

from ._global_objects import ANALYZER_CONFIG, PATTERNS
from .process_content_data import (
    find_all_lower,
    process_aliases,
    process_embedded_links,
    process_external_links,
    split_builtin_user_properties,
)
from .logseq_filestats import LogseqFilestats
from .logseq_filename import LogseqFilename


class LogseqFile:
    """
    A class to represent a Logseq file.
    """

    def __init__(self, file_path: Path):
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.logseq_filename = None
        self.logseq_filestats = None

        self.file_path = file_path
        self.content = ""
        self.data = {}
        self.primary_bullet = ""
        self.content_bullets = []

    def __repr__(self):
        """
        Return a string representation of the LogseqFile object.
        """
        return f"LogseqFile({self.data['name'], self.data['file_path_suffix']})"

    def process_single_file(self):
        """
        Process a single file: extract metadata, read content, and compute content-based metrics.
        """
        self.get_single_file_content()
        self.get_single_file_metadata()
        self.process_bullet_data()
        self.process_content_data()

    def get_single_file_content(self):
        """
        Read the text content of a file.
        """
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning("File not found: %s", self.file_path)
        except IsADirectoryError:
            logging.warning("Path is a directory, not a file: %s", self.file_path)
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)

    def get_single_file_metadata(self):
        """
        Extract metadata from a file.
        """
        ls_filename = LogseqFilename(self.file_path)
        self.logseq_filename = ls_filename

        ls_filestats = LogseqFilestats(self.file_path)
        self.logseq_filestats = ls_filestats

        self.data["file_path"] = str(self.file_path)

        self.data["id"] = ls_filename.id
        self.data["name"] = ls_filename.key
        self.data["name_secondary"] = ls_filename.name_secondary
        self.data["original_name"] = ls_filename.original_name
        self.data["file_path_parent_name"] = ls_filename.parent
        self.data["file_path_suffix"] = ls_filename.suffix
        self.data["file_path_parts"] = ls_filename.file_path_parts
        self.data["uri"] = ls_filename.uri
        if ls_filename.logseq_url:
            self.data["logseq_url"] = ls_filename.logseq_url

        self.data["date_created"] = ls_filestats.date_created
        self.data["date_modified"] = ls_filestats.date_modified
        self.data["time_existed"] = ls_filestats.time_existed
        self.data["time_unmodified"] = ls_filestats.time_unmodified
        self.data["size"] = ls_filestats.size

    def process_bullet_data(self):
        """
        Process bullet data to extract metadata and content.
        """
        if self.content:
            # Count characters
            self.data["char_count"] = len(self.content)
            # Count bullets
            bullet_count = 0
            if self.data["file_path_suffix"] == ".md":
                bullet_content = PATTERNS.content["bullet"].split(self.content)
                if len(bullet_content) > 1:
                    self.primary_bullet = bullet_content[0].strip()
                    self.content_bullets = [bullet.strip() for bullet in bullet_content[1:] if bullet.strip()]
                    empty_bullets = [bullet.strip() for bullet in bullet_content[1:] if not bullet.strip()]
                    bullet_count_empty = len(empty_bullets)
                    bullet_count = len(self.content_bullets)
                else:
                    bullet_count = 0
                    bullet_count_empty = 0
                self.data["bullet_count"] = bullet_count
                self.data["bullet_count_empty"] = bullet_count_empty
            # Calculate bullet density
            if bullet_count > 0:
                self.data["bullet_density"] = round(self.data["char_count"] / bullet_count, 2)

    def process_content_data(self):
        """
        Process content data to extract various elements like backlinks, tags, and properties.
        """
        # Process namespaces
        ns_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")
        if ns_sep in self.data["name"]:
            for key, value in self.process_content_namespace_data(ns_sep):
                self.data[key] = value

        # If no content, return self.data
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

        for key, value in primary_data.items():
            if value:
                self.data[key] = value

    def process_content_namespace_data(self, ns_sep: str):
        """
        Process namespaces in the data dictionary.
        """
        namespace_parts_list = self.data["name"].split(ns_sep)
        namespace_level = len(namespace_parts_list)
        namespace_root = namespace_parts_list[0]
        namespace_stem = namespace_parts_list[-1]
        namespace_parent = namespace_root
        if namespace_level > 2:
            namespace_parent = namespace_parts_list[-2]

        namespace_parts = {part: level for level, part in enumerate(namespace_parts_list, start=1)}
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
