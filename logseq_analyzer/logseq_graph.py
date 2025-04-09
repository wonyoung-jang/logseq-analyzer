"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from collections import defaultdict
from typing import Any, Dict

from ._global_objects import CACHE, ANALYZER_CONFIG
from .logseq_file import LogseqFile, LogseqFileHash

NS_SEP = ANALYZER_CONFIG.get("CONST", "NAMESPACE_SEP")


class LogseqGraph:
    """
    Class to handle all Logseq files in the graph directory.
    """

    def __init__(self):
        """
        Initialize the LogseqGraph instance.
        """
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
        self.hashed_files: Dict[LogseqFileHash, LogseqFile] = {}
        self.names_to_hashes = defaultdict(list)

    def keys(self) -> list:
        """
        Get all keys from the data dictionary.
        """
        return self.data.keys()

    def process_graph_files(self):
        """
        Process all files in the Logseq graph folder.
        """
        for file_path in CACHE.iter_modified_files():
            file = LogseqFile(file_path)
            self.data[file.hash] = file.__dict__
            self.content_bullets[file.hash] = file.content_bullets
            self.hashed_files[file.hash] = file
            self.names_to_hashes[file.path.name].append(file.hash)
            delattr(file, "content_bullets")
            delattr(file, "content")
            delattr(file, "primary_bullet")

    def post_processing_content(self):
        """
        Post-process the content data for all files.
        """
        unique_aliases = set()

        # Process each file's content
        for _, file in self.hashed_files.items():
            if file.path.is_namespace:
                self.post_processing_content_namespaces(file)

            found_aliases = file.data.get("aliases", [])
            unique_aliases.update(found_aliases)
            linked_references = [
                found_aliases,
                file.data.get("draws", []),
                file.data.get("page_references", []),
                file.data.get("tags", []),
                file.data.get("tagged_backlinks", []),
                file.data.get("properties_page_builtin", []),
                file.data.get("properties_page_user", []),
                file.data.get("properties_block_builtin", []),
                file.data.get("properties_block_user", []),
                [getattr(file, "ns_parent", "")],
            ]
            linked_references = [item for sublist in linked_references for item in sublist if item]

            for item in linked_references:
                self.all_linked_references.setdefault(item, {})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item].setdefault("found_in", []).append(file.name)

            if hasattr(file, "ns_parent"):
                linked_references.remove(file.ns_parent)

            self.unique_linked_references.update(linked_references)

        # Create alphanum lookups and identify dangling links
        self.all_linked_references = dict(
            sorted(
                self.all_linked_references.items(),
                key=lambda item: item[1]["count"],
                reverse=True,
            )
        )

        # Create dangling links
        self.dangling_links = self.unique_linked_references.union(self.unique_linked_references_ns)
        self.dangling_links.difference_update(self.names_to_hashes.keys(), unique_aliases)
        self.dangling_links = set(sorted(self.dangling_links))

    def post_processing_content_namespaces(self, file: LogseqFile):
        """
        Post-process namespaces in the content data.
        """
        ns_level = file.ns_level
        ns_root = file.ns_root
        ns_parent = file.ns_parent_full
        self.unique_linked_references_ns.update([ns_root, file.name])

        if self.names_to_hashes.get(ns_root):
            for hash_ in self.names_to_hashes[ns_root]:
                ns_root_file = self.hashed_files.get(hash_)
                ns_root_file.ns_level = 1
                if not hasattr(ns_root_file, "ns_children"):
                    ns_root_file.ns_children = set()
                ns_root_file.ns_children.add(file.name)
                ns_root_file.ns_size = len(ns_root_file.ns_children)

        if self.names_to_hashes.get(ns_parent) and ns_level > 2:
            for hash_ in self.names_to_hashes[ns_parent]:
                ns_parent_file = self.hashed_files.get(hash_)
                ns_parent_level = getattr(ns_parent_file, "ns_level", 0)
                direct_level = ns_level - 1
                ns_parent_file.ns_level = max(direct_level, ns_parent_level)
                if not hasattr(ns_parent_file, "ns_children"):
                    ns_parent_file.ns_children = set()
                ns_parent_file.ns_children.add(file.name)
                ns_parent_file.ns_size = len(ns_parent_file.ns_children)

    def process_summary_data(self):
        """
        Process summary data for each file based on metadata and content analysis.
        """
        for _, file in self.hashed_files.items():
            is_backlinked = file.check_is_backlinked(self.unique_linked_references)
            is_backlinked_by_ns_only = file.check_is_backlinked(self.unique_linked_references_ns)
            file.is_backlinked = is_backlinked
            file.is_backlinked_by_ns_only = is_backlinked_by_ns_only
            if is_backlinked and is_backlinked_by_ns_only:
                file.is_backlinked = False
            file.node_type = "other"
            if file.file_type in ("journal", "page"):
                file.node_type = file.determine_node_type()

    def generate_summary_file_subsets(self):
        """
        Generate summary subsets for the Logseq Analyzer.
        """
        summary_categories = {
            # Process general categories
            "___is_backlinked": {"is_backlinked": True},
            "___is_backlinked_by_ns_only": {"is_backlinked_by_ns_only": True},
            "___has_content": {"has_content": True},
            "___has_backlinks": {"has_backlinks": True},
            # Process file types
            "___is_filetype_asset": {"file_type": "asset"},
            "___is_filetype_draw": {"file_type": "draw"},
            "___is_filetype_journal": {"file_type": "journal"},
            "___is_filetype_page": {"file_type": "page"},
            "___is_filetype_whiteboard": {"file_type": "whiteboard"},
            "___is_filetype_other": {"file_type": "other"},
            # Process nodes
            "___is_node_orphan_true": {"node_type": "orphan_true"},
            "___is_node_orphan_graph": {"node_type": "orphan_graph"},
            "___is_node_orphan_namespace": {"node_type": "orphan_namespace"},
            "___is_node_orphan_namespace_true": {"node_type": "orphan_namespace_true"},
            "___is_node_root": {"node_type": "root"},
            "___is_node_leaf": {"node_type": "leaf"},
            "___is_node_branch": {"node_type": "branch"},
            "___is_node_other": {"node_type": "other"},
        }
        for output_name, criteria in summary_categories.items():
            self.summary_file_subsets[output_name] = self.list_files_with_keys_and_values(**criteria)

        # Process file extensions
        file_extensions = set()
        for _, file in self.hashed_files.items():
            ext = file.suffix
            if ext in file_extensions:
                continue
            file_extensions.add(ext)

        file_ext_dict = {}
        for ext in file_extensions:
            output_name = f"_all_{ext}s"
            criteria = {"suffix": ext}
            file_ext_dict[output_name] = self.list_files_with_keys_and_values(**criteria)
        self.summary_file_subsets["____file_extensions_dict"] = file_ext_dict

    def list_files_with_keys_and_values(self, **criteria) -> list:
        """
        Extract a subset of the summary data based on multiple criteria (key-value pairs).
        """
        result = []
        for _, file in self.hashed_files.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.name)
        return result

    def generate_summary_data_subsets(self):
        """
        Generate summary subsets for content data in the Logseq graph.
        """
        # Process content types
        content_subset_tags_nodes = [
            "advanced_commands",
            "advanced_commands_export",
            "advanced_commands_export_ascii",
            "advanced_commands_export_latex",
            "advanced_commands_caution",
            "advanced_commands_center",
            "advanced_commands_comment",
            "advanced_commands_example",
            "advanced_commands_important",
            "advanced_commands_note",
            "advanced_commands_pinned",
            "advanced_commands_query",
            "advanced_commands_quote",
            "advanced_commands_tip",
            "advanced_commands_verse",
            "advanced_commands_warning",
            "aliases",
            "assets",
            "block_embeds",
            "block_references",
            "blockquotes",
            "calc_blocks",
            "clozes",
            "draws",
            "embeds",
            "embedded_links_asset",
            "embedded_links_internet",
            "embedded_links_other",
            "external_links_alias",
            "external_links_internet",
            "external_links_other",
            "flashcards",
            "multiline_code_blocks",
            "multiline_code_langs",
            "namespace_queries",
            "page_embeds",
            "page_references",
            "properties_block_builtin",
            "properties_block_user",
            "properties_page_builtin",
            "properties_page_user",
            "properties_values",
            "query_functions",
            "references_general",
            "simple_queries",
            "tagged_backlinks",
            "tags",
            "inline_code_blocks",
            "dynamic_variables",
            "macros",
            "embed_video_urls",
            "cards",
            "embed_twitter_tweets",
            "embed_youtube_timestamps",
            "renderers",
        ]

        for criteria in content_subset_tags_nodes:
            counts_output_name = f"_content_{criteria}"
            self.summary_data_subsets[counts_output_name] = self.extract_summary_subset_content(criteria)

    def extract_summary_subset_content(self, criteria) -> Dict[str, Any]:
        """
        Extract a subset of data based on a specific criteria.
        Asks: What content matches the criteria? And where is it found? How many times?

        Args:
            criteria (str): The criteria for extraction.

        Returns:
            Dict[str, Any]: A dictionary containing the count and locations of the extracted values.
        """
        subset_counter = {}
        for _, file in self.hashed_files.items():
            if file.data.get(criteria):
                for value in file.data[criteria]:
                    subset_counter.setdefault(value, {})
                    subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                    subset_counter[value].setdefault("found_in", []).append(file.name)
        return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))

    def handle_assets(self):
        """
        Handle assets for the Logseq Analyzer.
        """
        for hash_, file in self.hashed_files.items():
            if not file.data.get("assets"):
                continue
            for asset in self.summary_file_subsets.get("___is_filetype_asset", []):
                asset_hash = self.names_to_hashes.get(asset)
                if not asset_hash:
                    continue
                for hash_ in asset_hash:
                    asset_file = self.hashed_files.get(hash_)
                    if not asset_file or asset_file.is_backlinked:
                        continue
                    for asset_mention in file.data["assets"]:
                        if asset_file.name in asset_mention or file.name in asset_mention:
                            asset_file.is_backlinked = True
                            break

        backlinked_kwargs = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_kwargs = {"is_backlinked": False, "file_type": "asset"}

        self.assets_backlinked = self.list_files_with_keys_and_values(**backlinked_kwargs)
        self.assets_not_backlinked = self.list_files_with_keys_and_values(**not_backlinked_kwargs)
