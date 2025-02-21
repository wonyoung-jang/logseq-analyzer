import logging
import shutil
from pathlib import Path


def init_logging(log_file: Path) -> None:
    '''
    Initialize logging to a file.
    '''
    if Path.exists(log_file):
        Path.unlink(log_file)
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    

def init_output_directory(directory: Path) -> None:
    '''
    Ensure that the output directory exists and is empty.

    This function uses shutil.rmtree to efficiently clear the directory,
    then recreates it.

    Args:
        directory (Path): The path of the output directory.
    '''
    if directory.exists() and directory.is_dir():
        try:
            shutil.rmtree(directory)
            logging.info('Cleared the existing output directory: %s', directory)
        except Exception as e:
            logging.exception('Failed to remove directory %s: %s', directory, e)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logging.info('Created output directory: %s', directory)
    except Exception as e:
        logging.exception('Failed to create output directory %s: %s', directory, e)
        raise
