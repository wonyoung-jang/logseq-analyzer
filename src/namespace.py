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
    1. Some parents may appear across multiple namespaces at different depths.
    2. The split namespace parts may conflict with existing, non-namespace pages.
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


def detect_non_namespace_conflicts(namespace_parts: Dict[str, Dict[str, int]], non_namespace_names: Set[str]) -> Dict[str, List[str]]:
    """
    Check for conflicts between split namespace parts and existing non-namespace page names.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.
        non_namespace_names (set): Set of names from non-namespace pages.

    Returns:
        dict: Mapping of conflicting namespace parts to a list of entry names where the conflict occurs.
    """
    conflicts = defaultdict(list)
    for entry, parts in namespace_parts.items():
        for part in parts.keys():
            if part in non_namespace_names:
                conflicts[part].append(entry)
    return dict(conflicts)


def process_namespace_data(output_dir: Path, graph_content_data: Dict[str, Any]) -> None:
    """
    Process namespace data and perform extended analysis for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        graph_content_data (dict): The graph content data.
    """
    # Extract unique namespace roots
    unique_namespace_roots = set(v["namespace_root"] for v in graph_content_data.values() if v.get("namespace_root"))
    write_output(output_dir, "unique_namespace_roots", unique_namespace_roots, config.OUTPUT_DIR_TEST)

    # Split content data by namespaces and non-namespaces
    content_data_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] >= 0}
    write_output(output_dir, "content_data_namespaces", content_data_namespaces, config.OUTPUT_DIR_TEST)

    unique_namespace_names = set(content_data_namespaces.keys())
    write_output(output_dir, "unique_namespace_names", unique_namespace_names, config.OUTPUT_DIR_TEST)

    content_data_not_namespaces = {k: v for k, v in graph_content_data.items() if v["namespace_level"] < 0}
    write_output(output_dir, "content_data_not_namespaces", content_data_not_namespaces, config.OUTPUT_DIR_TEST)

    unique_not_namespace_names = set(content_data_not_namespaces.keys())
    write_output(output_dir, "unique_not_namespace_names", unique_not_namespace_names, config.OUTPUT_DIR_TEST)

    # Extract namespace parts
    namespace_parts = {k: v["namespace_parts"] for k, v in graph_content_data.items() if v.get("namespace_parts")}
    write_output(output_dir, "__namespace_parts", namespace_parts, config.OUTPUT_DIR_TEST)

    # Existing analysis: group by levels
    namespace_part_levels = {}
    for name, parts in namespace_parts.items():
        for k, v in parts.items():
            namespace_part_levels.setdefault(k, set()).add(v)

    namespace_part_levels = {k: sorted(v) for k, v in sorted(namespace_part_levels.items(), key=lambda item: len(item[1]), reverse=True)}
    write_output(output_dir, "namespace_part_levels", namespace_part_levels, config.OUTPUT_DIR_TEST)

    namespace_part_levels_has_one_level = {k: v for k, v in namespace_part_levels.items() if len(v) == 1}
    write_output(output_dir, "namespace_part_levels_has_one_level", namespace_part_levels_has_one_level, config.OUTPUT_DIR_TEST)

    namespace_part_levels_has_multiple_levels = {k: v for k, v in namespace_part_levels.items() if len(v) > 1}
    write_output(output_dir, "namespace_part_levels_has_multiple_levels", namespace_part_levels_has_multiple_levels, config.OUTPUT_DIR_TEST)

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

    # Detecting conflicts with non-namespace pages
    non_namespace_conflicts = detect_non_namespace_conflicts(namespace_parts, unique_not_namespace_names)
    write_output(output_dir, "non_namespace_conflicts", non_namespace_conflicts, config.OUTPUT_DIR_TEST)
