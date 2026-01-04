"""Helper functions for file and date processing."""

from __future__ import annotations

import logging
import shutil
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..utils.enums import Format, Moved

if TYPE_CHECKING:
    import re
    from collections.abc import Generator
    from types import ModuleType

    from ..logseq_file.file import LogseqFile

__all__ = [
    "BUILT_IN_PROPERTIES",
    "IEC_UNITS",
    "SI_UNITS",
    "extract_builtin_properties",
    "format_bytes",
    "get_count_and_foundin_data",
    "iter_files",
    "iter_pattern_split",
    "process_aliases",
    "process_moves",
    "process_pattern_hierarchy",
    "remove_builtin_properties",
    "sort_dict_by_value",
    "yield_asset_paths",
    "yield_attrs",
    "yield_bak_rec_paths",
]

BUILT_IN_PROPERTIES: frozenset[str] = frozenset(
    [
        "alias",
        "aliases",
        "background_color",
        "background-color",
        "collapsed",
        "created_at",
        "created-at",
        "custom-id",
        "doing",
        "done",
        "exclude-from-graph-view",
        "filetags",
        "filters",
        "heading",
        "hl-color",
        "hl-page",
        "hl-stamp",
        "hl-type",
        "icon",
        "id",
        "last_modified_at",
        "last-modified-at",
        "later",
        "logseq.color",
        "logseq.macro-arguments",
        "logseq.macro-name",
        "logseq.order-list-type",
        "logseq.query/nlp-date",
        "logseq.table.borders",
        "logseq.table.compact",
        "logseq.table.headers",
        "logseq.table.hover",
        "logseq.table.max-width",
        "logseq.table.stripes",
        "logseq.table.version",
        "logseq.tldraw.page",
        "logseq.tldraw.shape",
        "logseq.tldraw.shape",
        "ls-type",
        "macro",
        "now",
        "public",
        "query-properties",
        "query-sort-by",
        "query-sort-desc",
        "query-table",
        "tags",
        "template-including-parent",
        "template",
        "title",
        "todo",
        "updated-at",
    ]
)

SI_UNITS = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
IEC_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]


class SizeUnit(StrEnum):
    """Enumeration for size units."""

    SI = "si"  # Powers of 1000
    IEC = "iec"  # Powers of 1024


logger = logging.getLogger(__name__)


def iter_files(root_dir: Path, target_dirs: set[str]) -> Generator[Path, None, None]:
    """Recursively iterate over files in the root directory."""
    for root, dirs, files in Path.walk(root_dir):
        if root == root_dir:
            continue
        if any(name in target_dirs for name in (root.name, root.parent.name)):
            for file in files:
                if Path(file).suffix == Format.ORG:
                    logger.info("Skipping org-mode file %s in %s", file, root)
                    continue
                yield root / file
        else:
            logger.info("Skipping directory %s outside target directories", root)
            dirs.clear()


def process_aliases(aliases: str) -> Generator[str, None, None]:
    """Process aliases to extract individual aliases."""
    strip_str = str.strip
    if not (aliases := strip_str(aliases)):
        return

    current = []
    append_current = current.append
    clear_current = current.clear
    lower_str = str.lower
    join_chars = "".join
    inside_brackets = False
    pos = 0
    length = len(aliases)
    while pos < length:
        if aliases[pos : pos + 2] == "[[":
            inside_brackets = True
            pos += 2
        elif aliases[pos : pos + 2] == "]]":
            inside_brackets = False
            pos += 2
        elif aliases[pos] == "," and not inside_brackets:
            if part := lower_str(strip_str(join_chars(current))):
                yield part
            clear_current()
            pos += 1
        else:
            append_current(aliases[pos])
            pos += 1

    if part := lower_str(strip_str(join_chars(current))):
        yield part


def sort_dict_by_value(data: dict, value: str = "", *, reverse: bool = False) -> dict:
    """Sort a dictionary by its values."""
    if value:
        return dict(sorted(data.items(), key=lambda item: item[1][value], reverse=reverse))
    return dict(sorted(data.items(), key=lambda item: item[1], reverse=reverse))


def yield_attrs(obj: object) -> Generator[tuple[str, Any], None, None]:
    """Collect slotted attributes from an object."""
    for slot in getattr(type(obj), "__slots__", ()):
        yield slot, getattr(obj, slot)


def process_pattern_hierarchy(content: str, pattern_mod: ModuleType) -> Generator[tuple[str, str], None, None]:
    """Process a pattern hierarchy to create a mapping of patterns to their respective values.

    Args:
        content (str): The content to process.
        pattern_mod (ModuleType): A module containing regex patterns and their corresponding criteria.

    Yields:
        Generator[tuple[str, str], None, None]: A generator yielding key-value pairs of patterns and their values.

    """
    finditer_all = pattern_mod.ALL.finditer(content)
    pattern_map: dict[re.Pattern, str] = pattern_mod.PATTERN_MAP.items()
    fallback: str = pattern_mod.FALLBACK

    for match in finditer_all:
        text = match.group(0)
        for pattern, criteria in pattern_map:
            if pattern.search(text):
                yield criteria, text
                break
        else:
            yield fallback, text


def iter_pattern_split(pattern: re.Pattern, text: str, maxsplit: int = 0) -> Generator[tuple[int, str], None, None]:
    """Emulate re.Pattern.split() but yields sections of text instead of returning a list.

    Iterate over sections of text separated by bullet markers.

    Args:
        pattern (re.Pattern): The regex pattern to match bullet markers.
        text (str): The text to split into sections.
        maxsplit (int): Maximum number of splits. If 0, all sections are returned.

    Yields:
        Generator[tuple[int, str], None, None]: Sections of text with their respective indices.

    """
    count = 0
    finditer_pattern = pattern.finditer

    for match in finditer_pattern(text):
        if maxsplit and count >= maxsplit:
            break

        if count == 0:
            yield count, text[: match.start()].strip("\t \n")
            count += 1

        content_start = match.end()
        next_match = next(finditer_pattern(text, content_start), None)
        content_end = next_match.start() if next_match else len(text)

        yield count, text[content_start:content_end].strip("\t \n")
        count += 1

    if count == 0:
        yield count, text.strip("\t \n")


def get_count_and_foundin_data(result: dict, collection: list[str], filename: str) -> dict:
    """Update the result dictionary with counts and file occurrences.

    Args:
        result (dict): The dictionary to update with counts and file occurrences.
        collection (list[str]): The collection of items to count.
        filename (str): The name of the file containing the path information.

    Returns:
        dict: The updated result dictionary with counts and file occurrences.

    """
    for item in collection:
        result.setdefault(item, {"count": 0, "found_in": Counter()})
        result[item]["count"] = result[item].get("count", 0) + 1
        result[item]["found_in"][filename] += 1
    return result


def extract_builtin_properties(properties: set[str]) -> set[str]:
    """Get built-in properties."""
    return properties.intersection(BUILT_IN_PROPERTIES)


def remove_builtin_properties(properties: set[str]) -> set[str]:
    """Get properties that are not built-in."""
    return properties.difference(BUILT_IN_PROPERTIES)


def format_bytes(size_bytes: int, system: str = SizeUnit.SI, precision: int = 2) -> str:
    """Convert a byte value into a human-readable string using SI or IEC units.

    Args:
        size_bytes (int): Number of bytes.
        system (str): 'si' for powers of 1000, 'iec' for powers of 1024.
        precision (int): Number of decimal places.

    Returns:
        str: Human-readable string, e.g. '1.23 MB' or '1.20 MiB'.

    """
    if size_bytes < 0:
        msg = "size_bytes must be non-negative"
        raise ValueError(msg)

    units = IEC_UNITS if system == SizeUnit.IEC else SI_UNITS
    base = 1024 if system == SizeUnit.IEC else 1000

    if size_bytes < base:
        return f"{size_bytes} {units[0]}"

    idx = 0
    size = float(size_bytes)
    while size >= base and idx < len(units) - 1:
        size /= base
        idx += 1

    return f"{size:.{precision}f} {units[idx]}"


def yield_asset_paths(unlinked_assets: set[LogseqFile]) -> Generator[Path, None, None]:
    """Yield the file paths of unlinked assets."""
    for asset in unlinked_assets:
        yield asset.path.file


def yield_bak_rec_paths(source_dir: Path) -> Generator[Path, None, None]:
    """Yield the file paths of bak and recycle directories."""
    for root, dirs, files in Path.walk(source_dir):
        for name in dirs + files:
            yield root / name


def process_moves(target_dir: Path, paths: Generator[Path, None, None], *, move: bool) -> list[str]:
    """Process the moving of files to a specified directory.

    Args:
        target_dir (Path): The directory to move files to.
        paths (Generator[Path, None, None]): A generator yielding file paths to move.
        move (bool): If True, move the files. If False, simulate the move.

    Returns:
        list[str]: A list of names of the moved files/folders.

    """
    listpaths = list(paths)
    names = [path.name for path in listpaths]
    if not names:
        return names

    if not move:
        return [Moved.SIMULATED_PREFIX, *names]

    for src in listpaths:
        dest = target_dir / src.name
        try:
            shutil.move(src, dest)
            logger.warning("Moved file: %s to %s", src, dest)
        except (shutil.Error, OSError):
            logger.exception("Failed to move file: %s to %s", src, dest)
    return names
