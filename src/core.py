"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from pathlib import Path
from typing import Any, Dict, List, Pattern, Tuple

from .process_basic_file_data import process_single_file
from .process_content_data import post_processing_content
from .process_summary_data import process_summary_data


def process_graph_files(
    modded_files: Path,
    patterns: Dict[str, Pattern],
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Process all files in the Logseq graph folder.

    Args:
        modded_files (Path): The modified files to process.
        patterns (dict): The compiled regex patterns.

    Returns:
        Tuple[Dict[str, Any], Dict[str, List[str]]]: A tuple containing the graph metadata and content bullets data.
    """
    graph_data = {}
    meta_content_bullets = {}

    for file_path in modded_files:
        file_data, content_bullets = process_single_file(file_path, patterns)

        name = file_data["name"]
        if name in graph_data:
            name = file_data["name_secondary"]

        graph_data[name] = file_data
        meta_content_bullets[name] = content_bullets

    return graph_data, meta_content_bullets


def core_data_analysis(
    graph_meta_data: dict,
) -> Tuple[dict, dict, dict, dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        graph_meta_data (dict): The graph data to analyze.

    Returns:
        Tuple[dict, dict, dict, dict, dict]: A tuple containing:
            - Alphanumeric dictionary.
            - Alphanumeric dictionary with namespace.
            - Dangling links.
            - Processed graph data.
            - All references.
    """
    graph_data_post, alphanum_dictionary, alphanum_dictionary_ns, dangling_links, all_refs = post_processing_content(
        graph_meta_data
    )

    graph_data = process_summary_data(graph_data_post, alphanum_dictionary, alphanum_dictionary_ns)

    return (
        alphanum_dictionary,
        alphanum_dictionary_ns,
        dangling_links,
        graph_data,
        all_refs,
    )
