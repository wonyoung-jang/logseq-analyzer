"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from typing import Any, Dict, List, Tuple

from ._global_objects import CACHE, ANALYZER_CONFIG
from .namespace_analyzer import NamespaceAnalyzer
from .process_summary_data import check_is_backlinked, determine_node_type
from .logseq_file import LogseqFile

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
        self.unique_linked_references_namespaces = set()
        self.all_linked_references = {}
        self.dangling_links = set()
        self.namespace_data = {}
        self.summary_file_subsets = {}
        self.summary_data_subsets = {}
        self.files: List[LogseqFile] = []
        self.assets_backlinked = []
        self.assets_not_backlinked = []

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
            file.get_single_file_metadata()
            file.process_content_data()

            name = file.data.get("name")
            if self.data.get(name):
                name = file.data.get("name_secondary")

            self.data[name] = file.data
            self.content_bullets[name] = file.content_bullets
            self.files.append(file)

    def post_processing_content(self):
        """
        Post-process the content data for all files.
        """
        unique_linked_references = set()
        unique_linked_references_namespaces = set()
        unique_aliases = set()

        # Process each file's content
        for file in self.files:
            if file.filename.is_namespace:
                unique_linked_references_namespaces.update([file.data["namespace_root"], file.filename.name])
                self.post_processing_content_namespaces(file.filename.name, file.data)

            found_aliases = file.data.get("aliases", [])
            unique_aliases.update(found_aliases)
            ns_parent = file.data.get("namespace_parent", "")
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
                [ns_parent],
            ]

            linked_references = [item for sublist in linked_references for item in sublist if item]

            for item in linked_references:
                self.all_linked_references.setdefault(item, {})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item].setdefault("found_in", []).append(file.filename.name)

            if ns_parent:
                linked_references.remove(ns_parent)

            unique_linked_references.update(linked_references)

        # Create alphanum lookups and identify dangling links
        self.all_linked_references = dict(
            sorted(
                self.all_linked_references.items(),
                key=lambda item: item[1]["count"],
                reverse=True,
            )
        )

        # Create dangling links
        self.dangling_links = unique_linked_references.union(unique_linked_references_namespaces)
        self.dangling_links.difference_update(self.keys(), unique_aliases)
        self.dangling_links = set(sorted(self.dangling_links))

        self.unique_linked_references = unique_linked_references
        self.unique_linked_references_namespaces = unique_linked_references_namespaces

    def post_processing_content_namespaces(self, name: str, data: Dict[str, Any]):
        """
        Post-process namespaces in the content data.
        """
        namespace_parts_list = name.split(NS_SEP)
        namespace_level = data["namespace_level"]
        ns_root = data["namespace_root"]
        ns_parent = NS_SEP.join(namespace_parts_list[:-1])

        if ns_root in self.data:
            root = self.data[ns_root]
            root_level = root.get("namespace_level", 0)
            root["namespace_level"] = max(1, root_level)
            root.setdefault("namespace_children", set()).add(name)
            root["namespace_size"] = len(root["namespace_children"])

        if namespace_level > 2:
            if ns_parent in self.data:
                parent = self.data[ns_parent]
                parent_level = parent.get("namespace_level", 0)
                direct_level = namespace_level - 1
                parent["namespace_level"] = max(direct_level, parent_level)
                parent.setdefault("namespace_children", set()).add(name)
                parent["namespace_size"] = len(parent["namespace_children"])

    def process_summary_data(self):
        """
        Process summary data for each file based on metadata and content analysis.
        """
        for file in self.files:
            is_backlinked = check_is_backlinked(file.filename.name, self.unique_linked_references)
            is_backlinked_by_ns_only = check_is_backlinked(file.filename.name, self.unique_linked_references_namespaces)

            node_type = "other"
            if file.data.get("file_type") in ("journal", "page"):
                node_type = determine_node_type(
                    file.data.get("has_content"),
                    is_backlinked,
                    is_backlinked_by_ns_only,
                    file.data.get("has_backlinks"),
                )

            file.data["node_type"] = node_type
            file.data["is_backlinked"] = is_backlinked
            file.data["is_backlinked_by_ns_only"] = is_backlinked_by_ns_only
            if is_backlinked_by_ns_only:
                file.data["is_backlinked"] = False

    def process_namespace_data(self):
        """
        Process namespace data and perform extended analysis for the Logseq Analyzer.
        """
        ns = NamespaceAnalyzer(self.files, self.data, self.dangling_links)
        ns.init_ns_parts()
        ns.analyze_ns_details()
        ns.analyze_ns_queries()

        # 01 Conflicts With Existing Pages
        ns.detect_non_ns_conflicts()

        # 02 Parts that Appear at Multiple Depths
        ns.detect_parent_depth_conflicts()
        ns.get_unique_parent_conflicts()

        # 03 Output Namespace Data
        self.namespace_data.update(
            {
                "___meta___namespace_data": ns.namespace_data,
                "___meta___namespace_parts": ns.namespace_parts,
                "unique_namespace_parts": ns.unique_namespace_parts,
                "namespace_details": ns.namespace_details,
                "unique_namespaces_per_level": ns.unique_namespaces_per_level,
                "namespace_queries": ns.namespace_queries,
                "namespace_hierarchy": ns.tree,
                "conflicts_non_namespace": ns.conflicts_non_namespace,
                "conflicts_dangling": ns.conflicts_dangling,
                "conflicts_parent_depth": ns.conflicts_parent_depth,
                "conflicts_parent_unique": ns.conflicts_parent_unique,
            },
        )

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
            "___is_node_other": {"node_type": "other_node"},
        }
        for output_name, criteria in summary_categories.items():
            self.summary_file_subsets[output_name] = self.list_files_with_keys_and_values(**criteria)

        # Process file extensions
        file_extensions = {}
        for meta in self.data.values():
            ext = meta.get("file_path_suffix")
            if ext in file_extensions:
                continue
            file_extensions[ext] = True

        file_ext_dict = {}
        for ext in file_extensions:
            output_name = f"_all_{ext}s"
            criteria = {"file_path_suffix": ext}
            file_ext_dict[output_name] = self.list_files_with_keys_and_values(file_path_suffix=ext)
        self.summary_file_subsets["____file_extensions_dict"] = file_ext_dict

    def list_files_with_keys_and_values(self, **criteria) -> list:
        """
        Extract a subset of the summary data based on multiple criteria (key-value pairs).
        """
        return [k for k, v in self.data.items() if all(v.get(key) == expected for key, expected in criteria.items())]

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
        for file in self.files:
            if file.data.get(criteria):
                for value in file.data[criteria]:
                    subset_counter.setdefault(value, {})
                    subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                    subset_counter[value].setdefault("found_in", []).append(file.filename.name)
        return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))

    def handle_assets(self):
        """
        Handle assets for the Logseq Analyzer.
        """
        for _, data in self.data.items():
            if not data.get("assets"):
                continue

            for asset in self.summary_file_subsets.get("___is_filetype_asset", []):
                if self.data[asset]["is_backlinked"]:
                    continue
                asset_original_name = self.data[asset]["name"]
                for asset_mention in data["assets"]:
                    if asset in asset_mention or asset_original_name in asset_mention:
                        self.data[asset]["is_backlinked"] = True
                        break

        asset_backlinked_kwargs = {
            "is_backlinked": True,
            "file_type": "asset",
        }
        asset_not_backlinked_kwargs = {
            "is_backlinked": False,
            "file_type": "asset",
        }

        self.assets_backlinked = self.list_files_with_keys_and_values(**asset_backlinked_kwargs)
        self.assets_not_backlinked = self.list_files_with_keys_and_values(**asset_not_backlinked_kwargs)
