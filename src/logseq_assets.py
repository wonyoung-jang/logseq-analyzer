"""
This module handles the processing of assets in the Logseq Analyzer.
"""

from typing import Any, Dict, List, Tuple

from .process_summary_data import extract_summary_subset_files


def handle_assets(
    graph_data: Dict[str, Any],
    summary_data_subsets: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    """
    Handle assets for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data.
        summary_data_subsets (dict): The summary data subsets.

    Returns:
        tuple: A tuple containing two lists:
            - List of assets that are backlinked.
            - List of assets that are not backlinked.
    """
    for _, data in graph_data.items():
        if not data.get("assets", []):
            continue

        for asset in summary_data_subsets["___is_asset"]:
            asset_original_name = graph_data[asset]["name"]

            for asset_mention in data["assets"]:
                if graph_data[asset]["is_backlinked"]:
                    continue

                if asset in asset_mention or asset_original_name in asset_mention:
                    graph_data[asset]["is_backlinked"] = True
                    break

    asset_backlinked_kwargs = {
        "is_backlinked": True,
        "file_type": "asset",
    }
    asset_not_backlinked_kwargs = {
        "is_backlinked": False,
        "file_type": "asset",
    }

    summary_is_asset_backlinked = extract_summary_subset_files(graph_data, **asset_backlinked_kwargs)
    summary_is_asset_not_backlinked = extract_summary_subset_files(graph_data, **asset_not_backlinked_kwargs)

    return summary_is_asset_backlinked, summary_is_asset_not_backlinked
