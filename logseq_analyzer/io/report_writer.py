"""Reporting module for writing output to files, including HTML reports."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TextIO

from logseq_analyzer.utils.enums import Format

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

logger = logging.getLogger(__name__)


class TextWriter:
    """A class to handle recursive writing of nested data structures to text files."""

    @staticmethod
    def write(outputpath: Path, prefix: str, count: int | None, filename: str, data: Any) -> None:
        """Write the data to a plain text file with the given prefix and count."""
        with outputpath.open("w", encoding="utf-8") as f:
            if count is not None:
                f.write(f"{prefix} | {filename}\n")
                f.write(f"COUNT: {count}\n")
                f.write(f"TYPE: {data.__class__.__qualname__}\n\n")
            TextWriter.write_recursive(f, data)

    @staticmethod
    def write_recursive(f: TextIO, data: Any, indent_level: int = 0) -> None:
        """Recursive function to write nested data structures to plain text files."""
        indent = "\t" * indent_level
        if isinstance(data, dict) and indent_level == 0:
            TextWriter.write_toplevel_dict(f, data, indent, indent_level)
        else:
            TextWriter.write_not_toplevel_dict(f, data, indent, indent_level)

    @staticmethod
    def write_toplevel_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """Write the top-level dictionary to a file."""
        for key, values in data.items():
            f.write(f"{indent}KEY: {key}\n")
            if isinstance(values, dict):
                TextWriter.write_values_is_dict(f, values, indent, indent_level)
            elif isinstance(values, (list, set)):
                TextWriter.write_values_is_collection(f, values, indent)
            else:
                f.write(f"{indent}VAL: {values}\n\n")

    @staticmethod
    def write_values_is_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """Write values of a dictionary to a file with indentation."""
        for key, values in data.items():
            if not isinstance(values, (list, set, dict)):
                f.write(f"{indent}\t{key:<60}: {values}\n")
            else:
                f.write(f"{indent}\t{key:<60}:\n")
                TextWriter.write_recursive(f, values, indent_level + 2)
        f.write("\n" + "-" * 180 + "\n\n")

    @staticmethod
    def write_values_is_collection(f: TextIO, values: Any, indent: str) -> None:
        """Write values of a collection to a file with indentation."""
        f.write(f"{indent}VALUES ({len(values)}):\n")
        f.writelines(f"{indent}\t{index}\t|\t{value}\n" for index, value in enumerate(values, 1))
        f.write("\n")

    @staticmethod
    def write_not_toplevel_dict(f: TextIO, data: Any, indent: str, indent_level: int = 0) -> None:
        """Write the non-top-level dictionary to a file."""
        if isinstance(data, dict):
            TextWriter.write_nested_dict(f, data, indent, indent_level)
        elif isinstance(data, (list, set)):
            TextWriter.write_nested_collection(f, data, indent, indent_level)
        else:
            f.write(f"{indent}{data}\n")

    @staticmethod
    def write_nested_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """Write nested dictionaries to a file with indentation."""
        for key, values in data.items():
            if isinstance(values, (list, set, dict)):
                f.write(f"{indent}{key}:\n")
                TextWriter.write_recursive(f, values, indent_level + 1)
            else:
                f.write(f"{indent}{key:<60}: {values}\n")

    @staticmethod
    def write_nested_collection(f: TextIO, data: Any, indent: str, indent_level: int = 0) -> None:
        """Write collections (lists, sets) to a file with indentation."""
        for index, item in enumerate(data, 1):
            if isinstance(item, (list, set, dict)):
                f.write(f"{indent}{index}:\n")
                TextWriter.write_recursive(f, item, indent_level + 1)
            else:
                f.write(f"{indent}{index}\t|\t{item}\n")


WRITE_METHOD_MAP: dict[str, Callable] = {
    Format.TXT: TextWriter.write,
    Format.MD: TextWriter.write,
}


@dataclass(slots=True)
class ReportWriter:
    """A class to handle reporting and writing output to files, including text, JSON, and HTML formats."""

    ext: str
    output_dir: Path

    def write(self, prefix: str, data: Any, subdir: str) -> None:
        """Write the report to a file in the configured format (TXT, JSON, or HTML)."""
        count = len(data) if hasattr(data, "__len__") else None
        filename = f"{prefix}.{self.ext}" if count else f"(EMPTY) {prefix}.{self.ext}"
        outputpath = self.get_output_path(filename, subdir)
        logger.info("Writing %s as %s", prefix, self.ext)
        write_method = WRITE_METHOD_MAP.get(self.ext, TextWriter.write)
        write_method(outputpath, prefix, count, filename, data)

    def get_output_path(self, filename: str, subdir: str) -> Path:
        """Get the output path for the report file.

        Args:
            filename (str): The name of the file to be created.
            subdir (str): The subdirectory where the file should be created.

        Returns:
            Path: The output path for the report file.

        """
        output_dir = self.output_dir / subdir if subdir else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename

    def write_reports(self, data_reports: Iterator[tuple[str, dict]]) -> None:
        """Write reports to the specified output directories."""
        for subdir, reports in data_reports:
            for prefix, data in reports.items():
                self.write(prefix, data, subdir)
        logger.debug("write_reports")
