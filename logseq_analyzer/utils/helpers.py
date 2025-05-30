"""
Helper functions for file and date processing.
"""

import functools
import logging
import re
import threading
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Generator, Type, TypeVar

from ..utils.enums import Format

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

__all__ = [
    "iter_files",
    "process_aliases",
    "sort_dict_by_value",
    "singleton",
    "yield_attrs",
    "process_pattern_hierarchy",
    "iter_pattern_split",
    "get_count_and_foundin_data",
    "get_token_map",
    "compile_token_pattern",
    "convert_cljs_date_to_py",
    "get_attribute_list",
    "BUILT_IN_PROPS",
    "extract_builtin_properties",
    "remove_builtin_properties",
]


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


def singleton(cls: Type[_T]) -> Type[_T]:
    """
    Decorator to create a singleton class that is thread-safe and pickle-friendly.

    Args:
        cls (Type[_T]): The class to be decorated as a singleton.
    Returns:
        Type[_T]: The singleton class.
    """
    instance_attr_name = f"__singleton_instance_{cls.__name__}"
    init_flag_attr_name = f"__singleton_init_done_{cls.__name__}"
    lock_attr_name = f"__singleton_lock_{cls.__name__}"

    if not hasattr(cls, instance_attr_name):
        setattr(cls, instance_attr_name, None)
    if not hasattr(cls, init_flag_attr_name):
        setattr(cls, init_flag_attr_name, False)
    if not hasattr(cls, lock_attr_name):
        setattr(cls, lock_attr_name, threading.Lock())

    original_new = cls.__new__
    original_init = cls.__init__

    @functools.wraps(original_new)
    def new_wrapper(wrapper_cls: Type[_T], *args: Any, **kwargs: Any) -> _T:
        """Wrapper for __new__ to control instance creation."""
        instance_lock = getattr(wrapper_cls, lock_attr_name)
        with instance_lock:
            if getattr(wrapper_cls, instance_attr_name) is None:
                if original_new is object.__new__:
                    current_instance = original_new(wrapper_cls)
                else:
                    current_instance = original_new(wrapper_cls, *args, **kwargs)
                setattr(wrapper_cls, instance_attr_name, current_instance)
        return getattr(wrapper_cls, instance_attr_name)

    @functools.wraps(original_init)
    def init_wrapper(self: _T, *args: Any, **kwargs: Any) -> None:
        """Wrapper for __init__ to ensure it's called only once."""
        decorated_class = type(self)
        instance_lock = getattr(decorated_class, lock_attr_name)
        with instance_lock:
            if not getattr(decorated_class, init_flag_attr_name):
                original_init(self, *args, **kwargs)
                setattr(decorated_class, init_flag_attr_name, True)

    cls.__new__ = new_wrapper
    cls.__init__ = init_wrapper

    return cls


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


def get_count_and_foundin_data(result: dict, collection: list[str], file: "LogseqFile") -> None:
    """
    Update the result dictionary with counts and file occurrences.

    Args:
        result (dict): The dictionary to update with counts and file occurrences.
        collection (list[str]): The collection of items to count.
        file (LogseqFile): The file object containing the path information.
    """
    for item in collection:
        result.setdefault(item, {"count": 0, "found_in": Counter()})
        result[item]["count"] = result[item].get("count", 0) + 1
        result[item]["found_in"][file.path.name] += 1
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


def get_attribute_list(file_list: Generator["LogseqFile", None, None], attribute: str) -> list[Any]:
    """
    Get a list of attribute values from a list of LogseqFile objects.

    Args:
        file_list (Generator[LogseqFile, None, None]): generator of LogseqFile objects.
        attribute (str): The attribute to extract from each LogseqFile object.

    Returns:
        list[Union[str, int]]: list of attribute values.
    """
    return sorted(getattr(file, attribute) for file in file_list)


BUILT_IN_PROPS: frozenset[str] = frozenset(
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


def extract_builtin_properties(properties: set[str]) -> set[str]:
    """Helper function to get built-in properties."""
    return properties.intersection(BUILT_IN_PROPS)


def remove_builtin_properties(properties: set[str]) -> set[str]:
    """Helper function to get properties that are not built-in."""
    return properties.difference(BUILT_IN_PROPS)
