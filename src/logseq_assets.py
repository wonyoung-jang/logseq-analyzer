from typing import Tuple

from .process_summary_data import extract_summary_subset_files


def handle_assets(graph_data: dict, summary_data_subsets: dict) -> Tuple[dict, dict]:
    """
    Handle assets for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data.
        summary_data_subsets (dict): The summary data subsets.
        
    Returns:
        Tuple[dict, dict]: Two dictionaries containing assets that are backlinked and not backlinked.
    """
    for name, data in graph_data.items():
        if not data.get("assets", []):
            continue

        for asset in summary_data_subsets["is_asset"]:
            asset_name_secondary = graph_data[asset]["name"]

            for asset_mention in data["assets"]:
                if graph_data[asset]["is_backlinked"]:
                    continue

                if asset in asset_mention or asset_name_secondary in asset_mention:
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
