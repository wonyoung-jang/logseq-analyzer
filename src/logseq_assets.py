from src import config
from src.process_summary_data import extract_summary_subset_files
from src.reporting import write_output


def handle_assets(graph_data: dict, summary_data_subsets: dict) -> None:
    """
    Handle assets for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data.
        summary_data_subsets (dict): The summary data subsets.
    """
    for name, data in graph_data.items():
        if not data["assets"]:
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

    write_output(
        config.DEFAULT_OUTPUT_DIR,
        "is_asset_backlinked",
        summary_is_asset_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )
    write_output(
        config.DEFAULT_OUTPUT_DIR,
        "is_asset_not_backlinked",
        summary_is_asset_not_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )

    return summary_is_asset_not_backlinked
