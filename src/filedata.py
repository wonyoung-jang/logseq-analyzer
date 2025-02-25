import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Pattern, Tuple
from src.keynames import process_key_name


def process_single_file(
    file_path: Path, patterns: Dict[str, Pattern]
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Process a single file: extract metadata, read content, and compute content-based metrics.

    Metrics computed are character count and bullet count using provided regex patterns.

    Args:
        file_path (Path): The file path to process.
        patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.

    Returns:
        Tuple[Dict[str, Any], Optional[str]]: A tuple containing metadata dictionary and file content (or None if reading failed).
    """
    metadata = extract_file_metadata(file_path)
    content = read_file_content(file_path)

    if content:
        metadata["char_count"] = len(content)
        bullet_count = len(patterns["bullet"].findall(content))
        metadata["bullet_count"] = bullet_count
        metadata["bullet_density"] = (
            metadata["char_count"] // bullet_count if bullet_count > 0 else 0
        )
    else:
        metadata["char_count"] = 0
        metadata["bullet_count"] = 0
        metadata["bullet_density"] = 0
    return metadata, content


def extract_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a file.

    Metadata includes: id, name, name_secondary, file paths, dates (creation, modification),
    time since creation, and size.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Dict[str, Any]: A dictionary with file metadata.
    """
    stat = file_path.stat()
    parent = file_path.parent.name
    name = process_key_name(file_path.stem, parent)
    suffix = file_path.suffix.lower() if file_path.suffix else None
    now = datetime.now().replace(microsecond=0)

    try:
        date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
    except AttributeError:
        date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
        logging.warning(
            f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead."
        )

    date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)

    time_existed = now - date_created
    time_unmodified = now - date_modified

    metadata = {
        "id": name[:2].lower() if len(name) > 1 else f"!{name[0].lower()}",
        "name": name,
        "name_secondary": f"{name} {parent} + {suffix}".lower(),
        "file_path": str(file_path),
        "file_path_parent_name": parent.lower(),
        "file_path_name": name.lower(),
        "file_path_suffix": suffix.lower() if suffix else None,
        "file_path_parts": file_path.parts,
        "date_created": date_created,
        "date_modified": date_modified,
        "time_existed": time_existed,
        "time_unmodified": time_unmodified,
        "size": stat.st_size,
    }
    return metadata


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Read the text content of a file using UTF-8 encoding.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Optional[str]: The file content as a string if successful; otherwise, None.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.warning(
            f"File not found: {file_path}"
        )  # More specific logging for file not found
        return None
    except Exception as e:
        logging.warning(f"Failed to read file {file_path}: {e}")
        return None
