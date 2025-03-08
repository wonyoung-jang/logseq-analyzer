"""
LogseqFile class to represent a Logseq file.
This class contains metadata about the file, including its name, path, creation date, modification date, and content.
"""

from collections import defaultdict
from datetime import datetime
import logging
import os
from pathlib import Path
from pprint import pprint
import re
from urllib.parse import unquote

from src.compile_regex import compile_re_content
import src.config as config
PROPS = config.BUILT_IN_PROPERTIES
PATTERNS = compile_re_content()

class LogseqFile:
    def __init__(self, file_path: Path):
        # Basic file attributes
        self.id = None
        self.name = None
        self.name_secondary = None
        self.file_path = None
        self.file_path_parent_name = None
        self.file_path_name = None
        self.file_path_suffix = None
        self.file_path_parts = None

        # Date/time attributes
        self.date_created = None
        self.date_modified = None
        self.time_existed = None
        self.time_unmodified = None

        # Content stats
        self.size = None
        self.uri = None
        self.char_count = None
        self.bullet_count = None
        self.bullet_density = None
        
        # Content
        self.content = None
        
        self.aliases = []
        self.page_references = []
        self.tags = []
        self.tagged_backlinks = []
        self.properties_values = []
        self.properties_page_builtin = []
        self.properties_page_user = []
        self.properties_block_builtin = []
        self.properties_block_user = []
        self.assets = []
        self.draws = []
        self.namespace_root = ""
        self.namespace_parent = ""
        self.namespace_parts = {}
        self.namespace_level = -1
        self.namespace_queries = []
        self.external_links = []
        self.external_links_internet = []
        self.external_links_alias = []
        self.embedded_links = []
        self.embedded_links_internet = []
        self.embedded_links_asset = []
        self.blockquotes = []
        self.flashcards = []
        
        # Initialize all attributes
        self.initialize_all(file_path)
        
        # Process content data
        self.process_content_data()
        
    def __repr__(self):
        return f"{self.__class__.__qualname__} - {self.name}"
    
    def __str__(self):
        return f"{self.__class__.__qualname__} - {self.name}"
   
    def __dict__(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_secondary": self.name_secondary,
            "file_path": self.file_path,
            "file_path_parent_name": self.file_path_parent_name,
            "file_path_name": self.file_path_name,
            "file_path_suffix": self.file_path_suffix,
            "file_path_parts": self.file_path_parts,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "time_existed": self.time_existed,
            "time_unmodified": self.time_unmodified,
            "size": self.size,
            "uri": self.uri,
            "char_count": self.char_count,
            "bullet_count": self.bullet_count,
            "bullet_density": self.bullet_density,
            # "content": self.content,
            "aliases": self.aliases,
            "page_references": self.page_references,
            "tags": self.tags,
            "tagged_backlinks": self.tagged_backlinks,
            "properties_values": self.properties_values,
            "properties_page_builtin": self.properties_page_builtin,
            "properties_page_user": self.properties_page_user,
            "properties_block_builtin": self.properties_block_builtin,
            "properties_block_user": self.properties_block_user,
            "assets": self.assets,
            "draws": self.draws,
            "namespace_root": self.namespace_root,
            "namespace_parent": self.namespace_parent,
            "namespace_parts": self.namespace_parts,
            "namespace_level": self.namespace_level,
            "namespace_queries": self.namespace_queries,
            "external_links": self.external_links,
            "external_links_internet": self.external_links_internet,
            "external_links_alias": self.external_links_alias,
            "embedded_links": self.embedded_links,
            "embedded_links_internet": self.embedded_links_internet,
            "embedded_links_asset": self.embedded_links_asset,
            "blockquotes": self.blockquotes,
            "flashcards": self.flashcards
        }
        
    def initialize_all(self, file_path: Path):
        stat = file_path.stat()
        self.set_basic_file_attributes(file_path)
        self.set_datetime_attributes(file_path, stat)
        self.set_content_stats(file_path, stat)

    def set_basic_file_attributes(self, file_path: Path):
        parent = file_path.parent.name
        name = self.process_filename_key(file_path.stem, parent)
        suffix = file_path.suffix.lower() if file_path.suffix else None

        self.id = name[:2].lower() if len(name) > 1 else f"!{name[0].lower()}"
        self.name = name
        self.name_secondary = f"{name} {parent} + {suffix}".lower()
        self.file_path = str(file_path)
        self.file_path_parent_name = parent.lower()
        self.file_path_name = name.lower()
        self.file_path_suffix = suffix.lower() if suffix else None
        self.file_path_parts = file_path.parts

    def set_datetime_attributes(self, file_path: Path, stat: os.stat_result):
        now = datetime.now().replace(microsecond=0)
        try:
            self.date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
        except AttributeError:
            self.date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
            logging.warning(f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.")
        self.date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)
        self.time_existed = now - self.date_created
        self.time_unmodified = now - self.date_modified

    def set_content_stats(self, file_path: Path, stat: os.stat_result):
        self.size = stat.st_size
        self.uri = file_path.as_uri()
        
        self.content = None
        try:
            self.content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning(f"File not found: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to read file {file_path}: {e}")

        if self.content:
            self.char_count = len(self.content)
            bullet_count = len(PATTERNS["bullet"].findall(self.content))
            self.bullet_count = bullet_count
            self.bullet_density = self.char_count // bullet_count if bullet_count > 0 else 0
 
    def transform_date_format(self, cljs_format: str) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.

        Args:
            cljs_format (str): Clojure-style date format.

        Returns:
            str: Python-style date format.
        """

        def replace_token(match):
            token = match.group(0)
            return config.DATETIME_TOKEN_MAP.get(token, token)

        py_format = config.DATETIME_TOKEN_PATTERN.sub(replace_token, cljs_format)
        return py_format

    def process_journal_key(self, key: str) -> str:
        """
        Process the journal key by converting it to a page title format.

        Args:
            key (str): The journal key (filename stem).

        Returns:
            str: Processed journal key as a page title.
        """
        page_title_format = config.JOURNAL_PAGE_TITLE_FORMAT
        file_name_format = config.JOURNAL_FILE_NAME_FORMAT
        py_file_name_format = self.transform_date_format(file_name_format)
        py_page_title_format = self.transform_date_format(page_title_format)

        try:
            date_object = datetime.strptime(key, py_file_name_format)
            page_title = date_object.strftime(py_page_title_format).lower()
            return page_title
        except ValueError:
            logging.warning(f"Could not parse journal key as date: {key}. Returning original key.")
            return key

    def process_filename_key(self, key: str, parent: str) -> str:
        """
        Process the key name by removing the parent name and formatting it.

        For 'journals' parent, it formats the key as 'day-month-year dayOfWeek'.
        For other parents, it unquotes URL-encoded characters and replaces '___' with '/'.

        Args:
            key (str): The key name (filename stem).
            parent (str): The parent directory name.

        Returns:
            str: Processed key name.
        """
        if parent == config.DIR_JOURNALS:
            return self.process_journal_key(key)

        if key.endswith(config.NAMESPACE_FILE_SEP):
            key = key.rstrip(config.NAMESPACE_FILE_SEP)

        return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()

    def process_content_data(self):
        # TODO complete
        if not self.content:
            logging.debug(f"File {self.file_path} has no content to process.")
            return
        
        # Process content data
        self.page_references = [page_ref.lower() for page_ref in PATTERNS["page_reference"].findall(self.content)]
        self.tags = [tag.lower() for tag in PATTERNS["tag"].findall(self.content)]
        self.tagged_backlinks = [tag.lower() for tag in PATTERNS["tagged_backlink"].findall(self.content)]
        self.assets = [asset.lower() for asset in PATTERNS["asset"].findall(self.content)]
        self.draws = [draw.lower() for draw in PATTERNS["draw"].findall(self.content)]
        self.namespace_queries = [query.lower() for query in PATTERNS["namespace_query"].findall(self.content)]
        self.properties_values = {prop: value for prop, value in PATTERNS["property_values"].findall(self.content)}
        self.blockquotes = [quote.lower() for quote in PATTERNS["blockquote"].findall(self.content)]
        self.flashcards = [card.lower() for card in PATTERNS["flashcard"].findall(self.content)]
        
        external_links = [link.lower() for link in PATTERNS["external_link"].findall(self.content)]
        embedded_links = [link.lower() for link in PATTERNS["embedded_link"].findall(self.content)]
        
    def extract_properties(self):
        """Extract page and block properties from text using a combined regex search."""
        # The regex groups a heading marker or a bullet marker.
        split_match = re.search(r"^\s*(#+\s|-\s)", self.content, re.MULTILINE)

        if split_match:
            split_point = split_match.start()
            page_text = self.content[:split_point]
            block_text = self.content[split_point:]
        else:
            page_text = self.content
            block_text = ""

        page_properties = [prop.lower() for prop in PATTERNS["property"].findall(page_text)]
        block_properties = [prop.lower() for prop in PATTERNS["property"].findall(block_text)]
        return page_properties, block_properties


    def categorize_properties(self, properties: list, built_in_props):
        """Helper function to split properties into built-in and user-defined."""
        builtin_props = [prop for prop in properties if prop in built_in_props]
        user_props = [prop for prop in properties if prop not in built_in_props]
        return builtin_props, user_props
        
