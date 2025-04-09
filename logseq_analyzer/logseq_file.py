"""
LogseqFile class to process Logseq files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple
import uuid


from ._global_objects import ANALYZER_CONFIG, PATTERNS
from .logseq_bullets import LogseqBullets
from .logseq_filestats import LogseqFilestats
from .logseq_filename import LogseqFilename
from .helpers import find_all_lower, process_aliases

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
        self.has_content = False
        self.has_backlinks = False
        self.init_file_data()
        self.hash = LogseqFileHash(self)
        self.process_content_data()

    def __repr__(self) -> str:
        return f"LogseqFile(name={self.name}, path={self.file_path})"

    def init_file_data(self):
        """
        Extract metadata from a file.
        """
        for attr, value in LogseqFilename(self.file_path).__dict__.items():
            setattr(self, attr, value)
        for attr, value in LogseqFilestats(self.file_path).__dict__.items():
            setattr(self, attr, value)
        for attr, value in LogseqBullets(self.file_path).__dict__.items():
            if attr not in ("all_bullets"):
                setattr(self, attr, value)

    def process_content_data(self):
        """
        Process content data to extract various elements like backlinks, tags, and properties.
        """
        # If no content, return
        if not self.content:
            return

        # Mask code blocks to avoid interference with pattern matching
        masked_content, code_blocks = self.mask_code_blocks(self.content)

        # Extract basic data
        primary_data = {
            # Code blocks
            "multiline_code_blocks": find_all_lower(PATTERNS.code["multiline_code_block"], self.content),
            "multiline_code_langs": find_all_lower(PATTERNS.code["multiline_code_lang"], self.content),
            "calc_blocks": find_all_lower(PATTERNS.code["calc_block"], self.content),
            "inline_code_blocks": find_all_lower(PATTERNS.code["inline_code_block"], self.content),
            # Advanced commands
            "advanced_commands": find_all_lower(PATTERNS.advcommand["_all"], masked_content),
            "advanced_commands_export": find_all_lower(PATTERNS.advcommand["export"], masked_content),
            "advanced_commands_export_ascii": find_all_lower(PATTERNS.advcommand["export_ascii"], masked_content),
            "advanced_commands_export_latex": find_all_lower(PATTERNS.advcommand["export_latex"], masked_content),
            "advanced_commands_caution": find_all_lower(PATTERNS.advcommand["caution"], masked_content),
            "advanced_commands_center": find_all_lower(PATTERNS.advcommand["center"], masked_content),
            "advanced_commands_comment": find_all_lower(PATTERNS.advcommand["comment"], masked_content),
            "advanced_commands_example": find_all_lower(PATTERNS.advcommand["example"], masked_content),
            "advanced_commands_important": find_all_lower(PATTERNS.advcommand["important"], masked_content),
            "advanced_commands_note": find_all_lower(PATTERNS.advcommand["note"], masked_content),
            "advanced_commands_pinned": find_all_lower(PATTERNS.advcommand["pinned"], masked_content),
            "advanced_commands_query": find_all_lower(PATTERNS.advcommand["query"], masked_content),
            "advanced_commands_quote": find_all_lower(PATTERNS.advcommand["quote"], masked_content),
            "advanced_commands_tip": find_all_lower(PATTERNS.advcommand["tip"], masked_content),
            "advanced_commands_verse": find_all_lower(PATTERNS.advcommand["verse"], masked_content),
            "advanced_commands_warning": find_all_lower(PATTERNS.advcommand["warning"], masked_content),
            # Basic content
            "assets": find_all_lower(PATTERNS.content["asset"], masked_content),
            "block_references": find_all_lower(PATTERNS.content["block_reference"], masked_content),
            "blockquotes": find_all_lower(PATTERNS.content["blockquote"], masked_content),
            "draws": find_all_lower(PATTERNS.content["draw"], masked_content),
            "flashcards": find_all_lower(PATTERNS.content["flashcard"], masked_content),
            "page_references": find_all_lower(PATTERNS.content["page_reference"], masked_content),
            "references_general": find_all_lower(PATTERNS.content["reference"], masked_content),
            "tagged_backlinks": find_all_lower(PATTERNS.content["tagged_backlink"], masked_content),
            "tags": find_all_lower(PATTERNS.content["tag"], masked_content),
            "dynamic_variables": find_all_lower(PATTERNS.content["dynamic_variable"], masked_content),
            # Double curly braces family
            "macros": find_all_lower(PATTERNS.dblcurly["_all"], masked_content),
            "embeds": find_all_lower(PATTERNS.dblcurly["embed"], masked_content),
            "page_embeds": find_all_lower(PATTERNS.dblcurly["page_embed"], masked_content),
            "block_embeds": find_all_lower(PATTERNS.dblcurly["block_embed"], masked_content),
            "namespace_queries": find_all_lower(PATTERNS.dblcurly["namespace_query"], masked_content),
            "cards": find_all_lower(PATTERNS.dblcurly["card"], masked_content),
            "clozes": find_all_lower(PATTERNS.dblcurly["cloze"], masked_content),
            "simple_queries": find_all_lower(PATTERNS.dblcurly["simple_query"], masked_content),
            "query_functions": find_all_lower(PATTERNS.dblcurly["query_function"], masked_content),
            "embed_video_urls": find_all_lower(PATTERNS.dblcurly["embed_video_url"], masked_content),
            "embed_twitter_tweets": find_all_lower(PATTERNS.dblcurly["embed_twitter_tweet"], masked_content),
            "embed_youtube_timestamps": find_all_lower(PATTERNS.dblcurly["embed_youtube_timestamp"], masked_content),
            "renderers": find_all_lower(PATTERNS.dblcurly["renderer"], masked_content),
        }

        # Extract all properties: values pairs
        properties_values = {}
        property_value_all = PATTERNS.content["property_value"].findall(masked_content)
        for prop, value in property_value_all:
            unmasked_value = self.unmask_code_blocks(value, code_blocks)
            properties_values[prop] = unmasked_value

        aliases = properties_values.get("alias")
        if aliases:
            masked_aliases = self.unmask_code_blocks(aliases, code_blocks)
            aliases = process_aliases(masked_aliases)

        # Extract page/block properties
        page_properties = []
        if self.is_primary_bullet_page_properties():
            masked_primary_bullet, _ = self.mask_code_blocks(self.primary_bullet)
            page_properties = find_all_lower(PATTERNS.content["property"], masked_primary_bullet)
            masked_content_bullets = []
            for bullet in self.content_bullets:
                masked_bullet, _ = self.mask_code_blocks(bullet)
                masked_content_bullets.append(masked_bullet)
            masked_content = "\n".join(masked_content_bullets)
        block_properties = find_all_lower(PATTERNS.content["property"], masked_content)

        properties_page_builtin, properties_page_user = LogseqFile.split_builtin_user_properties(page_properties)
        properties_block_builtin, properties_block_user = LogseqFile.split_builtin_user_properties(block_properties)

        # Process external and embedded links
        external_links = find_all_lower(PATTERNS.ext_links["external_link"], masked_content)
        embedded_links = find_all_lower(PATTERNS.emb_links["embedded_link"], masked_content)
        ext_links_other, ext_links_internet, ext_links_alias = LogseqFile.process_external_links(external_links)
        emb_links_other, emb_links_internet, emb_links_asset = LogseqFile.process_embedded_links(embedded_links)

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

    def mask_code_blocks(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace code blocks with placeholders to protect them from pattern matching.

        Args:
            content (str): The content to mask.

        Returns:
            Tuple[str, Dict[str, str]]: Masked content and a dictionary mapping placeholders to original code blocks.
        """
        # First mask multiline code blocks
        code_blocks = {}
        masked_content = content

        # Handle multiline code blocks first (```code blocks```)
        for match in PATTERNS.code["multiline_code_block"].finditer(content):
            block_id = f"__CODE_BLOCK_{uuid.uuid4()}__"
            code_blocks[block_id] = match.group(0)
            # Replace in masked content
            masked_content = masked_content.replace(match.group(0), block_id)

        # Then handle inline code blocks (`code`)
        for match in PATTERNS.code["inline_code_block"].finditer(masked_content):
            block_id = f"__INLINE_CODE_{uuid.uuid4()}__"
            code_blocks[block_id] = match.group(0)
            # Replace in masked content
            masked_content = masked_content.replace(match.group(0), block_id)

        return masked_content, code_blocks

    def unmask_code_blocks(self, masked_content: str, code_blocks: Dict[str, str]) -> str:
        """
        Restore code blocks from placeholders.

        Args:
            masked_content (str): Content with code block placeholders.
            code_blocks (Dict[str, str]): Mapping of placeholders to original code blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = masked_content
        for placeholder, code_block in code_blocks.items():
            content = content.replace(placeholder, code_block)
        return content

    def check_is_backlinked(self, lookup: Set[str]) -> bool:
        """
        Helper function to check if a file is backlinked.
        """
        try:
            lookup.remove(self.name)
            return True
        except KeyError:
            return False

    @staticmethod
    def process_external_links(
        external_links: List[str],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Process external links and categorize them."""
        internet = []
        alias = []
        if external_links:
            for _ in range(len(external_links)):
                link = external_links[-1]
                if PATTERNS.ext_links["external_link_internet"].match(link):
                    internet.append(link)
                    external_links.pop()
                    continue

                if PATTERNS.ext_links["external_link_alias"].match(link):
                    alias.append(link)
                    external_links.pop()
                    continue
        return external_links, internet, alias

    @staticmethod
    def process_embedded_links(
        embedded_links: List[str],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Process embedded links and categorize them."""
        internet = []
        asset = []
        if embedded_links:
            for _ in range(len(embedded_links)):
                link = embedded_links[-1]
                if PATTERNS.emb_links["embedded_link_internet"].match(link):
                    internet.append(link)
                    embedded_links.pop()
                    continue

                if PATTERNS.emb_links["embedded_link_asset"].match(link):
                    asset.append(link)
                    embedded_links.pop()
                    continue
        return embedded_links, internet, asset

    @staticmethod
    def split_builtin_user_properties(properties: list) -> Tuple[list, list]:
        """Helper function to split properties into built-in and user-defined."""
        builtin_props = [prop for prop in properties if prop in ANALYZER_CONFIG.built_in_properties]
        user_props = [prop for prop in properties if prop not in ANALYZER_CONFIG.built_in_properties]
        return builtin_props, user_props


@dataclass
class LogseqFileHash:
    """A class to represent a Logseq file hash."""

    file: LogseqFile

    def __repr__(self):
        """
        Return the string representation of the LogseqFileHash object.
        """
        return f"LogseqFileHash(key={self.__key()}, hash={self.__hash__()})"

    def __key(self):
        """
        Return the key for the LogseqFileHash object.
        """
        return (self.file.name, self.file.parent, self.file.suffix)

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
