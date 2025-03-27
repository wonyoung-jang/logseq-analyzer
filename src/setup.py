"""
Setup module for Logseq Analyzer.
"""

import argparse
import logging
import shutil
from pathlib import Path
from typing import Set


from .config_loader import get_config
from .helpers import get_sub_file_or_folder


CONFIG = get_config()


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
            graph_cache=kwargs.get("graph_cache", False),
            report_format=kwargs.get("report_format", ""),
        )
        return args

    parser = argparse.ArgumentParser(description="Logseq Analyzer")

    parser.add_argument(
        "-g",
        "--graph-folder",
        action="store",
        help="path to your main Logseq graph folder (contains subfolders)",
        required=True,
    )
    parser.add_argument(
        "-wg",
        "--write-graph",
        action="store_true",
        help="write all graph content to output folder (warning: may result in large file)",
    )
    parser.add_argument(
        "--graph-cache",
        action="store_true",
        help="reindex graph cache on run",
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
    parser.add_argument(
        "--report-format",
        action="store",
        help="report format (.txt, .json)",
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
    output_dir = Path(CONFIG.get("DEFAULT", "OUTPUT_DIR"))

    if output_dir.exists() and output_dir.is_dir():
        try:
            shutil.rmtree(output_dir)
            logging.info("Removed existing output directory: %s", output_dir)
        except IsADirectoryError:
            logging.error("Output directory is not empty: %s", output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Created output directory: %s", output_dir)
    except FileExistsError:
        logging.error("Output directory already exists: %s", output_dir)
    except PermissionError:
        logging.error("Permission denied to create output directory: %s", output_dir)
    except OSError as e:
        logging.error("Error creating output directory: %s", e)

    return output_dir


def create_log_file() -> None:
    """
    Setup logging configuration for the Logseq Analyzer.
    """
    output_dir = Path(CONFIG.get("DEFAULT", "OUTPUT_DIR"))
    log_path = CONFIG.get("DEFAULT", "LOG_FILE")
    log_file = Path(output_dir / log_path)

    if Path.exists(log_file):
        Path.unlink(log_file)
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logging.debug("Logging initialized to %s", log_file)
    logging.info("Logseq Analyzer started.")


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

    config_edn_data = {
        "journal_page_title_format": None,
        "journal_file_name_format": None,
        "journals_directory": None,
        "pages_directory": None,
        "whiteboards_directory": None,
        "file_name_format": None,
    }

    for key in config_edn_data:
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
    logseq_default_config_edn_data = {
        "journal_page_title_format": "MMM do, yyyy",
        "journal_file_name_format": "yyyy_MM_dd",
        "journals_directory": "journals",
        "pages_directory": "pages",
        "whiteboards_directory": "whiteboards",
        "file_name_format": ":legacy",
    }

    def_config_file = CONFIG.get("LOGSEQ_STRUCTURE", "CONFIG_FILE")
    config_file = get_sub_file_or_folder(logseq_dir, def_config_file)
    config_edn_content = clean_logseq_config_edn_content(config_file)
    config_edn_data = get_config_edn_data_for_analysis(config_edn_content, config_patterns)
    config_edn_data = {**logseq_default_config_edn_data, **config_edn_data}

    if args.global_config:
        global_config_edn_file = Path(args.global_config)
        CONFIG.set("LOGSEQ_STRUCTURE", "GLOBAL_CONFIG_FILE", args.global_config)
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
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "JOURNAL_PAGE_TITLE_FORMAT", config_edn_data["journal_page_title_format"])
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "JOURNAL_FILE_NAME_FORMAT", config_edn_data["journal_file_name_format"])
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "DIR_PAGES", config_edn_data["pages_directory"])
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "DIR_JOURNALS", config_edn_data["journals_directory"])
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "DIR_WHITEBOARDS", config_edn_data["whiteboards_directory"])
    CONFIG.set("LOGSEQ_CONFIG_DEFAULTS", "NAMESPACE_FORMAT", config_edn_data["file_name_format"])
    ns_fmt = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "NAMESPACE_FORMAT")
    if ns_fmt == ":triple-lowbar":
        CONFIG.set("LOGSEQ_NS", "NAMESPACE_FILE_SEP", "___")


def get_logseq_target_dirs() -> Set[str]:
    """
    Get the target directories based on the configuration data.

    Returns:
        Set[str]: A set of target directories.
    """
    target_dirs = {
        CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_ASSETS"),
        CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_DRAWS"),
        CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_JOURNALS"),
        CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_PAGES"),
        CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_WHITEBOARDS"),
    }

    return target_dirs


def validate_path(path: Path) -> None:
    """
    Validate if a path exists.

    Args:
        path (Path): The path to validate.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    try:
        path.resolve(strict=True)
    except FileNotFoundError:
        logging.warning("Path does not exist: %s", path)
        raise FileNotFoundError(f"Path does not exist: {path}") from None
