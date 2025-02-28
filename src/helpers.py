import logging
import re
import shutil
import src.config as config
from pathlib import Path
from typing import Optional, Dict, Any, Generator, Set, Tuple


def iter_files(directory: Path, target_dirs: Optional[Set[str]] = None) -> Generator[Path, None, None]:
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


def move_all_folder_content(input_dir: Path, target_dir: Path) -> None:
    """
    Move all folders from one directory to another.

    Args:
        input_dir (Path): The source directory.
        target_dir (Path): The destination directory.
    """
    if not input_dir.is_dir():
        logging.error(f"Directory not found: {input_dir}")
        return

    if not target_dir.is_dir():
        logging.error(f"Directory not found: {target_dir}")
        return

    for root, dirs, files in Path.walk(input_dir):
        for dir in dirs:
            try:
                shutil.move(Path(root) / dir, target_dir / dir)
                logging.info(f"Moved folder: {dir}")
            except Exception as e:
                logging.error(f"Failed to move folder: {dir}: {e}")
        for file in files:
            try:
                shutil.move(Path(root) / file, target_dir / file)
                logging.info(f"Moved file: {file}")
            except Exception as e:
                logging.error(f"Failed to move file: {file}: {e}")


def extract_logseq_bak_recycle(folder_path: Path) -> Tuple[Path, Path]:
    """
    Extract bak and recycle data from a Logseq.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Tuple[Path, Path]: A tuple containing the bak and recycle folders.
    """
    if not folder_path.is_dir():
        logging.error(f"Directory not found: {folder_path}")
        return ()

    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    if not logseq_folder.is_dir():
        logging.error(f"Directory not found: {logseq_folder}")
        return ()

    recycling_folder = logseq_folder / config.DEFAULT_RECYCLE_DIR
    bak_folder = logseq_folder / config.DEFAULT_BAK_DIR

    for folder in [recycling_folder, bak_folder]:
        if not folder.is_dir():
            logging.error(f"Directory not found: {folder}")
            return ()

    return recycling_folder, bak_folder


def extract_logseq_config_edn(folder_path: Path) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    if not is_path_exists(folder_path):
        return {}

    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    if not is_path_exists(logseq_folder):
        return {}

    config_edn_file = logseq_folder / config.DEFAULT_CONFIG_FILE
    if not is_path_exists(config_edn_file):
        return {}

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

    journal_page_title_pattern = re.compile(r':journal/page-title-format\s+"([^"]+)"')
    journal_file_name_pattern = re.compile(r':journal/file-name-format\s+"([^"]+)"')
    feature_enable_journals_pattern = re.compile(r":feature/enable-journals\?\s+(true|false)")
    feature_enable_whiteboards_pattern = re.compile(r":feature/enable-whiteboards\?\s+(true|false)")
    pages_directory_pattern = re.compile(r':pages-directory\s+"([^"]+)"')
    journals_directory_pattern = re.compile(r':journals-directory\s+"([^"]+)"')
    whiteboards_directory_pattern = re.compile(r':whiteboards-directory\s+"([^"]+)"')
    file_name_format_pattern = re.compile(r":file/name-format\s+(.+)")

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()
        config_edn_data["journal_page_title_format"] = journal_page_title_pattern.search(config_edn_content).group(1)
        config_edn_data["journal_file_name_format"] = journal_file_name_pattern.search(config_edn_content).group(1)
        config_edn_data["feature_enable_journals"] = feature_enable_journals_pattern.search(config_edn_content).group(1)
        config_edn_data["feature_enable_whiteboards"] = feature_enable_whiteboards_pattern.search(config_edn_content).group(1)
        config_edn_data["pages_directory"] = pages_directory_pattern.search(config_edn_content).group(1)
        config_edn_data["journals_directory"] = journals_directory_pattern.search(config_edn_content).group(1)
        config_edn_data["whiteboards_directory"] = whiteboards_directory_pattern.search(config_edn_content).group(1)
        config_edn_data["file_name_format"] = file_name_format_pattern.search(config_edn_content).group(1)

    setattr(
        config,
        "JOURNAL_PAGE_TITLE_FORMAT",
        config_edn_data["journal_page_title_format"],
    )
    setattr(
        config,
        "JOURNAL_FILE_NAME_FORMAT",
        config_edn_data["journal_file_name_format"],
    )
    setattr(config, "PAGES", config_edn_data["pages_directory"])
    setattr(config, "JOURNALS", config_edn_data["journals_directory"])
    setattr(config, "WHITEBOARDS", config_edn_data["whiteboards_directory"])
    target_dirs = {
        config.ASSETS,
        config.DRAWS,
        config.JOURNALS,
        config.PAGES,
        config.WHITEBOARDS,
    }
    return target_dirs


def move_unlinked_assets(summary_is_asset_not_backlinked: Dict[str, Any], graph_meta_data: Dict[str, Any]) -> None:
    """
    Move unlinked assets to a separate directory.

    Args:
        summary_is_asset_not_backlinked (Dict[str, Any]): Summary data for unlinked assets.
        graph_meta_data (Dict[str, Any]): Metadata for each file.
    """
    to_delete_dir = Path(config.DEFAULT_TO_DELETE_DIR)
    if not is_path_exists(to_delete_dir):
        create_directory(to_delete_dir)

    for name in summary_is_asset_not_backlinked.keys():
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = to_delete_dir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.info(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to move unlinked asset: {file_path} to {new_path}: {e}")


def is_path_exists(path: Path) -> bool:
    """
    Check if a directory exists.

    Args:
        directory (Path): The directory to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    if not path.exists():
        logging.error(f"Path not found: {path}")
        return False
    return True


def create_directory(directory: Path) -> None:
    """
    Create a directory if it does not exist.

    Args:
        directory (Path): The directory to create.
    """
    directory.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created directory: {directory}")
