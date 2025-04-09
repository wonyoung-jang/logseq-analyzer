"""
LogseqFile class to process Logseq files.
"""

from collections import defaultdict
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
        }

        # Process aliases and property:values
        properties_values = {}
        property_value_all = PATTERNS.content["property_value"].findall(masked_content)
        for prop, value in property_value_all:
            unmasked_value = self.unmask_code_blocks(value, code_blocks)
            properties_values[prop] = unmasked_value

        aliases = properties_values.get("alias")
        if aliases:
            masked_aliases = self.unmask_code_blocks(aliases, code_blocks)
            aliases = process_aliases(masked_aliases)

        # Process properties
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
        prop_page_builtin, prop_page_user = LogseqFile.split_builtin_user_properties(page_properties)
        prop_block_builtin, prop_block_user = LogseqFile.split_builtin_user_properties(block_properties)

        # Process external links
        external_links = find_all_lower(PATTERNS.ext_links["_all"], masked_content)
        external_links_family = LogseqFile.process_external_links(external_links)
        primary_data.update(external_links_family)

        # Process embedded links
        embedded_links = find_all_lower(PATTERNS.emb_links["_all"], masked_content)
        embedded_links_family = LogseqFile.process_embedded_links(embedded_links)
        primary_data.update(embedded_links_family)

        # Process double curly braces
        double_curly = find_all_lower(PATTERNS.dblcurly["_all"], masked_content)
        double_curly_family = LogseqFile.process_double_curly_braces(double_curly)
        primary_data.update(double_curly_family)

        # Process advanced commands
        advanced_commands = find_all_lower(PATTERNS.advcommand["_all"], masked_content)
        advanced_command_family = LogseqFile.process_advanced_commands(advanced_commands)
        primary_data.update(advanced_command_family)

        primary_data.update(
            {
                "aliases": aliases,
                "properties_block_builtin": prop_block_builtin,
                "properties_block_user": prop_block_user,
                "properties_page_builtin": prop_page_builtin,
                "properties_page_user": prop_page_user,
                "properties_values": properties_values,
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
    def process_external_links(results: List[str]):
        """Process external links and categorize them."""
        external_links_family = defaultdict(list)
        if results:
            for _ in range(len(results)):
                result = results[-1]
                if PATTERNS.ext_links["external_link_internet"].match(result):
                    external_links_family["external_links_internet"].append(result)
                    results.pop()
                    continue
                if PATTERNS.ext_links["external_link_alias"].match(result):
                    external_links_family["external_links_alias"].append(result)
                    results.pop()
                    continue
        external_links_family["external_links_other"] = results
        return external_links_family

    @staticmethod
    def process_embedded_links(results: List[str]):
        """Process embedded links and categorize them."""
        embedded_links_family = defaultdict(list)
        if results:
            for _ in range(len(results)):
                result = results[-1]
                if PATTERNS.emb_links["embedded_link_internet"].match(result):
                    embedded_links_family["embedded_links_internet"].append(result)
                    results.pop()
                    continue
                if PATTERNS.emb_links["embedded_link_asset"].match(result):
                    embedded_links_family["embedded_links_asset"].append(result)
                    results.pop()
                    continue
        embedded_links_family["embedded_links_other"] = results
        return embedded_links_family

    @staticmethod
    def split_builtin_user_properties(properties: list) -> Tuple[list, list]:
        """Helper function to split properties into built-in and user-defined."""
        builtin_props = [prop for prop in properties if prop in ANALYZER_CONFIG.built_in_properties]
        user_props = [prop for prop in properties if prop not in ANALYZER_CONFIG.built_in_properties]
        return builtin_props, user_props

    @staticmethod
    def process_double_curly_braces(results: List[str]):
        """Process double curly braces and extract relevant data."""
        double_curly_family = defaultdict(list)
        if results:
            for _ in range(len(results)):
                result = results[-1]
                if PATTERNS.dblcurly["embed"].match(result):
                    double_curly_family["embeds"].append(result)
                    results.pop()
                    if PATTERNS.dblcurly["page_embed"].match(result):
                        double_curly_family["page_embeds"].append(result)
                        double_curly_family["embeds"].remove(result)
                        continue
                    if PATTERNS.dblcurly["block_embed"].match(result):
                        double_curly_family["block_embeds"].append(result)
                        double_curly_family["embeds"].remove(result)
                        continue
                if PATTERNS.dblcurly["namespace_query"].match(result):
                    double_curly_family["namespace_queries"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["card"].match(result):
                    double_curly_family["cards"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["cloze"].match(result):
                    double_curly_family["clozes"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["simple_query"].match(result):
                    double_curly_family["simple_queries"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["query_function"].match(result):
                    double_curly_family["query_functions"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["embed_video_url"].match(result):
                    double_curly_family["embed_video_urls"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["embed_twitter_tweet"].match(result):
                    double_curly_family["embed_twitter_tweets"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["embed_youtube_timestamp"].match(result):
                    double_curly_family["embed_youtube_timestamps"].append(result)
                    results.pop()
                    continue
                if PATTERNS.dblcurly["renderer"].match(result):
                    double_curly_family["renderers"].append(result)
                    results.pop()
                    continue
        double_curly_family["macros"] = results
        return double_curly_family

    @staticmethod
    def process_advanced_commands(results: List[str]):
        """Process advanced commands and extract relevant data."""
        advanced_command_family = defaultdict(list)
        if results:
            for _ in range(len(results)):
                result = results[-1]
                if PATTERNS.advcommand["export"].match(result):
                    advanced_command_family["advanced_commands_export"].append(result)
                    results.pop()
                    if PATTERNS.advcommand["export_ascii"].match(result):
                        advanced_command_family["advanced_commands_export_ascii"].append(result)
                        advanced_command_family["advanced_commands_export"].pop()
                        continue
                    if PATTERNS.advcommand["export_latex"].match(result):
                        advanced_command_family["advanced_commands_export_latex"].append(result)
                        advanced_command_family["advanced_commands_export"].pop()
                        continue
                if PATTERNS.advcommand["caution"].match(result):
                    advanced_command_family["advanced_commands_caution"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["center"].match(result):
                    advanced_command_family["advanced_commands_center"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["comment"].match(result):
                    advanced_command_family["advanced_commands_comment"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["example"].match(result):
                    advanced_command_family["advanced_commands_example"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["important"].match(result):
                    advanced_command_family["advanced_commands_important"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["note"].match(result):
                    advanced_command_family["advanced_commands_note"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["pinned"].match(result):
                    advanced_command_family["advanced_commands_pinned"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["query"].match(result):
                    advanced_command_family["advanced_commands_query"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["quote"].match(result):
                    advanced_command_family["advanced_commands_quote"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["tip"].match(result):
                    advanced_command_family["advanced_commands_tip"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["verse"].match(result):
                    advanced_command_family["advanced_commands_verse"].append(result)
                    results.pop()
                    continue
                if PATTERNS.advcommand["warning"].match(result):
                    advanced_command_family["advanced_commands_warning"].append(result)
                    results.pop()
                    continue
        advanced_command_family["advanced_commands"] = results
        return advanced_command_family


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
