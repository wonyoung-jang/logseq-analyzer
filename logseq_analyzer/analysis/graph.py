"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from collections import defaultdict
from pathlib import Path
from typing import Dict

from ..config.builtin_properties import LogseqBuiltInProperties
from ..io.cache import Cache
from ..logseq_file.file import LogseqFile
from ..utils.enums import Output, Criteria


class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqGraph instance."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.cache = Cache()
            self.data = {}
            self.content_bullets = {}
            self.unique_linked_references = set()
            self.unique_linked_references_ns = set()
            self.all_linked_references = {}
            self.dangling_links = set()
            self.summary_file_subsets = {}
            self.summary_data_subsets = {}
            self.assets_backlinked = []
            self.assets_not_backlinked = []
            self.hashed_files: Dict[int, LogseqFile] = {}
            self.names_to_hashes = defaultdict(list)
            self.masked_blocks = {}
            self.logseq_builtin_properties = LogseqBuiltInProperties()
            self.logseq_builtin_properties.set_builtin_properties()

    def process_graph_files(self):
        """Process all files in the Logseq graph folder."""
        for file_path in self.cache.iter_modified_files():
            file = self.initialize_file(file_path)
            self.update_data_with_file(file)
            self.del_large_file_attributes(file)

    def initialize_file(self, file_path: Path) -> LogseqFile:
        """
        Initialize the file object.

        Args:
            file_path (Path): Path to the file to be initialized.

        Returns:
            LogseqFile: Initialized LogseqFile object.
        """
        file = LogseqFile(file_path, self.logseq_builtin_properties)
        file.init_file_data()
        file.process_content_data()
        return file

    def update_data_with_file(self, file: LogseqFile):
        """Update the graph data with a new file."""
        file_hash = hash(file)
        self.data[file_hash] = file.__dict__
        self.content_bullets[file_hash] = file.content_bullets
        self.hashed_files[file_hash] = file
        self.names_to_hashes[file.path.name].append(file_hash)
        self.masked_blocks[file_hash] = file.masked_blocks

    def del_large_file_attributes(self, file: LogseqFile):
        """Delete large attributes from the file object."""
        delattr(file, "content_bullets")
        delattr(file, "content")
        delattr(file, "primary_bullet")

    def update_graph_files_with_cache(self):
        """Update the graph files with cached data."""
        graph_data_db = self.cache.get(Output.GRAPH_DATA.value, {})
        graph_data_db.update(self.data)
        self.data = graph_data_db

        graph_content_db = self.cache.get(Output.GRAPH_CONTENT.value, {})
        graph_content_db.update(self.content_bullets)
        self.content_bullets = graph_content_db

        graph_hashed_files_db = self.cache.get(Output.GRAPH_HASHED_FILES.value, {})
        graph_hashed_files_db.update(self.hashed_files)
        self.hashed_files = graph_hashed_files_db

        graph_names_to_hashes_db = self.cache.get(Output.GRAPH_NAMES_TO_HASHES.value, {})
        graph_names_to_hashes_db.update(self.names_to_hashes)
        self.names_to_hashes = graph_names_to_hashes_db

        graph_dangling_links_db = self.cache.get(Output.DANGLING_LINKS.value, set())
        graph_dangling_links = {d for d in self.dangling_links if d not in graph_dangling_links_db}
        self.dangling_links = graph_dangling_links.union(graph_dangling_links_db)

    def post_processing_content(self):
        """Post-process the content data for all files."""
        unique_aliases = set()

        # Process each file's content
        for _, file in self.hashed_files.items():
            if file.path.is_namespace:
                self.post_processing_content_namespaces(file)

            found_aliases = file.data.get(Criteria.ALIASES.value, [])
            unique_aliases.update(found_aliases)
            linked_references = [
                found_aliases,
                file.data.get(Criteria.DRAWS.value, []),
                file.data.get(Criteria.PAGE_REFERENCES.value, []),
                file.data.get(Criteria.TAGS.value, []),
                file.data.get(Criteria.TAGGED_BACKLINKS.value, []),
                file.data.get(Criteria.PROPERTIES_PAGE_BUILTIN.value, []),
                file.data.get(Criteria.PROPERTIES_PAGE_USER.value, []),
                file.data.get(Criteria.PROPERTIES_BLOCK_BUILTIN.value, []),
                file.data.get(Criteria.PROPERTIES_BLOCK_USER.value, []),
                [getattr(file, "ns_parent", "")],
            ]
            linked_references = [item for sublist in linked_references for item in sublist if item]

            for item in linked_references:
                self.all_linked_references.setdefault(item, {})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item].setdefault("found_in", []).append(file.path.name)

            if hasattr(file, "ns_parent"):
                linked_references.remove(file.ns_parent)

            self.unique_linked_references.update(linked_references)

        self.all_linked_references = dict(
            sorted(
                self.all_linked_references.items(),
                key=lambda item: item[1]["count"],
                reverse=True,
            )
        )

        # Create dangling links
        self.dangling_links = self.unique_linked_references.union(self.unique_linked_references_ns)
        self.dangling_links.difference_update(self.names_to_hashes.keys())
        self.dangling_links.difference_update(unique_aliases)
        self.dangling_links = set(sorted(self.dangling_links))

    def post_processing_content_namespaces(self, file: LogseqFile):
        """Post-process namespaces in the content data."""
        ns_level = file.ns_level
        ns_root = file.ns_root
        ns_parent = file.ns_parent_full
        self.unique_linked_references_ns.update([ns_root, file.path.name])

        if self.names_to_hashes.get(ns_root):
            for hash_ in self.names_to_hashes[ns_root]:
                ns_root_file = self.hashed_files.get(hash_)
                ns_root_file.ns_level = 1
                if not hasattr(ns_root_file, "ns_children"):
                    ns_root_file.ns_children = set()
                ns_root_file.ns_children.add(file.path.name)
                ns_root_file.ns_size = len(ns_root_file.ns_children)

        if self.names_to_hashes.get(ns_parent) and ns_level > 2:
            for hash_ in self.names_to_hashes[ns_parent]:
                ns_parent_file = self.hashed_files.get(hash_)
                ns_parent_level = getattr(ns_parent_file, "ns_level", 0)
                direct_level = ns_level - 1
                ns_parent_file.ns_level = max(direct_level, ns_parent_level)
                if not hasattr(ns_parent_file, "ns_children"):
                    ns_parent_file.ns_children = set()
                ns_parent_file.ns_children.add(file.path.name)
                ns_parent_file.ns_size = len(ns_parent_file.ns_children)

    def process_summary_data(self):
        """Process summary data for each file based on metadata and content analysis."""
        for _, file in self.hashed_files.items():
            file.is_backlinked = file.check_is_backlinked(self.unique_linked_references)
            file.is_backlinked_by_ns_only = file.check_is_backlinked(self.unique_linked_references_ns)
            if file.is_backlinked and file.is_backlinked_by_ns_only:
                file.is_backlinked = False
            if file.file_type in ("journal", "page"):
                file.node_type = file.determine_node_type()

    def list_files_with_keys_and_values(self, **criteria) -> list:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.hashed_files.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result

    def handle_assets(self, asset_files: list):
        """Handle assets for the Logseq Analyzer."""
        for hash_, file in self.hashed_files.items():
            emb_link_asset = file.data.get(Criteria.EMBEDDED_LINKS_ASSET.value)
            asset_captured = file.data.get(Criteria.ASSETS.value)
            if not (emb_link_asset or asset_captured):
                continue
            for asset in asset_files:
                asset_hash = self.names_to_hashes.get(asset)
                if not asset_hash:
                    continue
                for hash_ in asset_hash:
                    asset_file = self.hashed_files.get(hash_)
                    if not asset_file or asset_file.is_backlinked:
                        continue
                    if emb_link_asset:
                        for asset_mention in emb_link_asset:
                            if asset_file.path.name in asset_mention or file.path.name in asset_mention:
                                asset_file.is_backlinked = True
                                break
                    if asset_captured:
                        for asset_mention in asset_captured:
                            if asset_file.path.name in asset_mention or file.path.name in asset_mention:
                                asset_file.is_backlinked = True
                                break

        backlinked_kwargs = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_kwargs = {"is_backlinked": False, "file_type": "asset"}

        self.assets_backlinked = self.list_files_with_keys_and_values(**backlinked_kwargs)
        self.assets_not_backlinked = self.list_files_with_keys_and_values(**not_backlinked_kwargs)
