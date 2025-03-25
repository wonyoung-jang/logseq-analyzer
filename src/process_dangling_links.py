"""
Module to process dangling links in a graph data structure.
"""

from typing import Any, Dict, Set


def process_dangling_links(all_refs: Dict[str, Any], dangling_links: Set[str]) -> Dict[str, Any]:
    """
    Process dangling links in the graph data.

    Args:
        all_refs (dict): The graph data containing nodes and edges.
        dangling_links (set): Set of dangling links to be processed.

    Returns:
        dict: Dictionary containing dangling links and their corresponding data.
    """
    dangling_dict = {k: v for k, v in all_refs.items() if k in dangling_links}
    dangling_dict = dict(sorted(dangling_dict.items(), key=lambda item: item[1]["count"], reverse=True))
    return dangling_dict
