from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple

from src import config
from src.core import generate_global_summary

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


def process_namespace_data(
    graph_data: Dict[str, Any], dangling_links: List[str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process namespace data and perform extended analysis for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph content data.
        dangling_links (list): The list of dangling links.

    Returns:
        tuple: A tuple containing:
            - A dictionary with namespace data and analysis results.
            - A dictionary with a global summary of the namespace data.
    """
    namespace_data_subset = {}

    # 01 Conflicts With Existing Pages

    # Find unique names that are not namespaces
    content_data_not_namespaces = {k: v for k, v in graph_data.items() if not v["namespace_level"]}
    unique_names_not_namespace = sorted(content_data_not_namespaces.keys())

    # Find unique names that are namespaces
    content_data_is_namespaces = [k for k, v in graph_data.items() if v.get("namespace_level")]
    unique_names_is_namespace = sorted(content_data_is_namespaces)

    namespace_data = {}
    for name in unique_names_is_namespace:
        namespace_data[name] = {k: v for k, v in graph_data[name].items() if "namespace" in k}

    # Extract namespace parts
    namespace_parts = {k: v["namespace_parts"] for k, v in namespace_data.items() if v.get("namespace_parts")}

    # Existing analysis: group by levels
    namespace_part_levels, unique_namespace_parts = analyze_namespace_part_levels(namespace_parts)

    # Detecting conflicts with non-namespace pages
    potential_non_namespace = unique_namespace_parts.intersection(unique_names_not_namespace)
    potential_dangling = unique_namespace_parts.intersection(dangling_links)
    conflicts_non_namespace, conflicts_dangling = detect_non_namespace_conflicts(
        namespace_parts, potential_non_namespace, potential_dangling
    )

    # 02 Parts that Appear at Multiple Depths
    conflicts_parent_depth, conflicts_parents_unique = detect_parent_depth_conflicts(namespace_parts)

    # 03 General Namespace Data
    namespace_details = analyze_namespace_details(namespace_parts)

    unique_namespaces_per_level = {i: set() for i in range(1, namespace_details["max_depth"] + 1)}
    for parts in namespace_parts.values():
        for part, level in parts.items():
            unique_namespaces_per_level[level].add(part)
    for level, names in unique_namespaces_per_level.items():
        namespace_data_subset[f"unique_namespaces_level_{level}"] = names
    namespace_data_subset["unique_namespaces_per_level"] = {k: len(v) for k, v in unique_namespaces_per_level.items()}

    namespace_frequency, namespace_freq_list = analyze_namespace_frequency(namespace_parts)

    # Namespace queries
    namespace_queries = analyze_namespace_queries(graph_data)

    #################################
    ############ Testing ############
    #################################
    # Test namespace hierarchy visualization
    namespace_hierarchy = visualize_namespace_hierarchy(namespace_parts)

    namespace_data_subset.update(
        {
            "__namespace_data": namespace_data,
            "__namespace_details": namespace_details,
            "__namespace_parts": namespace_parts,
            "unique_names_is_namespace": unique_names_is_namespace,
            "unique_names_not_namespace": unique_names_not_namespace,
            "unique_namespace_parts": unique_namespace_parts,
            "conflicts_non_namespace": conflicts_non_namespace,
            "conflicts_dangling": conflicts_dangling,
            "conflicts_parent_depth": conflicts_parent_depth,
            "conflicts_parents_unique": conflicts_parents_unique,
            "namespace_part_levels": namespace_part_levels,
            "namespace_frequency": namespace_frequency,
            "namespace_freq_list": namespace_freq_list,
            "namespace_queries": namespace_queries,
            "namespace_hierarchy": namespace_hierarchy,
        }
    )

    namespace_global_summary = generate_global_summary(namespace_data_subset)

    return namespace_data_subset, namespace_global_summary


def analyze_namespace_details(namespace_parts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """
    Perform extended analysis on namespace parts.

    Args:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.

    Returns:
        dict: A dictionary containing various statistics about namespaces.
    """
    level_distribution = Counter()
    root_counter = {}
    part_level_details = defaultdict(list)

    for namespace, parts in namespace_parts.items():
        for part, level in parts.items():
            level_distribution[level] += 1
            part_level_details[part].append(level)

        sorted_parts = sorted(parts.items(), key=lambda x: x[1])

        if sorted_parts:
            for sorted_part in sorted_parts:
                part, level = sorted_part
                if level == 0:
                    root_counter[namespace] = part
                if level not in root_counter:
                    root_counter[level] = {}
                root_counter[level][part] = root_counter[level].get(part, 0) + 1

    max_depth = max(level_distribution) if level_distribution else 0

    for k, v in root_counter.items():
        root_counter[k] = {k: v for k, v in sorted(v.items(), key=lambda item: item[1], reverse=True)}

    details = {
        "level_distribution": dict(level_distribution),
        "max_depth": max_depth,
        "root_counter": root_counter,
    }
    return details


def analyze_namespace_frequency(
    namespace_parts: Dict[str, Dict[str, int]],
) -> Tuple[Dict[str, Counter], Dict[str, str]]:
    """
    Analyze frequency of each namespace part and their levels.

    Args:
        namespace_parts (dict): Dictionary of namespace parts per entry.

    Returns:
        tuple: A tuple containing:
            - A dictionary mapping each namespace part to its frequency and levels.
            - A dictionary mapping combined names to their corresponding entries.
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
) -> Tuple[Dict[str, List[str]], Dict[str, Set[str]]]:
    """
    Identify namespace parts that appear at different depths (levels) across entries.

    For each namespace part, we collect the levels at which it appears as well as
    the associated entries. Parts that occur at more than one depth are flagged
    as potential conflicts.

    Returns:
        tuple: A tuple containing two dictionaries:
            - Conflicts with non-namespace pages.
            - Conflicts with dangling links.
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
        tuple: A tuple containing:
            - A dictionary mapping each namespace part to its levels.
            - A set of unique namespace parts.
    """
    namespace_part_levels = {}
    unique_namespace_parts = set()
    for parts in namespace_parts.values():
        for k, v in parts.items():
            namespace_part_levels.setdefault(k, set()).add(v)
            unique_namespace_parts.add(k)
    namespace_part_levels = {
        k: sorted(v) for k, v in sorted(namespace_part_levels.items(), key=lambda item: len(item[1]), reverse=True)
    }
    return namespace_part_levels, unique_namespace_parts


def analyze_namespace_queries(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze namespace queries.

    Args:
        graph_data (dict): The graph content data.

    Returns:
        dict: A dictionary mapping namespace parts to their level and associated entries
    """
    namespace_queries = {}
    for entry, data in graph_data.items():
        if data.get("namespace_queries"):
            namespace_queries[entry] = {}
            namespace_queries[entry]["query"] = data["namespace_queries"]
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
        for part_level in sorted(parts.items(), key=lambda x: x[1]):
            part = part_level[0]
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree
