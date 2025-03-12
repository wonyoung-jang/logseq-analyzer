import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Pattern, Tuple

from src.helpers import process_filename_key


def init_metadata() -> Dict[str, Any]:
    """
    Initialize an empty metadata dictionary.

    Returns:
        Dict[str, Any]: An empty dictionary for metadata.
    """
    return {
        "id": None,
        "name": None,
        "name_secondary": None,
        "file_path": None,
        "file_path_parent_name": None,
        "file_path_name": None,
        "file_path_suffix": None,
        "file_path_parts": None,
        "date_created": None,
        "date_modified": None,
        "time_existed": None,
        "time_unmodified": None,
        "size": 0,
        "uri": None,
        "char_count": 0,
        "bullet_count": 0,
        "bullet_density": 0,
    }


def process_single_file(file_path: Path, patterns: Dict[str, Pattern]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Process a single file: extract metadata, read content, and compute content-based metrics.

    Metrics computed are character count and bullet count using provided regex patterns.

    Args:
        file_path (Path): The file path to process.
        patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.

    Returns:
        Tuple[Dict[str, Any], Optional[str]]: A tuple containing metadata dictionary and file content (or None if reading failed).
    """
    metadata = get_file_metadata(file_path)
    content = read_file_content(file_path)
    primary_bullet = ""
    content_bullets = []

    if content:
        metadata["char_count"] = len(content)
        bullet_count = 0
        if metadata["file_path_suffix"] == ".md":
            bullet_content = patterns["bullet"].split(content)
            primary_bullet = bullet_content[0].strip()
            content_bullets = [bullet.strip() for bullet in bullet_content[1:]]
            bullet_count = len(content_bullets) if content_bullets else 0
        metadata["bullet_count"] = bullet_count
        metadata["bullet_density"] = metadata["char_count"] // bullet_count if bullet_count > 0 else 0
    return metadata, content, primary_bullet, content_bullets


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a file.

    Metadata includes: id, name, name_secondary, file paths, dates (creation, modification),
    time since creation, and size.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Dict[str, Any]: A dictionary with file metadata.
    """
    metadata = init_metadata()

    stat = file_path.stat()
    parent = file_path.parent.name
    name = process_filename_key(file_path.stem, parent)
    suffix = file_path.suffix.lower() if file_path.suffix else None
    now = datetime.now().replace(microsecond=0)
    date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)

    try:
        date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
    except AttributeError:
        date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
        logging.warning(f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.")

    metadata["id"] = name[:2].lower() if len(name) > 1 else f"!{name[0].lower()}"
    metadata["name"] = name
    metadata["name_secondary"] = f"{name} {parent} + {suffix}".lower()
    metadata["file_path"] = str(file_path)
    metadata["file_path_parent_name"] = parent.lower()
    metadata["file_path_name"] = name.lower()
    metadata["file_path_suffix"] = suffix.lower() if suffix else None
    metadata["file_path_parts"] = file_path.parts
    metadata["date_created"] = date_created
    metadata["date_modified"] = date_modified
    metadata["time_existed"] = now - date_created
    metadata["time_unmodified"] = now - date_modified
    metadata["size"] = stat.st_size
    metadata["uri"] = file_path.as_uri()

    return metadata


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Read the text content of a file using utf-8 encoding.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Optional[str]: The file content as a string if successful; otherwise, None.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
        return None
    except Exception as e:
        logging.warning(f"Failed to read file {file_path}: {e}")
        return None
