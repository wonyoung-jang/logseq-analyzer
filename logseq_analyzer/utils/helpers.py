"""
Helper functions for file and date processing.
"""

import functools
from pathlib import Path
from typing import Generator, Set, List, Pattern
import logging


def iter_files(root_dir: Path, target_dirs: Set[str]) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the root directory.
    """
    for root, dirs, files in Path.walk(root_dir):
        path_root = Path(root)
        if path_root == root_dir:
            continue

        if path_root.name in target_dirs or path_root.parent.name in target_dirs:
            for file in files:
                yield path_root / file
        else:
            logging.info("Skipping directory %s outside target directories", path_root)
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


def singleton(cls):
    """
    Decorator to create a singleton class that is pickle-friendly.
    """

    # Store original __new__ method
    orig_new = cls.__new__

    # Keep track of instance
    instance = None

    @functools.wraps(orig_new)
    def __new__(cls, *args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = orig_new(cls, *args, **kwargs)
        return instance

    # Replace __new__ method, keep class identity
    cls.__new__ = __new__

    # Store the original __init__ method
    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def __init__(self, *args, **kwargs):
        # Set a flag indicating that initialization has started
        if not hasattr(self, "_init_started"):
            self._init_started = True
            # Call the original init
            orig_init(self, *args, **kwargs)

    # Replace the __init__ method
    cls.__init__ = __init__

    return cls
