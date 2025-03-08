import logging
import shutil
import argparse
import src.config as config
from pathlib import Path
from typing import Set
from src.helpers import is_path_exists
from src.compile_regex import compile_re_config


def setup_logseq_analyzer_args() -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Logseq Analyzer")

    parser.add_argument("-g", "--graph-folder", action="store", help="path to your Logseq graph folder", required=True)
    parser.add_argument(
        "-wg",
        "--write-graph",
        action="store_true",
        help="write all graph content to output folder (warning: may result in large file)",
    )
    parser.add_argument(
        "-ma",
        "--move-unlinked-assets",
        action="store_true",
        help='move unlinked assets to "unlinked_assets" folder',
    )
    parser.add_argument(
        "-mb",
        "--move-bak",
        action="store_true",
        help="move bak files to bak folder in output directory",
    )
    parser.add_argument(
        "-mr",
        "--move-recycle",
        action="store_true",
        help="move recycle files to recycle folder in output directory",
    )
    parser.add_argument(
        "--global-config",
        action="store",
        help="path to global configuration file",
    )

    return parser.parse_args()


def setup_output_directory() -> Path:
    """
    Setup the output directory for the Logseq Analyzer.

    Raises:
        Exception: If the output directory cannot be created or removed.

    Returns:
        Path: The output directory path.
    """
    output_dir = Path(config.DEFAULT_OUTPUT_DIR)

    if output_dir.exists() and output_dir.is_dir():
        try:
            shutil.rmtree(output_dir)
            logging.info(f"Removed existing output directory: {output_dir}")
        except Exception as e:
            logging.debug(f"Failed to remove directory {output_dir}: {e}")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory: {output_dir}")
    except Exception as e:
        logging.debug(f"Failed to create output directory {output_dir}: {e}")
        raise

    return output_dir


def setup_logging(output: Path) -> None:
    """
    Setup logging configuration for the Logseq Analyzer.
    """
    log_file = Path(output / config.DEFAULT_LOG_FILE)

    if Path.exists(log_file):
        Path.unlink(log_file)
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
    )
    logging.info(f"Logging initialized to {log_file}")
    logging.debug("Logseq Analyzer started.")


def get_logseq_config_edn(folder_path: Path, args: argparse.Namespace) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    config_edn_file = logseq_folder / config.DEFAULT_CONFIG_FILE
    folders = [folder_path, logseq_folder, config_edn_file]
    for folder in folders:
        if not is_path_exists(folder):
            return {}

    config_patterns = compile_re_config()

    config_edn_data = {
        "journal_page_title_format": config.JOURNAL_PAGE_TITLE_FORMAT,
        "journal_file_name_format": config.JOURNAL_FILE_NAME_FORMAT,
        "journals_directory": config.DIR_JOURNALS,
        "pages_directory": config.DIR_PAGES,
        "whiteboards_directory": config.DIR_WHITEBOARDS,
        "file_name_format": config.NAMESPACE_FORMAT,
    }

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()

    config_edn_content = [line.strip() for line in config_edn_content if line.strip()]
    config_edn_content = [line for line in config_edn_content if not line.startswith(";")]
    config_edn_content = "\n".join(config_edn_content)

    journal_page_title = config_patterns["journal_page_title_pattern"].search(config_edn_content)
    journal_file_name = config_patterns["journal_file_name_pattern"].search(config_edn_content)
    pages_directory = config_patterns["pages_directory_pattern"].search(config_edn_content)
    journals_directory = config_patterns["journals_directory_pattern"].search(config_edn_content)
    whiteboards_directory = config_patterns["whiteboards_directory_pattern"].search(config_edn_content)
    file_name_format = config_patterns["file_name_format_pattern"].search(config_edn_content)

    if journal_page_title:
        config_edn_data["journal_page_title_format"] = journal_page_title.group(1)

    if journal_file_name:
        config_edn_data["journal_file_name_format"] = journal_file_name.group(1)

    if pages_directory:
        config_edn_data["pages_directory"] = pages_directory.group(1)

    if journals_directory:
        config_edn_data["journals_directory"] = journals_directory.group(1)

    if whiteboards_directory:
        config_edn_data["whiteboards_directory"] = whiteboards_directory.group(1)

    if file_name_format:
        config_edn_data["file_name_format"] = file_name_format.group(1)

    # Check global config for overwriting configs
    global_config_edn_file = None
    if args.global_config:
        global_config_edn_file = config.GLOBAL_CONFIG_FILE = Path(args.global_config)
        if not is_path_exists(global_config_edn_file):
            return {}

        if global_config_edn_file:
            with global_config_edn_file.open("r", encoding="utf-8") as f:
                content = f.read()
                keys_patterns = {
                    "journal_page_title_format": config_patterns["journal_page_title_pattern"],
                    "journal_file_name_format": config_patterns["journal_file_name_pattern"],
                    "pages_directory": config_patterns["pages_directory_pattern"],
                    "journals_directory": config_patterns["journals_directory_pattern"],
                    "whiteboards_directory": config_patterns["whiteboards_directory_pattern"],
                    "file_name_format": config_patterns["file_name_format_pattern"],
                }

                for key, pattern in keys_patterns.items():
                    match = pattern.search(content)
                    value = match.group(1) if match else ""
                    if value:
                        config_edn_data[key] = value

    config.JOURNAL_PAGE_TITLE_FORMAT = config_edn_data["journal_page_title_format"]
    config.JOURNAL_FILE_NAME_FORMAT = config_edn_data["journal_file_name_format"]
    config.NAMESPACE_FORMAT = config_edn_data["file_name_format"]
    if config.NAMESPACE_FORMAT == ":triple-lowbar":
        config.NAMESPACE_FILE_SEP = "___"
    config.DIR_PAGES = config_edn_data["pages_directory"]
    config.DIR_JOURNALS = config_edn_data["journals_directory"]
    config.DIR_WHITEBOARDS = config_edn_data["whiteboards_directory"]

    target_dirs = {
        config.DIR_ASSETS,
        config.DIR_DRAWS,
        config.DIR_JOURNALS,
        config.DIR_PAGES,
        config.DIR_WHITEBOARDS,
    }

    return target_dirs, config_edn_data


def get_sub_folder(parent, child) -> Path:
    """
    Get the path to a specific subfolder.

    Args:
        parent (Path): The path to the parent folder.
        child (str): The name of the target subfolder (e.g., "recycle", "bak", etc.).

    Returns:
        Path: The path to the specified subfolder or None if not found.
    """
    target = parent / child
    if not is_path_exists(parent) or not is_path_exists(target):
        logging.warning(f"Subfolder does not exist: {target}")
        return None
    logging.debug(f"Successfully received: {target}")
    return target
