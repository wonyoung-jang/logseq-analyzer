import logging
import shutil
import argparse
import src.config as config
from pathlib import Path
from typing import Set, Tuple
from src.helpers import is_path_exists
from src.compile_regex import compile_re_config


def setup_logging(log_file: Path) -> None:
    """
    Initialize logging to a file.
    """
    if Path.exists(log_file):
        Path.unlink(log_file)
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info(f"Logging initialized to {log_file}")


def setup_output_directory(output_dir: Path) -> None:
    """
    Ensure that the output directory exists and is empty.

    This function uses shutil.rmtree to efficiently clear the directory,
    then recreates it.

    Args:
        output_dir (Path): The path of the output directory.
    """
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


def setup_logseq_analyzer_args() -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Logseq Analyzer")

    parser.add_argument("-g", "--graph-folder", action="store", help="path to your Logseq graph folder", required=True)

    parser.add_argument("-o", "--output-folder", action="store", help="path to output folder")

    parser.add_argument("-l", "--log-file", action="store", help="path to log file")

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


def setup_logging_and_output(args) -> Tuple[Path, Path]:
    """
    Configure logging and output directory for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.

    Returns:
        Tuple[Path, Path]: The Logseq graph folder and output directory.
    """
    log_file = Path(args.log_file) if args.log_file else Path(config.DEFAULT_LOG_FILE)
    setup_logging(log_file)
    logging.info("Starting Logseq Analyzer.")

    logseq_graph_folder = Path(args.graph_folder)
    output_dir = Path(args.output_folder) if args.output_folder else Path(config.DEFAULT_OUTPUT_DIR)
    setup_output_directory(output_dir)
    return logseq_graph_folder, output_dir


def get_logseq_config_edn(folder_path: Path, args) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    global_config_edn_file = None
    if args.global_config:
        global_config_edn_file = config.GLOBAL_CONFIG_FILE = Path(args.global_config)
        if not is_path_exists(global_config_edn_file):
            return {}

    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    config_edn_file = logseq_folder / config.DEFAULT_CONFIG_FILE
    folders = [folder_path, logseq_folder, config_edn_file]
    for folder in folders:
        if not is_path_exists(folder):
            return {}

    config_patterns = compile_re_config()

    config_edn_data = {
        "journal_page_title_format": "MMM do, yyyy",
        "journal_file_name_format": "yyyy_MM_dd",
        "journals_directory": "journals",
        "pages_directory": "pages",
        "whiteboards_directory": "whiteboards",
        "file_name_format": ":legacy",
    }

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()
        config_edn_data["journal_page_title_format"] = config_patterns["journal_page_title_pattern"].search(config_edn_content).group(1)
        config_edn_data["journal_file_name_format"] = config_patterns["journal_file_name_pattern"].search(config_edn_content).group(1)
        config_edn_data["pages_directory"] = config_patterns["pages_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["journals_directory"] = config_patterns["journals_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["whiteboards_directory"] = config_patterns["whiteboards_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["file_name_format"] = config_patterns["file_name_format_pattern"].search(config_edn_content).group(1)

    # Check global config for overwriting configs
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
    config.PAGES = config_edn_data["pages_directory"]
    config.JOURNALS = config_edn_data["journals_directory"]
    config.WHITEBOARDS = config_edn_data["whiteboards_directory"]

    target_dirs = {
        config.ASSETS,
        config.DRAWS,
        config.JOURNALS,
        config.PAGES,
        config.WHITEBOARDS,
    }

    return target_dirs


def get_logseq_bak_recycle(folder_path: Path) -> Tuple[Path, Path]:
    """
    Extract bak and recycle data from a Logseq.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Tuple[Path, Path]: A tuple containing the bak and recycle folders.
    """
    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    folders = [folder_path, logseq_folder]
    for folder in folders:
        if not is_path_exists(folder):
            return ()

    recycling_folder = logseq_folder / config.DEFAULT_RECYCLE_DIR
    bak_folder = logseq_folder / config.DEFAULT_BAK_DIR

    for folder in [recycling_folder, bak_folder]:
        if not is_path_exists(folder):
            return ()

    return recycling_folder, bak_folder
