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
