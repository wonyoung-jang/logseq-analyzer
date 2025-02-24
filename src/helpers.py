from pathlib import Path
from typing import Optional, Dict, Any, Generator, Set
import logging
import re
import shutil

import src.logseq_config as logseq_config


def iter_files(
    directory: Path, target_dirs: Optional[Set[str]] = None
) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the given directory.

    If target_dirs is provided, only yield files that reside within directories
    whose names are in the target_dirs set.

    Args:
        directory (Path): The root directory to search.
        target_dirs (Optional[Set[str]]): Set of allowed parent directory names.

    Yields:
        Path: File paths that match the criteria.
    """
    if not directory.is_dir():
        logging.error(f"Directory not found: {directory}")
        return

    for path in directory.rglob("*"):
        if path.is_file():
            if target_dirs:
                if path.parent.name in target_dirs:
                    yield path
                else:
                    logging.info(f"Skipping file {path} outside target directories")
            else:
                yield path


def extract_logseq_config_edn(file_path: Path) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        file_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    if not file_path.is_dir():
        logging.error(f"Directory not found: {file_path}")
        return {}

    logseq_folder = file_path / "logseq"
    if not logseq_folder.is_dir():
        logging.error(f"Directory not found: {logseq_folder}")
        return {}

    config_edn_file = logseq_folder / "config.edn"
    if not config_edn_file.is_file():
        logging.error(f"File not found: {config_edn_file}")
        return {}

    journal_page_title_pattern = re.compile(r':journal/page-title-format\s+"([^"]+)"')
    journal_file_name_pattern = re.compile(r':journal/file-name-format\s+"([^"]+)"')
    feature_enable_journals_pattern = re.compile(
        r":feature/enable-journals\?\s+(true|false)"
    )
    feature_enable_whiteboards_pattern = re.compile(
        r":feature/enable-whiteboards\?\s+(true|false)"
    )
    pages_directory_pattern = re.compile(r':pages-directory\s+"([^"]+)"')
    journals_directory_pattern = re.compile(r':journals-directory\s+"([^"]+)"')
    whiteboards_directory_pattern = re.compile(r':whiteboards-directory\s+"([^"]+)"')
    file_name_format_pattern = re.compile(r":file/name-format\s+(.+)")

    config_edn_data = {
        "journal_page_title_format": "MMM do, yyyy",
        "journal_file_name_format": "yyyy_MM_dd",
        "feature_enable_journals": "true",
        "feature_enable_whiteboards": "true",
        "pages_directory": "pages",
        "journals_directory": "journals",
        "whiteboards_directory": "whiteboards",
        "file_name_format": ":triple-lowbar",
    }

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()
        config_edn_data["journal_page_title_format"] = (
            journal_page_title_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["journal_file_name_format"] = journal_file_name_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["feature_enable_journals"] = (
            feature_enable_journals_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["feature_enable_whiteboards"] = (
            feature_enable_whiteboards_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["pages_directory"] = pages_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["journals_directory"] = journals_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["whiteboards_directory"] = whiteboards_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["file_name_format"] = file_name_format_pattern.search(
            config_edn_content
        ).group(1)

    setattr(
        logseq_config,
        "JOURNAL_PAGE_TITLE_FORMAT",
        config_edn_data["journal_page_title_format"],
    )
    setattr(
        logseq_config,
        "JOURNAL_FILE_NAME_FORMAT",
        config_edn_data["journal_file_name_format"],
    )
    setattr(logseq_config, "PAGES_DIRECTORY", config_edn_data["pages_directory"])
    setattr(logseq_config, "JOURNALS_DIRECTORY", config_edn_data["journals_directory"])
    setattr(
        logseq_config, "WHITEBOARDS_DIRECTORY", config_edn_data["whiteboards_directory"]
    )
    target_dirs = {
        logseq_config.ASSETS_DIRECTORY,
        logseq_config.DRAWS_DIRECTORY,
        logseq_config.JOURNALS_DIRECTORY,
        logseq_config.PAGES_DIRECTORY,
        logseq_config.WHITEBOARDS_DIRECTORY,
    }
    return target_dirs


def move_unlinked_assets(
    summary_is_asset_not_backlinked: Dict[str, Any], graph_meta_data: Dict[str, Any]
) -> None:
    """
    Move unlinked assets to a separate directory.

    Args:
        summary_is_asset_not_backlinked (Dict[str, Any]): Summary data for unlinked assets.
        graph_meta_data (Dict[str, Any]): Metadata for each file.
    """
    unlinked_assets_dir = Path("unlinked_assets")
    if not unlinked_assets_dir.exists():
        unlinked_assets_dir.mkdir()
        logging.info(f"Created directory: {unlinked_assets_dir}")

    for name in summary_is_asset_not_backlinked.keys():
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = unlinked_assets_dir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.info(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(
                f"Failed to move unlinked asset: {file_path} to {new_path}: {e}"
            )
