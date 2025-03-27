"""
This module contains functions for processing and analyzing namespace data in Logseq.

What are the problems trying to be solved?

Logseq's move to a database system from a markdown one.
Currently, namespace pages are full and valid, so root/parent/child is a name.
The proposed migration by Logseq is to split each part and tag the children with their parents.
Now we have three pages of root, parent, and child.

Problems:
    1. The split namespace parts may conflict with existing, non-namespace pages.
    2. Some parents may appear across multiple namespaces at different depths.
    3. There is no easy way to get data about namespaces.
"""

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple

from .config_loader import get_config
from .process_summary_data import extract_summary_subset_files
from .compile_regex import compile_re_content

CONFIG = get_config()
CONTENT_RE = compile_re_content()


def process_namespace_data(graph_data: Dict[str, Any], dangling_links: List[str]) -> Dict[str, Any]:
    """
    Process namespace data and perform extended analysis for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph content data.
        dangling_links (list): The list of dangling links.

    Returns:
        dict: A dictionary containing namespace data and analysis results.
    """
    namespace_data_subset = {}
    # Find unique names that are not namespaces
    namespace_data_subset["___meta___unique_names_not_namespace"] = extract_summary_subset_files(
        graph_data, namespace_level=0
    )

    # Find unique names that are namespaces
    namespace_data_subset["___meta___unique_names_is_namespace"] = sorted(
        [k for k, v in graph_data.items() if v.get("namespace_level")]
    )

    namespace_data = {}
    for name in namespace_data_subset["___meta___unique_names_is_namespace"]:
        namespace_data[name] = {k: v for k, v in graph_data[name].items() if "namespace" in k and v}

    namespace_parts = {k: v["namespace_parts"] for k, v in namespace_data.items() if v.get("namespace_parts")}
    unique_namespace_parts = extract_unique_namespace_parts(namespace_parts)
    namespace_details = analyze_namespace_details(namespace_parts)
    unique_namespaces_per_level = get_unique_namespaces_by_level(namespace_parts, namespace_details)
    namespace_data_subset["namespace_queries"] = analyze_namespace_queries(graph_data, namespace_data)
    namespace_data_subset["namespace_hierarchy"] = visualize_namespace_hierarchy(namespace_parts)

    ##################################
    # 01 Conflicts With Existing Pages
    ##################################
    # Potential non-namespace pages are those that are in the namespace data
    potential_non_namespace = unique_namespace_parts.intersection(
        namespace_data_subset["___meta___unique_names_not_namespace"]
    )

    # Potential dangling links are those that are in the namespace data
    potential_dangling = unique_namespace_parts.intersection(dangling_links)

    # Detect conflicts with non-namespace pages and dangling links
    conflicts_non_namespace, conflicts_dangling = detect_non_namespace_conflicts(
        namespace_parts, potential_non_namespace, potential_dangling
    )

    #########################################
    # 02 Parts that Appear at Multiple Depths
    #########################################
    namespace_data_subset["conflicts_parent_depth"] = detect_parent_depth_conflicts(namespace_parts)
    namespace_data_subset["conflicts_parents_unique"] = get_unique_conflicts(
        namespace_data_subset["conflicts_parent_depth"]
    )

    ###########################
    # 03 Output Namespace Data
    ###########################
    namespace_data_subset.update(
        {
            "___meta___namespace_data": namespace_data,
            "___meta___namespace_parts": namespace_parts,
            "conflicts_dangling": conflicts_dangling,
            "conflicts_non_namespace": conflicts_non_namespace,
            "namespace_details": namespace_details,
            "unique_namespace_parts": unique_namespace_parts,
            "unique_namespaces_per_level": unique_namespaces_per_level,
        },
    )

    return namespace_data_subset


def get_unique_namespaces_by_level(
    namespace_parts: Dict[str, Dict[str, int]], namespace_details: Dict[str, Any]
) -> Dict[str, Set[str]]:
    """
    Get unique namespaces by level.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.
        namespace_details (dict): Dictionary containing details about namespaces.

    Returns:
        dict: A dictionary mapping each level to a set of unique namespaces.
    """
    unique_namespaces_per_level = {i: set() for i in range(1, namespace_details["max_depth"] + 1)}

    for parts in namespace_parts.values():
        for part, level in parts.items():
            unique_namespaces_per_level[level].add(part)

    return unique_namespaces_per_level


def analyze_namespace_details(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """
    Perform extended analysis on namespace parts.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: A dictionary containing various statistics about namespaces.
    """
    level_distribution = Counter()

    for _, parts in namespace_parts.items():
        for _, level in parts.items():
            level_distribution[level] += 1

    max_depth = max(level_distribution) if level_distribution else 0

    details = {
        "max_depth": max_depth,
        "level_distribution": dict(level_distribution),
    }
    return details


def detect_non_namespace_conflicts(
    namespace_parts: Dict[str, Dict[str, int]], non_namespace: Set[str], dangling: Set[str]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Check for conflicts between split namespace parts and existing non-namespace page names.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.
        non_namespace (set): Set of names from potential non-namespace pages.
        dangling (set): Set of potential dangling links.

    Returns:
        tuple: A tuple containing two dictionaries:
            - Conflicts with non-namespace pages.
            - Conflicts with dangling links.
    """
    conflicts_non_namespace = defaultdict(list)
    conflicts_dangling = defaultdict(list)
    for entry, parts in namespace_parts.items():
        for part in parts.keys():
            if part in non_namespace:
                conflicts_non_namespace[part].append(entry)

            if part in dangling:
                conflicts_dangling[part].append(entry)

    return conflicts_non_namespace, conflicts_dangling


def detect_parent_depth_conflicts(
    namespace_parts: Dict[str, Dict[str, int]],
) -> Dict[str, List[str]]:
    """
    Identify namespace parts that appear at different depths (levels) across entries.

    For each namespace part, we collect the levels at which it appears as well as
    the associated entries. Parts that occur at more than one depth are flagged
    as potential conflicts.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: A dictionary where keys are namespace parts with conflicts, and values
              are lists of entries associated with those parts at different levels.
    """
    # Mapping from namespace part to a set of levels and associated entries
    part_levels = defaultdict(set)
    part_entries = defaultdict(list)

    for entry, parts in namespace_parts.items():
        for part, level in parts.items():
            part_levels[part].add(level)
            part_entries[part].append({"entry": entry, "level": level})

    # Filter out parts that only occur at a single depth.
    conflicts = {}
    for part, levels in part_levels.items():
        if len(levels) > 1:
            conflicts[part] = {"levels": sorted(list(levels)), "entries": part_entries[part]}

    # Split so it's dict[part level] = [list of parts]
    output_conflicts = {}
    for part, details in conflicts.items():
        for level in details["levels"]:
            output_conflicts[f"{part} {level}"] = [i["entry"] for i in details["entries"] if i["level"] == level]

    return output_conflicts


def get_unique_conflicts(output_conflicts: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """
    Get unique conflicts for each namespace part.

    Args:
        output_conflicts (dict): Dictionary mapping namespace parts to their associated entries.

    Returns:
        dict: A dictionary mapping each namespace part to a set of unique pages.
    """
    ns_sep = CONFIG.get("LOGSEQ_NS", "NAMESPACE_SEP")
    unique_conflicts = {}
    for part, details in output_conflicts.items():
        level = int(part.split(" ")[-1])
        unique_pages = set()
        for page in details:
            parts = page.split(ns_sep)
            up_to_level = parts[:level]
            unique_pages.add(ns_sep.join(up_to_level))
        unique_conflicts[part] = unique_pages
    return unique_conflicts


def extract_unique_namespace_parts(namespace_parts: Dict[str, Dict[str, int]]) -> Set[str]:
    """
    Analyze the levels of namespace parts across all entries.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        set: A set of unique namespace parts.
    """
    unique_namespace_parts = set()
    for parts in namespace_parts.values():
        unique_namespace_parts.update(parts.keys())
    return unique_namespace_parts


def analyze_namespace_queries(graph_data: Dict[str, Any], namespace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze namespace queries.

    Args:
        graph_data (dict): The graph content data.

    Returns:
        dict: A dictionary containing namespace queries and their details.
    """
    namespace_queries = {}
    for entry, data in graph_data.items():
        got_ns_queries = data.get("namespace_queries")
        if not got_ns_queries:
            continue
        for q in got_ns_queries:
            page_refs = CONTENT_RE["page_reference"].findall(q)
            if len(page_refs) != 1:
                logging.warning("Invalid references found in query: %s", q)
                continue

            page_ref = page_refs[0]
            namespace_queries[q] = namespace_queries.get(q, {})
            namespace_queries[q]["found_in"] = namespace_queries[q].get("found_in", [])
            namespace_queries[q]["found_in"].append(entry)
            namespace_queries[q]["namespace"] = page_ref
            namespace_queries[q]["size"] = namespace_data.get(page_ref, {}).get("namespace_size", 0)
            namespace_queries[q]["uri"] = graph_data[entry].get("uri", "")
            namespace_queries[q]["logseq_url"] = graph_data[entry].get("logseq_url", "")

    # Sort the queries by size in descending order
    namespace_queries = dict(sorted(namespace_queries.items(), key=lambda item: item[1]["size"], reverse=True))

    return namespace_queries


def visualize_namespace_hierarchy(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """
    Build a tree-like structure of namespaces.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: A tree-like structure representing the hierarchy of namespaces.
    """
    tree = {}
    for _, parts in namespace_parts.items():
        current_level = tree
        for part_level in parts.items():
            part = part_level[0]
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree
