"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from ._global_objects import CACHE, ANALYZER_CONFIG
from .namespace_analyzer import NamespaceAnalyzer
from .process_content_data import create_alphanum, post_processing_content_namespaces
from .process_summary_data import (
    check_has_backlinks,
    check_has_embedded_links,
    check_has_external_links,
    check_is_backlinked,
    determine_file_type,
    determine_node_type,
)
from .logseq_file import LogseqFile


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
        self.alphanum_dict = {}
        self.alphanum_dict_ns = {}
        self.all_linked_references = {}
        self.dangling_links = set()
        self.namespace_data = {}

    def process_graph_files(self):
        """
        Process all files in the Logseq graph folder.
        """
        for file_path in CACHE.iter_modified_files():
            file = LogseqFile(file_path)
            file.process_single_file()

            name = file.data.get("name")
            if name in self.data:
                name = file.data.get("name_secondary")

            self.data[name] = file.data
            self.content_bullets[name] = file.content_bullets

    def post_processing_content(self):
        """
        Post-process the content data for all files.
        """
        self.all_linked_references = {}
        unique_linked_references = set()
        unique_linked_references_namespaces = set()
        unique_aliases = set()

        # Process each file's content
        ns_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")

        for name, data in self.data.items():
            # Process namespaces
            if ns_sep in name:
                unique_linked_references_namespaces.update([data["namespace_root"], name])
                self.data = post_processing_content_namespaces(self.data, name, data, ns_sep)

            # Update aliases and linked references
            found_aliases = data.get("aliases", [])
            unique_aliases.update(found_aliases)
            ns_parent = data.get("namespace_parent", "")
            linked_references = [
                found_aliases,
                data.get("draws", []),
                data.get("page_references", []),
                data.get("tags", []),
                data.get("tagged_backlinks", []),
                data.get("properties_page_builtin", []),
                data.get("properties_page_user", []),
                data.get("properties_block_builtin", []),
                data.get("properties_block_user", []),
                [ns_parent],
            ]

            linked_references = [item for sublist in linked_references for item in sublist if item]

            for item in linked_references:
                self.all_linked_references.setdefault(item, {})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item].setdefault("found_in", []).append(name)

            if ns_parent:
                linked_references.remove(ns_parent)

            unique_linked_references.update(linked_references)

        # Create alphanum lookups and identify dangling links
        self.all_linked_references = dict(
            sorted(self.all_linked_references.items(), key=lambda item: item[1]["count"], reverse=True)
        )
        unique_filenames = set(sorted(self.data.keys()))
        unique_aliases = set(sorted(unique_aliases))
        unique_linked_references = set(sorted(unique_linked_references))
        unique_linked_references_namespaces = set(sorted(unique_linked_references_namespaces))

        # Create dangling links
        self.dangling_links = unique_linked_references.union(unique_linked_references_namespaces)
        self.dangling_links.difference_update(unique_filenames)
        self.dangling_links.difference_update(unique_aliases)

        # Create alphanum dictionaries
        self.alphanum_dict = create_alphanum(unique_linked_references)
        self.alphanum_dict_ns = create_alphanum(unique_linked_references_namespaces)

    def process_summary_data(self):
        """
        Process summary data for each file based on metadata and content analysis.
        """
        for name, data in self.data.items():
            has_content = data.get("size") > 0
            has_backlinks = check_has_backlinks(data, has_content)
            has_external_links = check_has_external_links(data, has_content)
            has_embedded_links = check_has_embedded_links(data, has_content)

            file_path_parent_name = data.get("file_path_parent_name")
            file_path_parts = data.get("file_path_parts")

            file_type = determine_file_type(file_path_parent_name, file_path_parts)

            is_backlinked = check_is_backlinked(name, data, self.alphanum_dict)
            is_backlinked_by_ns_only = check_is_backlinked(name, data, self.alphanum_dict_ns, is_backlinked)

            node_type = "other"
            if file_type in ["journal", "page"]:
                node_type = determine_node_type(has_content, is_backlinked, is_backlinked_by_ns_only, has_backlinks)

            data["file_type"] = file_type
            data["node_type"] = node_type
            data["has_content"] = has_content
            data["has_backlinks"] = has_backlinks
            data["has_external_links"] = has_external_links
            data["has_embedded_links"] = has_embedded_links
            data["is_backlinked"] = is_backlinked
            data["is_backlinked_by_ns_only"] = is_backlinked_by_ns_only
        self.data = dict(sorted(self.data.items(), key=lambda item: item[0]))

    def process_namespace_data(self):
        """
        Process namespace data and perform extended analysis for the Logseq Analyzer.
        """
        ns = NamespaceAnalyzer(self.data, self.dangling_links)
        ns.create_namespace_parts()
        ns.extract_unique_namespace_parts()
        ns.analyze_namespace_details()
        ns.get_unique_namespaces_by_level()
        ns.analyze_namespace_queries()
        ns.visualize_namespace_hierarchy()

        ##################################
        # 01 Conflicts With Existing Pages
        ##################################
        ns.detect_non_namespace_conflicts()

        #########################################
        # 02 Parts that Appear at Multiple Depths
        #########################################
        ns.detect_parent_depth_conflicts()
        ns.get_unique_conflicts()

        ###########################
        # 03 Output Namespace Data
        ###########################
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
