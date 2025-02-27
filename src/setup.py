import logging
import shutil
from pathlib import Path


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


def setup_output_directory(directory: Path) -> None:
    """
    Ensure that the output directory exists and is empty.

    This function uses shutil.rmtree to efficiently clear the directory,
    then recreates it.

    Args:
        directory (Path): The path of the output directory.
    """
    if directory.exists() and directory.is_dir():
        try:
            shutil.rmtree(directory)
            logging.info(f"Removed existing output directory: {directory}")
        except Exception as e:
            logging.debug(f"Failed to remove directory {directory}: {e}")
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory: {directory}")
    except Exception as e:
        logging.debug(f"Failed to create output directory {directory}: {e}")
        raise
