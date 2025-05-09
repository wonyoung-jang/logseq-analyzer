"""
Helper functions for file and date processing.
"""

from pathlib import Path
from typing import Generator, Set, List, Pattern
import functools
import logging

from ..utils.enums import Format


def iter_files(root_dir: Path, target_dirs: Set[str]) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the root directory.
    """
    for root, dirs, files in Path.walk(root_dir):
        if root == root_dir:
            continue

        if root.name in target_dirs or root.parent.name in target_dirs:
            for file in files:
                if Path(file).suffix in [Format.ORG.value]:
                    logging.info("Skipping org-mode file %s in %s", file, root)
                    continue
                yield root / file
        else:
            logging.info("Skipping directory %s outside target directories", root)
            dirs.clear()


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def process_aliases(aliases: str) -> List[str]:
    """Process aliases to extract individual aliases."""
    aliases = aliases.strip()
    results = []
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
            part = "".join(current).strip().lower()
            if part:
                results.append(part)
            current = []
            i += 1
        else:
            current.append(aliases[i])
            i += 1

    part = "".join(current).strip().lower()
    if part:
        results.append(part)
    return results


def sort_dict_by_value(d: dict, value: str = "", reverse: bool = True):
    """Sort a dictionary by its values."""
    if not value:
        return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))
    return dict(sorted(d.items(), key=lambda item: item[1][value], reverse=reverse))


def singleton(cls: type) -> type:
    """
    Decorator to create a singleton class that is pickle-friendly.
    """

    orig_new = cls.__new__
    instance = None

    @functools.wraps(orig_new)
    def __new__(cls, *args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = orig_new(cls, *args, **kwargs)
        return instance

    cls.__new__ = __new__

    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def __init__(self, *args, **kwargs):
        if not hasattr(self, "init_started"):
            self.init_started = True
            orig_init(self, *args, **kwargs)

    cls.__init__ = __init__

    return cls
