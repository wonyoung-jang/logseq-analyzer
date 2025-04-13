"""
LogseqFile class to process Logseq files.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import uuid

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import find_all_lower, process_aliases
from ..utils.patterns import (
    AdvancedCommandPatterns,
    ContentPatterns,
    DoubleCurlyBracketsPatterns,
    EmbeddedLinksPatterns,
    ExternalLinksPatterns,
    DoubleParenthesesPatterns,
    CodePatterns,
)
from ..utils.enums import Criteria
from .bullets import LogseqBullets
from .name import LogseqFilename
from .stats import LogseqFilestats

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
        self.embedded_links = EmbeddedLinksPatterns()
        self.external_links = ExternalLinksPatterns()
        self.double_parentheses = DoubleParenthesesPatterns()
        self.code = CodePatterns()
        self.content_patterns = ContentPatterns()
        self.double_curly_brackets = DoubleCurlyBracketsPatterns()
        self.advanced_commands = AdvancedCommandPatterns()

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
            Criteria.INLINE_CODE_BLOCKS.value: find_all_lower(self.code.inline_code_block, self.content),
            # Captures from all content
            Criteria.ASSETS.value: find_all_lower(self.content_patterns.asset, self.content),
            Criteria.ANY_LINKS.value: find_all_lower(self.content_patterns.any_link, self.content),
            # Basic content
            Criteria.BLOCKQUOTES.value: find_all_lower(self.content_patterns.blockquote, masked_content),
            Criteria.DRAWS.value: find_all_lower(self.content_patterns.draw, masked_content),
            Criteria.FLASHCARDS.value: find_all_lower(self.content_patterns.flashcard, masked_content),
            Criteria.PAGE_REFERENCES.value: find_all_lower(self.content_patterns.page_reference, masked_content),
            Criteria.TAGGED_BACKLINKS.value: find_all_lower(self.content_patterns.tagged_backlink, masked_content),
            Criteria.TAGS.value: find_all_lower(self.content_patterns.tag, masked_content),
            Criteria.DYNAMIC_VARIABLES.value: find_all_lower(self.content_patterns.dynamic_variable, masked_content),
        }

        # Process aliases and property:values
        property_value_all = self.content_patterns.property_value.findall(self.content)
        properties_values = dict(property_value_all)
        if aliases := properties_values.get("alias"):
            aliases = process_aliases(aliases)

        # Process properties
        page_properties = []
        if self.bullets.has_page_properties:
            page_properties = find_all_lower(self.content_patterns.property, self.primary_bullet)
            self.content = "\n".join(self.content_bullets)
        block_properties = find_all_lower(self.content_patterns.property, self.content)
        page_props = LogseqFile.split_builtin_user_properties(page_properties)
        block_props = LogseqFile.split_builtin_user_properties(block_properties)

        # Process code blocks
        code_pattern = find_all_lower(self.code.all, self.content)
        code_family = self.process_code_blocks(code_pattern)
        primary_data.update(code_family)

        # Process double parentheses
        double_paren_pattern = find_all_lower(self.double_parentheses.all, self.content)
        double_paren_family = self.process_double_parens(double_paren_pattern)
        primary_data.update(double_paren_family)

        # Process external links
        external_links = find_all_lower(self.external_links.all, self.content)
        external_links_family = self.process_external_links(external_links)
        primary_data.update(external_links_family)

        # Process embedded links
        embedded_links = find_all_lower(self.embedded_links.all, self.content)
        embedded_links_family = self.process_embedded_links(embedded_links)
        primary_data.update(embedded_links_family)

        # Process double curly braces
        double_curly = find_all_lower(self.double_curly_brackets.all, self.content)
        double_curly_family = self.process_double_curly_braces(double_curly)
        primary_data.update(double_curly_family)

        # Process advanced commands
        advanced_commands = find_all_lower(self.advanced_commands.all, self.content)
        advanced_command_family = self.process_advanced_commands(advanced_commands)
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

        for match in self.code.all.finditer(content):
            block_id = f"__CODE_BLOCK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.code.inline_code_block.finditer(masked_content):
            block_id = f"__INLINE_CODE_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.advanced_commands.all.finditer(masked_content):
            block_id = f"__ADV_COMMAND_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.double_curly_brackets.all.finditer(masked_content):
            block_id = f"__DOUBLE_CURLY_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.embedded_links.all.finditer(masked_content):
            block_id = f"__EMB_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.external_links.all.finditer(masked_content):
            block_id = f"__EXT_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.double_parentheses.all.finditer(masked_content):
            block_id = f"__DBLPAREN_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in self.content_patterns.any_link.finditer(masked_content):
            block_id = f"__ANY_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        return masked_content, masked_blocks

    @staticmethod
    def split_builtin_user_properties(properties: list) -> Dict[str, List[str]]:
        """Helper function to split properties into built-in and user-defined."""
        properties_dict = {
            "built_in": [prop for prop in properties if prop in ANALYZER_CONFIG.built_in_properties],
            "user_props": [prop for prop in properties if prop not in ANALYZER_CONFIG.built_in_properties],
        }
        return properties_dict

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

    def process_code_blocks(self, results: List[str]):
        """Process code blocks and categorize them."""
        code_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.code.calc_block.search(result):
                code_family[Criteria.CALC_BLOCKS.value].append(result)
                results.pop()
                continue
            if self.code.multiline_code_lang.search(result):
                code_family[Criteria.MULTILINE_CODE_LANGS.value].append(result)
                results.pop()
                continue
        code_family[Criteria.MULTILINE_CODE_BLOCKS.value] = results
        return code_family

    def process_double_parens(self, results: List[str]):
        """Process double parentheses and categorize them."""
        double_paren_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.double_parentheses.block_reference.search(result):
                double_paren_family[Criteria.BLOCK_REFERENCES.value].append(result)
                results.pop()
                continue
        double_paren_family[Criteria.REFERENCES_GENERAL.value] = results
        return double_paren_family

    def process_external_links(self, results: List[str]):
        """Process external links and categorize them."""
        external_links_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.external_links.internet.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if self.external_links.alias.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_ALIAS.value].append(result)
                results.pop()
                continue
        external_links_family[Criteria.EXTERNAL_LINKS_OTHER.value] = results
        return external_links_family

    def process_embedded_links(self, results: List[str]):
        """Process embedded links and categorize them."""
        embedded_links_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.embedded_links.internet.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if self.embedded_links.asset.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_ASSET.value].append(result)
                results.pop()
                continue
        embedded_links_family[Criteria.EMBEDDED_LINKS_OTHER.value] = results
        return embedded_links_family

    def process_double_curly_braces(self, results: List[str]):
        """Process double curly braces and extract relevant data."""
        double_curly_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.double_curly_brackets.embed.search(result):
                double_curly_family[Criteria.EMBEDS.value].append(result)
                results.pop()
                if self.double_curly_brackets.page_embed.search(result):
                    double_curly_family[Criteria.PAGE_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
                if self.double_curly_brackets.block_embed.search(result):
                    double_curly_family[Criteria.BLOCK_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
            if self.double_curly_brackets.namespace_query.search(result):
                double_curly_family[Criteria.NAMESPACE_QUERIES.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.card.search(result):
                double_curly_family[Criteria.CARDS.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.cloze.search(result):
                double_curly_family[Criteria.CLOZES.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.simple_query.search(result):
                double_curly_family[Criteria.SIMPLE_QUERIES.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.query_function.search(result):
                double_curly_family[Criteria.QUERY_FUNCTIONS.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.embed_video_url.search(result):
                double_curly_family[Criteria.EMBED_VIDEO_URLS.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.embed_twitter_tweet.search(result):
                double_curly_family[Criteria.EMBED_TWITTER_TWEETS.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.embed_youtube_timestamp.search(result):
                double_curly_family[Criteria.EMBED_YOUTUBE_TIMESTAMPS.value].append(result)
                results.pop()
                continue
            if self.double_curly_brackets.renderer.search(result):
                double_curly_family[Criteria.RENDERERS.value].append(result)
                results.pop()
                continue
        double_curly_family[Criteria.MACROS.value] = results
        return double_curly_family

    def process_advanced_commands(self, results: List[str]):
        """Process advanced commands and extract relevant data."""
        advanced_command_family = defaultdict(list)
        if not results:
            return {}
        for _ in range(len(results)):
            result = results[-1]
            if self.advanced_commands.export.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].append(result)
                results.pop()
                if self.advanced_commands.export_ascii.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_ASCII.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
                if self.advanced_commands.export_latex.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_LATEX.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
            if self.advanced_commands.caution.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CAUTION.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.center.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CENTER.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.comment.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_COMMENT.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.example.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXAMPLE.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.important.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_IMPORTANT.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.note.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_NOTE.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.pinned.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_PINNED.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.query.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUERY.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.quote.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUOTE.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.tip.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_TIP.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.verse.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_VERSE.value].append(result)
                results.pop()
                continue
            if self.advanced_commands.warning.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_WARNING.value].append(result)
                results.pop()
                continue
        advanced_command_family[Criteria.ADVANCED_COMMANDS.value] = results
        return advanced_command_family
