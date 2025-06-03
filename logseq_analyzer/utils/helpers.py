"""
Helper functions for file and date processing.
"""

import logging
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Generator, TypeVar

from ..utils.enums import Format, MovedFiles

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile

__all__ = [
    "iter_files",
    "process_aliases",
    "sort_dict_by_value",
    "yield_attrs",
    "process_pattern_hierarchy",
    "iter_pattern_split",
    "get_count_and_foundin_data",
    "get_token_map",
    "compile_token_pattern",
    "convert_cljs_date_to_py",
    "BUILT_IN_PROPERTIES",
    "extract_builtin_properties",
    "remove_builtin_properties",
    "format_bytes",
    "SI_UNITS",
    "IEC_UNITS",
    "yield_asset_paths",
    "yield_bak_rec_paths",
    "process_moves",
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
_T = TypeVar("_T")
SI_UNITS = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
IEC_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]

logger = logging.getLogger(__name__)


def iter_files(root_dir: Path, target_dirs: set[str]) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the root directory.
    """
    for root, dirs, files in Path.walk(root_dir):
        if root == root_dir:
            continue

        if root.name in target_dirs or root.parent.name in target_dirs:
            for file in files:
                if Path(file).suffix == Format.ORG.value:
                    logger.info("Skipping org-mode file %s in %s", file, root)
                    continue
                yield root / file
        else:
            logger.info("Skipping directory %s outside target directories", root)
            dirs.clear()


def process_aliases(aliases: str) -> Generator[str, None, None]:
    """Process aliases to extract individual aliases."""
    aliases = aliases.strip()
    current = []
    inside_brackets = False
    i = 0
    while i < len(aliases):
        if aliases[i : i + 2] == "[[":
            inside_brackets = True
            i += 2
        elif aliases[i : i + 2] == "]]":
            inside_brackets = False
            i += 2
        elif aliases[i] == "," and not inside_brackets:
            if part := "".join(current).strip().lower():
                yield part
            current.clear()
            i += 1
        else:
            current.append(aliases[i])
            i += 1

    if part := "".join(current).strip().lower():
        yield part


def sort_dict_by_value(d: dict, value: str = "", reverse: bool = True) -> dict:
    """Sort a dictionary by its values."""
    if not value:
        return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))
    return dict(sorted(d.items(), key=lambda item: item[1][value], reverse=reverse))


def yield_attrs(obj: object) -> Generator[tuple[str, Any], None, None]:
    """Collect slotted attributes from an object."""
    for slot in getattr(type(obj), "__slots__", ()):
        yield slot, getattr(obj, slot)
    for attr, value in getattr(obj, "__dict__", {}).items():
        yield attr, value


def process_pattern_hierarchy(content: str, pattern_mod: ModuleType) -> dict:
    """
    Process a pattern hierarchy to create a mapping of patterns to their respective values.

    Args:
        content (str): The content to process.
        pattern_mod (ModuleType): A module containing regex patterns and their corresponding criteria.

    Returns:
        dict: A dictionary mapping patterns to their respective values.
    """
    output = defaultdict(list)

    for match in pattern_mod.ALL.finditer(content):
        text = match.group(0)
        for pattern, criteria in pattern_mod.PATTERN_MAP.items():
            if re.search(pattern, text):
                output[criteria].append(text)
                break
        else:
            output[pattern_mod.FALLBACK].append(text)

    return output


def iter_pattern_split(pattern: re.Pattern, text: str, maxsplit: int = 0) -> Generator[tuple[int, str], None, None]:
    """
    Emulates re.Pattern.split() but yields sections of text instead of returning a list.
    Iterate over sections of text separated by bullet markers.

    Args:
        pattern (re.Pattern): The regex pattern to match bullet markers.
        text (str): The text to split into sections.
        maxsplit (int): Maximum number of splits. If 0, all sections are returned.

    Yields:
        Generator[tuple[int, str], None, None]: Sections of text with their respective indices.
    """
    count = 0

    for match in pattern.finditer(text):
        if maxsplit and count >= maxsplit:
            break

        if count == 0:
            yield count, text[: match.start()].strip(" \t\n")
            count += 1

        start_of_content = match.end()
        next_match = next(pattern.finditer(text, start_of_content), None)
        end_of_content = next_match.start() if next_match else len(text)

        yield count, text[start_of_content:end_of_content].strip(" \t\n")
        count += 1

    if count == 0:
        yield count, text.strip(" \t\n")


def get_count_and_foundin_data(result: dict, collection: list[str], file: "LogseqFile") -> dict:
    """
    Update the result dictionary with counts and file occurrences.

    Args:
        result (dict): The dictionary to update with counts and file occurrences.
        collection (list[str]): The collection of items to count.
        file (LogseqFile): The file object containing the path information.
    Returns:
        dict: The updated result dictionary with counts and file occurrences.
    """
    for item in collection:
        result.setdefault(item, {"count": 0, "found_in": Counter()})
        result[item]["count"] = result[item].get("count", 0) + 1
        result[item]["found_in"][file.name] += 1
    return result


def get_token_map() -> dict[str, str]:
    """
    Get the date token map.
    """
    return {
        "yyyy": "%Y",
        "xxxx": "%Y",
        "yy": "%y",
        "xx": "%y",
        "MMMM": "%B",
        "MMM": "%b",
        "MM": "%m",
        "M": "%#m",
        "dd": "%d",
        "d": "%#d",
        "D": "%j",
        "EEEE": "%A",
        "EEE": "%a",
        "EE": "%a",
        "E": "%a",
        "e": "%u",
        "HH": "%H",
        "H": "%H",
        "hh": "%I",
        "h": "%I",
        "mm": "%M",
        "m": "%#M",
        "ss": "%S",
        "s": "%#S",
        "SSS": "%f",
        "a": "%p",
        "A": "%p",
        "Z": "%z",
        "ZZ": "%z",
    }


def compile_token_pattern(token_map: dict[str, str]) -> re.Pattern:
    """
    Set the regex pattern for date tokens.
    """
    tokenkeys = token_map.keys()
    pattern = "|".join(re.escape(k) for k in sorted(tokenkeys, key=len, reverse=True))
    return re.compile(pattern)


def convert_cljs_date_to_py(cljs_format: str, token_map: dict[str, str], token_pattern: re.Pattern) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.
    """
    cljs_format = cljs_format.replace("o", "")

    def replace_token(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return token_map.get(token, token)

    return token_pattern.sub(replace_token, cljs_format)


def extract_builtin_properties(properties: set[str]) -> set[str]:
    """Helper function to get built-in properties."""
    return properties.intersection(BUILT_IN_PROPERTIES)


def remove_builtin_properties(properties: set[str]) -> set[str]:
    """Helper function to get properties that are not built-in."""
    return properties.difference(BUILT_IN_PROPERTIES)


def format_bytes(size_bytes: int, system: str = "si", precision: int = 2) -> str:
    """
    Convert a byte value into a human-readable string using SI or IEC units.

    Args:
        size_bytes (int): Number of bytes.
        system (str): 'si' for powers of 1000, 'iec' for powers of 1024.
        precision (int): Number of decimal places.
    Returns:
        str: Human-readable string, e.g. '1.23 MB' or '1.20 MiB'.
    """
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")

    units = SI_UNITS if system == "si" else IEC_UNITS
    base = 1000 if system == "si" else 1024

    if size_bytes < base:
        return f"{size_bytes} {units[0]}"

    idx = 0
    size = float(size_bytes)
    while size >= base and idx < len(units) - 1:
        size /= base
        idx += 1

    return f"{size:.{precision}f} {units[idx]}"


def yield_asset_paths(unlinked_assets: set["LogseqFile"]) -> Generator[Path, None, None]:
    """Yield the file paths of unlinked assets."""
    for asset in unlinked_assets:
        yield asset.path.file


def yield_bak_rec_paths(source_dir: Path) -> Generator[Path, None, None]:
    """Yield the file paths of bak and recycle directories."""
    for root, dirs, files in Path.walk(source_dir):
        for name in dirs + files:
            yield root / name


def process_moves(move: bool, target_dir: Path, paths: Generator[Path, None, None]) -> list[str]:
    """
    Process the moving of files to a specified directory.

    Args:
        move (bool): If True, move the files. If False, simulate the move.
        target_dir (Path): The directory to move files to.
        paths (Generator[Path, None, None]): A generator yielding file paths to move.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    names = [path.name for path in paths]
    if not names:
        return []

    if not move:
        return [MovedFiles.SIMULATED_PREFIX.value] + names

    for src in paths:
        dest = target_dir / src.name
        try:
            shutil.move(str(src), str(dest))
            logger.warning("Moved file: %s to %s", src, dest)
        except (shutil.Error, OSError) as e:
            logger.error("Failed to move file: %s to %s: %s", src, dest, e)
    return names
