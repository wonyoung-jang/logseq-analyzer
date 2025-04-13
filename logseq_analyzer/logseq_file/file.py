"""
LogseqFile class to process Logseq files.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import uuid

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import find_all_lower, process_aliases
from ..utils.patterns import RegexPatterns
from ..utils.enums import Criteria
from .bullets import LogseqBullets
from .name import LogseqFilename
from .stats import LogseqFilestats

PATTERNS = RegexPatterns()
ANALYZER_CONFIG = LogseqAnalyzerConfig()
NS_SEP = ANALYZER_CONFIG.config["CONST"]["NAMESPACE_SEP"]


class LogseqFile:
    """A class to represent a Logseq file."""

    def __init__(self, file_path: Path):
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path = file_path
        self.masked_blocks = {}
        self.path = LogseqFilename(self.file_path)
        self.stat = LogseqFilestats(self.file_path)
        self.bullets = LogseqBullets(self.file_path)
        self.content = ""
        self.data = {}
        self.primary_bullet = ""
        self.content_bullets = []
        self.has_content = False
        self.has_backlinks = False
        self.is_backlinked = False
        self.is_backlinked_by_ns_only = False
        self.node_type = "other"
        self.file_type = "other"

    def __repr__(self) -> str:
        return f"LogseqFile(name={self.path.name}, path={self.file_path})"

    def __hash__(self) -> int:
        return hash(self.path.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def init_file_data(self):
        """
        Extract metadata from a file.
        """
        self.path.determine_file_type()
        self.path.process_logseq_filename()
        self.path.convert_uri_to_logseq_url()
        self.path.get_namespace_name_data()
        for attr, value in self.path.__dict__.items():
            setattr(self, attr, value)

        for attr, value in self.stat.__dict__.items():
            setattr(self, attr, value)

        self.bullets.get_content()
        self.bullets.get_char_count()
        self.bullets.get_bullet_content()
        self.bullets.get_primary_bullet()
        self.bullets.get_bullet_density()
        self.bullets.is_primary_bullet_page_properties()
        for attr, value in self.bullets.__dict__.items():
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
        masked_content, masked_blocks = self.mask_blocks(self.content)
        self.masked_blocks = masked_blocks

        # Extract basic data
        primary_data = {
            # Code blocks
            Criteria.INLINE_CODE_BLOCKS.value: find_all_lower(PATTERNS.code["inline_code_block"], self.content),
            # Captures from all content
            Criteria.ASSETS.value: find_all_lower(PATTERNS.content["asset"], self.content),
            Criteria.ANY_LINKS.value: find_all_lower(PATTERNS.content["any_link"], self.content),
            # Basic content
            Criteria.BLOCKQUOTES.value: find_all_lower(PATTERNS.content["blockquote"], masked_content),
            Criteria.DRAWS.value: find_all_lower(PATTERNS.content["draw"], masked_content),
            Criteria.FLASHCARDS.value: find_all_lower(PATTERNS.content["flashcard"], masked_content),
            Criteria.PAGE_REFERENCES.value: find_all_lower(PATTERNS.content["page_reference"], masked_content),
            Criteria.TAGGED_BACKLINKS.value: find_all_lower(PATTERNS.content["tagged_backlink"], masked_content),
            Criteria.TAGS.value: find_all_lower(PATTERNS.content["tag"], masked_content),
            Criteria.DYNAMIC_VARIABLES.value: find_all_lower(PATTERNS.content["dynamic_variable"], masked_content),
        }

        # Process aliases and property:values
        property_value_all = PATTERNS.content["property_value"].findall(self.content)
        properties_values = dict(property_value_all)
        if aliases := properties_values.get("alias"):
            aliases = process_aliases(aliases)

        # Process properties
        page_properties = []
        if self.bullets.has_page_properties:
            page_properties = find_all_lower(PATTERNS.content["property"], self.primary_bullet)
            self.content = "\n".join(self.content_bullets)
        block_properties = find_all_lower(PATTERNS.content["property"], self.content)
        page_props = LogseqFile.split_builtin_user_properties(page_properties)
        block_props = LogseqFile.split_builtin_user_properties(block_properties)

        # Process code blocks
        code_pattern = find_all_lower(PATTERNS.code["_all"], self.content)
        code_family = LogseqFile.process_code_blocks(code_pattern)
        primary_data.update(code_family)

        # Process double parentheses
        double_paren_pattern = find_all_lower(PATTERNS.dblparen["_all"], self.content)
        double_paren_family = LogseqFile.process_double_parens(double_paren_pattern)
        primary_data.update(double_paren_family)

        # Process external links
        external_links = find_all_lower(PATTERNS.ext_links["_all"], self.content)
        external_links_family = LogseqFile.process_external_links(external_links)
        primary_data.update(external_links_family)

        # Process embedded links
        embedded_links = find_all_lower(PATTERNS.emb_links["_all"], self.content)
        embedded_links_family = LogseqFile.process_embedded_links(embedded_links)
        primary_data.update(embedded_links_family)

        # Process double curly braces
        double_curly = find_all_lower(PATTERNS.dblcurly["_all"], self.content)
        double_curly_family = LogseqFile.process_double_curly_braces(double_curly)
        primary_data.update(double_curly_family)

        # Process advanced commands
        advanced_commands = find_all_lower(PATTERNS.advcommand["_all"], self.content)
        advanced_command_family = LogseqFile.process_advanced_commands(advanced_commands)
        primary_data.update(advanced_command_family)

        primary_data.update(
            {
                Criteria.ALIASES.value: aliases,
                Criteria.PROPERTIES_BLOCK_BUILTIN.value: block_props["built_in"],
                Criteria.PROPERTIES_BLOCK_USER.value: block_props["user_props"],
                Criteria.PROPERTIES_PAGE_BUILTIN.value: page_props["built_in"],
                Criteria.PROPERTIES_PAGE_USER.value: page_props["user_props"],
                Criteria.PROPERTIES_VALUES.value: properties_values,
            }
        )

        for key, value in primary_data.items():
            if value:
                self.data[key] = value
                if not self.has_backlinks:
                    if key in ("page_references", "tags", "tagged_backlinks") or "properties" in key:
                        self.has_backlinks = True

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

    def mask_blocks(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask code blocks and other patterns in the content.

        Args:
            content (str): The content to mask.

        Returns:
            Tuple[str, Dict[str, str]]: Masked content and a dictionary mapping placeholders to original blocks.
        """
        masked_blocks = {}
        masked_content = content

        for match in PATTERNS.code["_all"].finditer(content):
            block_id = f"__CODE_BLOCK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.code["inline_code_block"].finditer(masked_content):
            block_id = f"__INLINE_CODE_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.advcommand["_all"].finditer(masked_content):
            block_id = f"__ADV_COMMAND_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.dblcurly["_all"].finditer(masked_content):
            block_id = f"__DOUBLE_CURLY_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.emb_links["_all"].finditer(masked_content):
            block_id = f"__EMB_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.ext_links["_all"].finditer(masked_content):
            block_id = f"__EXT_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.dblparen["_all"].finditer(masked_content):
            block_id = f"__DBLPAREN_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in PATTERNS.content["any_link"].finditer(masked_content):
            block_id = f"__ANY_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        return masked_content, masked_blocks

    def unmask_blocks(self, masked_content: str, masked_blocks: Dict[str, str]) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Args:
            masked_content (str): Content with code block placeholders.
            masked_blocks (Dict[str, str]): Mapping of placeholders to original code blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = masked_content
        for placeholder, block in masked_blocks.items():
            content = content.replace(placeholder, block)
        return content

    def check_is_backlinked(self, lookup: Set[str]) -> bool:
        """
        Helper function to check if a file is backlinked.
        """
        try:
            lookup.remove(self.path.name)
            return True
        except KeyError:
            return False

    @staticmethod
    def process_code_blocks(results: List[str]):
        """Process code blocks and categorize them."""
        code_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.code["calc_block"].search(result):
                code_family["calc_blocks"].append(result)
                results.pop()
                continue
            if PATTERNS.code["multiline_code_lang"].search(result):
                code_family["multiline_code_langs"].append(result)
                results.pop()
                continue
        code_family["multiline_code_blocks"] = results
        return code_family

    @staticmethod
    def process_double_parens(results: List[str]):
        """Process double parentheses and categorize them."""
        double_paren_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.dblparen["block_reference"].search(result):
                double_paren_family["block_references"].append(result)
                results.pop()
                continue
        double_paren_family["references_general"] = results
        return double_paren_family

    @staticmethod
    def process_external_links(results: List[str]):
        """Process external links and categorize them."""
        external_links_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.ext_links["external_link_internet"].search(result):
                external_links_family["external_links_internet"].append(result)
                results.pop()
                continue
            if PATTERNS.ext_links["external_link_alias"].search(result):
                external_links_family["external_links_alias"].append(result)
                results.pop()
                continue
        external_links_family["external_links_other"] = results
        return external_links_family

    @staticmethod
    def process_embedded_links(results: List[str]):
        """Process embedded links and categorize them."""
        embedded_links_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.emb_links["embedded_link_internet"].search(result):
                embedded_links_family["embedded_links_internet"].append(result)
                results.pop()
                continue
            if PATTERNS.emb_links["embedded_link_asset"].search(result):
                embedded_links_family["embedded_links_asset"].append(result)
                results.pop()
                continue
        embedded_links_family["embedded_links_other"] = results
        return embedded_links_family

    @staticmethod
    def split_builtin_user_properties(properties: list) -> Dict[str, List[str]]:
        """Helper function to split properties into built-in and user-defined."""
        properties_dict = {
            "built_in": [prop for prop in properties if prop in ANALYZER_CONFIG.built_in_properties],
            "user_props": [prop for prop in properties if prop not in ANALYZER_CONFIG.built_in_properties],
        }
        return properties_dict

    @staticmethod
    def process_double_curly_braces(results: List[str]):
        """Process double curly braces and extract relevant data."""
        double_curly_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.dblcurly["embed"].search(result):
                double_curly_family["embeds"].append(result)
                results.pop()
                if PATTERNS.dblcurly["page_embed"].search(result):
                    double_curly_family["page_embeds"].append(result)
                    double_curly_family["embeds"].remove(result)
                    continue
                if PATTERNS.dblcurly["block_embed"].search(result):
                    double_curly_family["block_embeds"].append(result)
                    double_curly_family["embeds"].remove(result)
                    continue
            if PATTERNS.dblcurly["namespace_query"].search(result):
                double_curly_family["namespace_queries"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["card"].search(result):
                double_curly_family["cards"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["cloze"].search(result):
                double_curly_family["clozes"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["simple_query"].search(result):
                double_curly_family["simple_queries"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["query_function"].search(result):
                double_curly_family["query_functions"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["embed_video_url"].search(result):
                double_curly_family["embed_video_urls"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["embed_twitter_tweet"].search(result):
                double_curly_family["embed_twitter_tweets"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["embed_youtube_timestamp"].search(result):
                double_curly_family["embed_youtube_timestamps"].append(result)
                results.pop()
                continue
            if PATTERNS.dblcurly["renderer"].search(result):
                double_curly_family["renderers"].append(result)
                results.pop()
                continue
        double_curly_family["macros"] = results
        return double_curly_family

    @staticmethod
    def process_advanced_commands(results: List[str]):
        """Process advanced commands and extract relevant data."""
        advanced_command_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if PATTERNS.advcommand["export"].search(result):
                advanced_command_family["advanced_commands_export"].append(result)
                results.pop()
                if PATTERNS.advcommand["export_ascii"].search(result):
                    advanced_command_family["advanced_commands_export_ascii"].append(result)
                    advanced_command_family["advanced_commands_export"].pop()
                    continue
                if PATTERNS.advcommand["export_latex"].search(result):
                    advanced_command_family["advanced_commands_export_latex"].append(result)
                    advanced_command_family["advanced_commands_export"].pop()
                    continue
            if PATTERNS.advcommand["caution"].search(result):
                advanced_command_family["advanced_commands_caution"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["center"].search(result):
                advanced_command_family["advanced_commands_center"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["comment"].search(result):
                advanced_command_family["advanced_commands_comment"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["example"].search(result):
                advanced_command_family["advanced_commands_example"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["important"].search(result):
                advanced_command_family["advanced_commands_important"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["note"].search(result):
                advanced_command_family["advanced_commands_note"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["pinned"].search(result):
                advanced_command_family["advanced_commands_pinned"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["query"].search(result):
                advanced_command_family["advanced_commands_query"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["quote"].search(result):
                advanced_command_family["advanced_commands_quote"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["tip"].search(result):
                advanced_command_family["advanced_commands_tip"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["verse"].search(result):
                advanced_command_family["advanced_commands_verse"].append(result)
                results.pop()
                continue
            if PATTERNS.advcommand["warning"].search(result):
                advanced_command_family["advanced_commands_warning"].append(result)
                results.pop()
                continue
        advanced_command_family["advanced_commands"] = results
        return advanced_command_family
