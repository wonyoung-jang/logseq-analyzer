import logging
import shutil
import argparse
import src.config as config
from pathlib import Path
from typing import Set


def get_logseq_analyzer_args(**kwargs: dict) -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Args:
        **kwargs: Keyword arguments for GUI mode.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    if kwargs:
        args = argparse.Namespace(
            graph_folder=kwargs.get("graph_folder"),
            global_config=kwargs.get("global_config_file"),
            move_unlinked_assets=kwargs.get("move_assets", False),
            move_bak=kwargs.get("move_bak", False),
            move_recycle=kwargs.get("move_recycle", False),
            write_graph=kwargs.get("write_graph", False),
        )
        return args

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


def create_output_directory() -> Path:
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


def create_log_file(output: Path) -> None:
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


def clean_logseq_config_edn_content(config_file: Path) -> str:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        str: The content of the configuration file.
    """
    with config_file.open("r", encoding="utf-8") as f:
        config_edn_content = ""
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if ";" in line:
                line = line.split(";")[0].strip()
            config_edn_content += f"{line}\n"
    return config_edn_content


def get_config_edn_data_for_analysis(config_edn_content: str, config_patterns: dict) -> dict:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        config_edn_content (str): The content of the configuration file.
        config_patterns (dict): A dictionary of regex patterns for extracting configuration data.

    Returns:
        dict: A dictionary containing the extracted configuration data.
    """
    if not config_edn_content:
        logging.warning("No config.edn content found.")
        return {}

    config_edn_data = {k: None for k, v in config.CONFIG_EDN_DATA.items()}
    for key in config_edn_data.keys():
        pattern = config_patterns.get(f"{key}_pattern")
        if pattern:
            match = pattern.search(config_edn_content)
            if match:
                config_edn_data[key] = match.group(1)
    config_edn_data = {k: v for k, v in config_edn_data.items() if v is not None}

    return config_edn_data


def get_logseq_config_edn(args, logseq_dir: Path, config_patterns: dict) -> dict:
    """
    Get the configuration data from the Logseq configuration file.

    Args:
        args (argparse.Namespace): The command line arguments.
        logseq_dir (Path): The path to the Logseq graph folder.
        config_patterns (dict): A dictionary of regex patterns for extracting configuration data.

    Returns:
        dict: A dictionary containing the extracted configuration data.
    """
    config_file = get_sub_file_or_folder(logseq_dir, config.DEFAULT_CONFIG_FILE)
    config_edn_content = clean_logseq_config_edn_content(config_file)
    config_edn_data = get_config_edn_data_for_analysis(config_edn_content, config_patterns)
    config_edn_data = {**config.CONFIG_EDN_DATA, **config_edn_data}
    if args.global_config:
        global_config_edn_file = config.GLOBAL_CONFIG_FILE = Path(args.global_config)
        global_config_edn_content = clean_logseq_config_edn_content(global_config_edn_file)
        global_config_edn_data = get_config_edn_data_for_analysis(global_config_edn_content, config_patterns)
        config_edn_data = {**config_edn_data, **global_config_edn_data}
    return config_edn_data


def set_logseq_config_edn_data(config_edn_data: dict) -> None:
    """
    Set the Logseq configuration data.

    Args:
        config_edn_data (dict): The configuration data.
    """
    config.JOURNAL_PAGE_TITLE_FORMAT = config_edn_data["journal_page_title_format"]
    config.JOURNAL_FILE_NAME_FORMAT = config_edn_data["journal_file_name_format"]
    config.DIR_PAGES = config_edn_data["pages_directory"]
    config.DIR_JOURNALS = config_edn_data["journals_directory"]
    config.DIR_WHITEBOARDS = config_edn_data["whiteboards_directory"]
    config.NAMESPACE_FORMAT = config_edn_data["file_name_format"]
    if config.NAMESPACE_FORMAT == ":triple-lowbar":
        config.NAMESPACE_FILE_SEP = "___"


def get_logseq_target_dirs() -> Set[str]:
    """
    Get the target directories based on the configuration data.

    Args:
        config_edn_data (dict): The configuration data.

    Returns:
        Set[str]: A set of target directories.
    """
    target_dirs = {
        config.DIR_ASSETS,
        config.DIR_DRAWS,
        config.DIR_JOURNALS,
        config.DIR_PAGES,
        config.DIR_WHITEBOARDS,
    }

    return target_dirs


def get_sub_file_or_folder(parent: Path, child: str) -> Path:
    """
    Get the path to a specific subfolder.

    Args:
        parent (Path): The path to the parent folder.
        child (str): The name of the target subfolder (e.g., "recycle", "bak", etc.).

    Returns:
        Path: The path to the specified subfolder or None if not found.
    """
    target = parent / child

    if not parent.exists() or not target.exists():
        logging.warning(f"Subfolder does not exist: {target}")
        return None
    logging.debug(f"Successfully received: {target}")

    return target


def get_or_create_subdir(parent: Path, child: str) -> Path:
    """
    Get a subdirectory or create it if it doesn't exist.

    Args:
        parent (Path): The path to the parent folder.
        child (str): The name of the target subfolder.

    Returns:
        Path: The path to the specified subfolder.
    """
    target = parent / child

    if not parent.exists():
        logging.warning(f"Parent folder does not exist: {parent}")
        return None
    elif not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created subdirectory: {target}")
        except Exception as e:
            logging.error(f"Failed to create subdirectory {target}: {e}")
            raise
    else:
        logging.debug(f"Subdirectory already exists: {target}")

    return target
