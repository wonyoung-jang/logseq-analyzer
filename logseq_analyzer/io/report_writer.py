"""Reporting module for writing output to files, including HTML reports."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

logger = logging.getLogger(__name__)


def _write(path: Path, data: dict) -> None:
    """Write the data to a plain text file with the given prefix and count."""
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{path.name}\n")
        f.write(f"COUNT: {len(data)}\n\n")
        _write_recursive(f, data, level=0)


def _write_recursive(f: TextIO, data: dict | list | set | object, level: int = 0) -> None:
    if isinstance(data, dict) and level == 0:
        _write_toplevel_dict(f, data)
    else:
        _write_not_toplevel_dict(f, data, level)


def _write_toplevel_dict(f: TextIO, data: dict) -> None:
    for key, vals in data.items():
        f.write(f"KEY: {key}\n")
        if isinstance(vals, dict):
            _write_values_is_dict(f, vals)
        elif isinstance(vals, (list, set)):
            _write_values_is_collection(f, vals)
        else:
            f.write(f"VAL: {vals}\n\n")


def _write_values_is_dict(f: TextIO, data: dict) -> None:
    for key, vals in data.items():
        if isinstance(vals, (list, set, dict)):
            f.write(f"\t{key:<60}:\n")
            _write_recursive(f, vals, level=2)
        else:
            f.write(f"\t{key:<60}: {vals}\n")
    f.write("\n" + "-" * 180 + "\n\n")


def _write_values_is_collection(f: TextIO, vals: list | set) -> None:
    f.write(f"VALUES ({len(vals)}):\n")
    f.writelines(f"\t{i}\t|\t{v}\n" for i, v in enumerate(vals, 1))
    f.write("\n")


def _write_not_toplevel_dict(f: TextIO, data: dict | list | set | object, level: int) -> None:
    indent = "\t" * level
    if isinstance(data, dict):
        _write_nested_dict(f, data, level)
    elif isinstance(data, (list, set)):
        _write_nested_collection(f, data, level)
    else:
        f.write(f"{indent}{data}\n")


def _write_nested_dict(f: TextIO, data: dict, level: int) -> None:
    indent = "\t" * level
    for key, vals in data.items():
        if isinstance(vals, (list, set, dict)):
            f.write(f"{indent}{key}:\n")
            _write_recursive(f, vals, level + 1)
        else:
            f.write(f"{indent}{key:<60}: {vals}\n")


def _write_nested_collection(f: TextIO, data: list | set, level: int) -> None:
    indent = "\t" * level
    for i, item in enumerate(data, 1):
        if isinstance(item, (list, set, dict)):
            f.write(f"{indent}{i}:\n")
            _write_recursive(f, item, level + 1)
        else:
            f.write(f"{indent}{i}\t|\t{item}\n")


@dataclass(slots=True)
class ReportWriter:
    """A class to handle reporting and writing output to files, including text, JSON, and HTML formats."""

    ext: str
    output_dir: Path

    def write_reports(self, data_reports: Iterator[tuple[str, dict]]) -> None:
        """Write reports to the specified output directories."""
        for subdir, reports in data_reports:
            for prefix, data in reports.items():
                self.write(prefix, data, subdir)

    def write(self, prefix: str, data: dict, subdir: str) -> None:
        """Write the report to a file in the configured format (TXT, JSON, or HTML)."""
        filename = f"{prefix}.{self.ext}" if len(data) else f"(EMPTY) {prefix}.{self.ext}"
        output_dir = self.output_dir / subdir if subdir else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        logger.info("Writing %s as %s", prefix, self.ext)
        _write(path, data)
