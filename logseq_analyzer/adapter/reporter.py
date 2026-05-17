"""Reporting module for writing output to files, including HTML reports."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from collections.abc import Sized
    from pathlib import Path

logger = logging.getLogger(__name__)


def _write(path: Path, data: Sized) -> None:
    """Write the data to a plain text file with the given prefix and count."""
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{path.name}\n")
        f.write(f"COUNT: {len(data)}\n")
        _write_recursive(f, data, level=0)


def _write_recursive(f: TextIO, data: object, level: int = 0) -> None:
    indent = "\t" * level
    if isinstance(data, dict):
        for key, vals in data.items():
            if level == 0:
                f.write("-" * 180 + "\n")
                f.write(f"KEY: {key}\n")
                _write_toplevel(f, vals)
            elif isinstance(vals, (dict, list, set, tuple)):
                f.write(f"{indent}{key}:\n")
                _write_recursive(f, vals, level + 1)
            else:
                f.write(f"{indent}{key:<60}: {vals}\n")
    elif isinstance(data, (list, set, tuple)):
        for i, item in enumerate(data, 1):
            if isinstance(item, (dict, list, set, tuple)):
                f.write(f"{indent}{i}:\n")
                _write_recursive(f, item, level + 1)
            else:
                f.write(f"{indent}{i}\t|\t{item}\n")
    else:
        f.write(f"{indent}{data}\n")


def _write_toplevel(f: TextIO, vals: object) -> None:
    if isinstance(vals, dict):
        for k, v in vals.items():
            if isinstance(v, (dict, list, set, tuple)):
                f.write(f"\t{k:<60}:\n")
                _write_recursive(f, v, level=2)
            else:
                f.write(f"\t{k:<60}: {v}\n")
    elif isinstance(vals, (list, set, tuple)):
        f.write(f"\tVALUES ({len(vals)}):\n")
        f.writelines(f"\t{i}\t|\t{v}\n" for i, v in enumerate(vals, 1))
    else:
        f.write(f"VAL: {vals}\n")


@dataclass(slots=True)
class ReportWriter:
    """A class to handle reporting and writing output to files, including text, JSON, and HTML formats."""

    ext: str
    output_dir: Path

    def write_report(self, data_report: tuple[str, list[tuple[str, Sized]]]) -> None:
        """Write reports to the specified output directories."""
        subdir, reports = data_report
        logger.info("Processing reports for subdir: %s", subdir)
        for prefix, data in reports:
            filename = f"{prefix}.{self.ext}" if len(data) else f"(EMPTY) {prefix}.{self.ext}"
            output_dir = self.output_dir / subdir if subdir else self.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / filename
            logger.info("\tWriting %s as %s", prefix, self.ext)
            _write(path, data)
