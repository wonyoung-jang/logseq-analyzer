from pathlib import Path
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple

import src.config as config
from src.reporting import write_output

"""
Namespace Analysis
------------------
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


def analyze_namespace_details(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """
    Perform extended analysis on namespace parts.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: A dictionary containing various statistics about namespaces.
    """
    level_distribution = Counter()
    root_counter = Counter()
    part_level_details = defaultdict(list)

    for entry, parts in namespace_parts.items():
        for part, level in parts.items():
            level_distribution[level] += 1
            part_level_details[part].append(level)

        sorted_parts = sorted(parts.items(), key=lambda x: x[1])
        if sorted_parts:
            prefix, _ = sorted_parts[0]
            root_counter[prefix] += 1

    max_depth = max(level_distribution) if level_distribution else 0
    root_counter = {k: v for k, v in sorted(root_counter.items(), key=lambda item: item[1], reverse=True)}

    details = {
        "level_distribution": dict(level_distribution),
        "max_depth": max_depth,
        "namespace_size": root_counter,
    }

    return details


def analyze_namespace_frequency(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Counter]:
    """
    Analyze frequency of each namespace part and their levels.

    Args:
        namespace_parts (dict): Dictionary of namespace parts per entry.

    Returns:
        dict: A dictionary mapping each namespace part to a Counter of levels.
    """
    frequency = {}
    frequency_list = {}
    for name, parts in namespace_parts.items():
        for part, level in parts.items():
            if part not in frequency:
                frequency[part] = Counter()
            frequency[part][level] += 1
            combine_name = f"{part} ({level})"
            if combine_name not in frequency_list:
                frequency_list[combine_name] = ""
            frequency_list[combine_name] += f"\n\t{name}"
    return frequency, frequency_list


def detect_non_namespace_conflicts(
    namespace_parts: Dict[str, Dict[str, int]], non_namespace: Set[str], dangling: List[str]
) -> Dict[str, List[str]]:
    """
    Check for conflicts between split namespace parts and existing non-namespace page names.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.
        non_namespace (set): Set of names from non-namespace pages.
        dangling (list): List of dangling links.

    Returns:
        dict: Mapping of conflicting namespace parts to a list of entry names where the conflict occurs.
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


def detect_parent_depth_conflicts(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, Any]]:
    """
    Identify namespace parts that appear at different depths (levels) across entries.

    For each namespace part, we collect the levels at which it appears as well as
    the associated entries. Parts that occur at more than one depth are flagged
    as potential conflicts.

    Returns:
        dict: Mapping of conflicting namespace parts to details including
              the sorted levels they appear at and the list of entries with their level.
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

    unique_conflicts = {}
    for part, details in output_conflicts.items():
        level = int(part.split(" ")[-1]) + 1
        unique_pages = set()
        for page in details:
            parts = page.split(config.NAMESPACE_SEP)
            up_to_level = parts[:level]
            unique_pages.add(config.NAMESPACE_SEP.join(up_to_level))
        unique_conflicts[part] = unique_pages

    return output_conflicts, unique_conflicts


def analyze_namespace_part_levels(namespace_parts: Dict[str, Dict[str, int]]) -> Tuple[Dict[str, List[int]], Set[str]]:
    """
    Analyze the levels of namespace parts across all entries.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: Mapping of namespace parts to a sorted list of levels they appear at.
        set: Set all of unique namespace parts.
    """
    namespace_part_levels = {}
    unique_namespace_parts = set()
    for name, parts in namespace_parts.items():
        for k, v in parts.items():
            namespace_part_levels.setdefault(k, set()).add(v)
            unique_namespace_parts.add(k)
    namespace_part_levels = {
        k: sorted(v) for k, v in sorted(namespace_part_levels.items(), key=lambda item: len(item[1]), reverse=True)
    }
    return namespace_part_levels, unique_namespace_parts


def analyze_namespace_queries(graph_content_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze namespace queries.

    Args:
        graph_content_data (dict): The graph content data.

    Returns:
        dict: A dictionary mapping namespace parts to their level and associated entries
    """
    namespace_queries = {}
    for entry, data in graph_content_data.items():
        if data.get("namespace_queries"):
            queries = data["namespace_queries"]
            namespace_queries[entry] = queries

    return namespace_queries


def process_namespace_data(
    output_dir: Path, graph_content_data: Dict[str, Any], meta_dangling_links: List[str]
) -> None:
    """
    Process namespace data and perform extended analysis for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        graph_content_data (dict): The graph content data.
        meta_dangling_links (list): The list of dangling links.

    Main outputs:
        conflicts_non_namespace
        conflicts_dangling
        conflicts_parent_depth
        conflicts_parents_unique
    """
    output_dir_ns = config.OUTPUT_DIR_NAMESPACE

    # 01 Conflicts With Existing Pages
    # Extract namespace parts
    namespace_parts = {k: v["namespace_parts"] for k, v in graph_content_data.items() if v.get("namespace_parts")}
    write_output(output_dir, "__namespace_parts", namespace_parts, output_dir_ns)

    # Split content data by namespaces and non-namespaces
    content_data_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] >= 0}
    unique_names_namespace = set(content_data_namespaces.keys())
    write_output(output_dir, "unique_names_namespace", unique_names_namespace, output_dir_ns)

    content_data_not_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] < 0}
    unique_names_not_namespace = set(content_data_not_namespaces.keys())
    write_output(output_dir, "unique_names_not_namespace", unique_names_not_namespace, output_dir_ns)

    # Existing analysis: group by levels
    namespace_part_levels, unique_namespace_parts = analyze_namespace_part_levels(namespace_parts)
    write_output(output_dir, "namespace_part_levels", namespace_part_levels, output_dir_ns)
    write_output(output_dir, "unique_namespace_parts", unique_namespace_parts, output_dir_ns)

    potential_non_namespace = unique_names_not_namespace.intersection(unique_namespace_parts)
    write_output(output_dir, "potential_non_namespace", potential_non_namespace, output_dir_ns)

    potential_dangling = set(meta_dangling_links).intersection(unique_namespace_parts)
    write_output(output_dir, "potential_dangling", potential_dangling, output_dir_ns)

    # Detecting conflicts with non-namespace pages
    conflicts_non_namespace, conflicts_dangling = detect_non_namespace_conflicts(
        namespace_parts, potential_non_namespace, potential_dangling
    )
    write_output(output_dir, "conflicts_non_namespace", conflicts_non_namespace, output_dir_ns)
    write_output(output_dir, "conflicts_dangling", conflicts_dangling, output_dir_ns)

    # 02 Parts that Appear at Multiple Depths
    conflicts_parent_depth, conflicts_parents_unique = detect_parent_depth_conflicts(namespace_parts)
    write_output(output_dir, "conflicts_parent_depth", conflicts_parent_depth, output_dir_ns)
    write_output(output_dir, "conflicts_parents_unique", conflicts_parents_unique, output_dir_ns)

    # 03 General Namespace Data
    unique_namespace_roots = set(v["namespace_root"] for v in graph_content_data.values() if v.get("namespace_root"))
    write_output(output_dir, "unique_namespace_roots", unique_namespace_roots, output_dir_ns)

    namespace_details = analyze_namespace_details(namespace_parts)
    write_output(output_dir, "__namespace_details", namespace_details, output_dir_ns)

    namespace_frequency, namespace_freq_list = analyze_namespace_frequency(namespace_parts)
    write_output(output_dir, "namespace_frequency", namespace_frequency, output_dir_ns)
    write_output(output_dir, "namespace_freq_list", namespace_freq_list, output_dir_ns)

    # Namespace queries
    namespace_queries = analyze_namespace_queries(graph_content_data)
    write_output(output_dir, "namespace_queries", namespace_queries, output_dir_ns)
