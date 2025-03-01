from pathlib import Path
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set
from src.reporting import write_output
import src.config as config

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
    namespace_lengths = []
    prefix_counter = Counter()
    part_level_details = defaultdict(list)

    for entry, parts in namespace_parts.items():
        namespace_lengths.append(len(parts))

        for part, level in parts.items():
            level_distribution[level] += 1
            part_level_details[part].append(level)

        sorted_parts = sorted(parts.items(), key=lambda x: x[1])
        if sorted_parts:
            prefix, _ = sorted_parts[0]
            prefix_counter[prefix] += 1

    max_depth = max(level_distribution) if level_distribution else 0

    details = {
        "level_distribution": dict(level_distribution),
        "max_depth": max_depth,
        "prefix_frequency": dict(prefix_counter),
        "namespace_lengths": namespace_lengths,
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

    frequency_list = {k: v for k, v in sorted(frequency_list.items())}
    return frequency, frequency_list


def detect_parent_depth_conflicts(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, Any]]:
    """
    Identify namespace parts that appear at different depths (levels) across entries.

    Returns:
        dict: Mapping of conflicting namespace parts to details including
              the levels they appear at and the entries in which they occur.
    """
    # A mapping from namespace part to a set of levels
    part_levels = defaultdict(set)
    # A mapping from namespace part to the list of entries with their level
    part_entries = defaultdict(list)

    for entry, parts in namespace_parts.items():
        for part, level in parts.items():
            part_levels[part].add(level)
            part_entries[part].append({"entry": entry, "level": level})

    # Filter out those parts that only occur at a single level.
    conflicts = {}
    for part, levels in part_levels.items():
        if len(levels) > 1:
            conflicts[part] = {"levels": sorted(list(levels)), "entries": part_entries[part]}
    return conflicts


def detect_non_namespace_conflicts(namespace_parts: Dict[str, Dict[str, int]], non_namespace: Set[str], dangling: List[str]) -> Dict[str, List[str]]:
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


def process_namespace_data(output_dir: Path, graph_content_data: Dict[str, Any], meta_dangling_links: List[str]) -> None:
    """
    Process namespace data and perform extended analysis for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        graph_content_data (dict): The graph content data.
    """
    
    """
    01 Conflicts With Existing Pages
    Namespace parts = part/part/part
    If any part exists in graph_content and is not a namespace, it is a conflict.
    Potential issues:
        Namespace parts that do not have files
            Can be orphaned or dangling links
            Can occur as it's not required to have a file for a namespace part
    """
    # Extract namespace parts
    namespace_parts = {k: v["namespace_parts"] for k, v in graph_content_data.items() if v.get("namespace_parts")}
    write_output(output_dir, "__namespace_parts", namespace_parts, config.OUTPUT_DIR_TEST)

    # Split content data by namespaces and non-namespaces
    content_data_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] >= 0}
    unique_names_namespace = set(content_data_namespaces.keys())
    write_output(output_dir, "unique_names_namespace", unique_names_namespace, config.OUTPUT_DIR_TEST)

    content_data_not_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] < 0}
    unique_names_not_namespace = set(content_data_not_namespaces.keys())
    write_output(output_dir, "unique_names_not_namespace", unique_names_not_namespace, config.OUTPUT_DIR_TEST)

    # Existing analysis: group by levels
    namespace_part_levels = {}
    unique_namespace_parts = set()
    for name, parts in namespace_parts.items():
        for k, v in parts.items():
            namespace_part_levels.setdefault(k, set()).add(v)
            unique_namespace_parts.add(k)
    
    potential_non_namespace = unique_names_not_namespace.intersection(unique_namespace_parts)
    write_output(output_dir, "potential_non_namespace", potential_non_namespace, config.OUTPUT_DIR_TEST)
    
    potential_dangling = set(meta_dangling_links).intersection(unique_namespace_parts)
    write_output(output_dir, "potential_dangling", potential_dangling, config.OUTPUT_DIR_TEST)
            
    # Detecting conflicts with non-namespace pages
    conflicts_non_namespace, conflicts_dangling = detect_non_namespace_conflicts(namespace_parts, potential_non_namespace, potential_dangling)
    write_output(output_dir, "conflicts_non_namespace", conflicts_non_namespace, config.OUTPUT_DIR_TEST)
    write_output(output_dir, "conflicts_dangling", conflicts_dangling, config.OUTPUT_DIR_TEST)

    # TODO Other
    # Extract unique namespace roots
    unique_namespace_roots = set(v["namespace_root"] for v in graph_content_data.values() if v.get("namespace_root"))
    write_output(output_dir, "unique_namespace_roots", unique_namespace_roots, config.OUTPUT_DIR_TEST)

    namespace_part_levels = {k: sorted(v) for k, v in sorted(namespace_part_levels.items(), key=lambda item: len(item[1]), reverse=True)}
    write_output(output_dir, "namespace_part_levels", namespace_part_levels, config.OUTPUT_DIR_TEST)
    write_output(output_dir, "unique_namespace_parts", unique_namespace_parts, config.OUTPUT_DIR_TEST)

    # Extended analysis on namespace details
    namespace_details = analyze_namespace_details(namespace_parts)
    write_output(output_dir, "namespace_details", namespace_details, config.OUTPUT_DIR_TEST)

    # Frequency of each namespace part and their levels
    namespace_frequency, namespace_freq_list = analyze_namespace_frequency(namespace_parts)
    write_output(output_dir, "namespace_frequency", namespace_frequency, config.OUTPUT_DIR_TEST)
    write_output(output_dir, "namespace_freq_list", namespace_freq_list, config.OUTPUT_DIR_TEST)

    # Detecting parent depth conflicts
    parent_depth_conflicts = detect_parent_depth_conflicts(namespace_parts)
    write_output(output_dir, "parent_depth_conflicts", parent_depth_conflicts, config.OUTPUT_DIR_TEST)
