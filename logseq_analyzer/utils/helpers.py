"""
Helper functions for file and date processing.
"""

import functools
import logging
import threading
from pathlib import Path
from typing import Any, Generator, Type, TypeVar

from ..utils.enums import Format

_T = TypeVar("_T")


def iter_files(root_dir: Path, target_dirs: set[str]) -> Generator[Path, None, None]:
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


def process_aliases(aliases: str) -> list[str]:
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
