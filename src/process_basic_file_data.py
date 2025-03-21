import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Pattern, Tuple

from src.helpers import process_logseq_filename_key
from src.process_content_data import process_content_data
from src.logseq_uri_convert import convert_uri_to_logseq_url


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
    data = {}
    data = get_file_metadata(file_path, data)
    content = get_file_content(file_path)
    content_bullets = []
    primary_bullet = ""

    if content:
        # Count characters
        data["char_count"] = len(content)
        # Count bullets
        bullet_count = 0
        if data["file_path_suffix"] == ".md":
            bullet_content = patterns["bullet"].split(content)
            if len(bullet_content) > 1:
                primary_bullet = bullet_content[0].strip()
                content_bullets = [bullet.strip() for bullet in bullet_content[1:]]
                empty_bullets = [bullet for bullet in content_bullets if not bullet]
                bullet_count_empty = len(empty_bullets)
                bullet_count = len(content_bullets)
            else:
                bullet_count = 0
                bullet_count_empty = 0
            data["bullet_count"] = bullet_count
            data["bullet_count_empty"] = bullet_count_empty
        # Calculate bullet density
        if bullet_count > 0:
            data["bullet_density"] = round(data["char_count"] / bullet_count, 2)

    data = process_content_data(data, content, patterns, primary_bullet)

    return data, content_bullets


def get_file_metadata(file_path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from a file.

    Args:
        file_path (Path): The path to the file.
        data (Dict[str, Any]): A dictionary to store metadata.

    Returns:
        Dict[str, Any]: A dictionary with file metadata.
    """
    stat = file_path.stat()
    parent = file_path.parent.name.lower()
    name = process_logseq_filename_key(file_path.stem, parent)
    suffix = file_path.suffix.lower() if file_path.suffix else None
    now = datetime.now().timestamp()
    date_modified = stat.st_mtime

    try:
        date_created = stat.st_birthtime
    except AttributeError:
        date_created = stat.st_ctime
        logging.warning(f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.")

    data["id"] = name[:2] if len(name) > 1 else f"!{name[0]}"
    data["name"] = name
    data["name_secondary"] = f"{name} {parent} + {suffix}".lower()
    data["file_path"] = str(file_path)
    data["file_path_parent_name"] = parent
    data["file_path_name"] = name
    data["file_path_suffix"] = suffix if suffix else None
    data["file_path_parts"] = list(file_path.parts)
    data["date_created"] = date_created
    data["date_modified"] = date_modified
    data["time_existed"] = now - date_created
    data["time_unmodified"] = now - date_modified
    data["uri"] = file_path.as_uri()
    data["logseq_url"] = convert_uri_to_logseq_url(data["uri"])
    data["size"] = stat.st_size

    return data


def get_file_content(file_path: Path) -> Optional[str]:
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
