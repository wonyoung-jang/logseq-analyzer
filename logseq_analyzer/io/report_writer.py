"""Reporting module for writing output to files, including HTML reports."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, TextIO

from ..utils.enums import Format

if TYPE_CHECKING:
    from pathlib import Path

    from ..config.arguments import Args
    from ..io.filesystem import LogseqAnalyzerDirs

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
        f_write = f.write
        write_dict = TextWriter.write_values_is_dict
        write_collection = TextWriter.write_values_is_collection
        for key, values in data.items():
            f_write(f"{indent}KEY: {key}\n")
            if isinstance(values, dict):
                write_dict(f, values, indent, indent_level)
            elif isinstance(values, (list, set)):
                write_collection(f, values, indent)
            else:
                f_write(f"{indent}VAL: {values}\n\n")

    @staticmethod
    def write_values_is_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """Write values of a dictionary to a file with indentation."""
        f_write = f.write
        write_recursive = TextWriter.write_recursive
        for key, values in data.items():
            if not isinstance(values, (list, set, dict)):
                f_write(f"{indent}\t{key:<60}: {values}\n")
            else:
                f_write(f"{indent}\t{key:<60}:\n")
                write_recursive(f, values, indent_level + 2)
        f_write("\n" + "-" * 180 + "\n\n")

    @staticmethod
    def write_values_is_collection(f: TextIO, values: Any, indent: str) -> None:
        """Write values of a collection to a file with indentation."""
        f_write = f.write
        f_write(f"{indent}VALUES ({len(values)}):\n")
        for index, value in enumerate(values, 1):
            f_write(f"{indent}\t{index}\t|\t{value}\n")
        f_write("\n")

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
        f_write = f.write
        write_recursive = TextWriter.write_recursive
        for key, values in data.items():
            if isinstance(values, (list, set, dict)):
                f_write(f"{indent}{key}:\n")
                write_recursive(f, values, indent_level + 1)
            else:
                f_write(f"{indent}{key:<60}: {values}\n")

    @staticmethod
    def write_nested_collection(f: TextIO, data: Any, indent: str, indent_level: int = 0) -> None:
        """Write collections (lists, sets) to a file with indentation."""
        f_write = f.write
        write_recursive = TextWriter.write_recursive
        for index, item in enumerate(data, 1):
            if isinstance(item, (list, set, dict)):
                f_write(f"{indent}{index}:\n")
                write_recursive(f, item, indent_level + 1)
            else:
                f_write(f"{indent}{index}\t|\t{item}\n")


class HTMLWriter:
    """A class to handle writing HTML content."""

    @staticmethod
    def write(outputpath: Path, prefix: str, count: int | None, filename: str, data: Any) -> None:
        """Write the data to an HTML file with the given prefix and count.

        Args:
            outputpath (Path): The path where the HTML file will be written.
            prefix (str): The prefix for the HTML title and header.
            count (int | None): The count of items, if applicable.
            filename (str): The name of the file being processed.
            data (Any): The data to be written to the HTML file.

        """
        with outputpath.open("w", encoding="utf-8") as f:
            f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
            f.write(f'<meta charset="utf-8">\n<title>{prefix}</title>\n')
            f.write(
                """<style>
                body { font-family: sans-serif; margin: 2em; }
                dl { margin-left: 1em; }
                ol { margin-left: 1em; }
                span { display: inline-block; }
                </style>\n"""
            )
            f.write("</head>\n<body>\n")
            f.write(f"<h1>{prefix}</h1>\n")
            if count is not None:
                f.write(f"<p>{filename}</p>\n")
                f.write(f"<p>COUNT: {count}</p>\n")
                f.write(f"<p>TYPE: {data.__class__.__qualname__}</p>\n")
            HTMLWriter.write_html_recursive(f, data)
            f.write("</body>\n</html>\n")

    @staticmethod
    def write_html_recursive(f: TextIO, data: Any) -> None:
        """Recursive helper to write nested data structures into HTML format.

        Uses <dl> for dicts, <ol> for lists/sets, and <span> for simple values.
        """
        if isinstance(data, dict):
            HTMLWriter.write_dict_html(f, data)
        elif isinstance(data, (list, set)):
            HTMLWriter.write_collection_html(f, data)
        else:
            f.write(f"<span>{data}</span>\n")

    @staticmethod
    def write_collection_html(f: TextIO, data: Any) -> None:
        """Write collections (lists, sets) to HTML format.

        Uses <ol> for ordered lists and <li> for items.
        """
        f.write("<ol>\n")
        for item in data:
            f.write("  <li>")
            if isinstance(item, (dict, list, set)):
                f.write("\n")
                HTMLWriter.write_html_recursive(f, item)
                f.write("  ")
            else:
                f.write(f"<span>{item}</span>")
            f.write("</li>\n")
        f.write("</ol>\n")

    @staticmethod
    def write_dict_html(f: TextIO, data: dict) -> None:
        """Write a dictionary to HTML format.

        Uses <dl> for definition lists, <dt> for terms, and <dd> for definitions.
        """
        f.write("<dl>\n")
        for key, value in data.items():
            f.write(f"  <dt><strong>{key}</strong></dt>\n")
            f.write("  <dd>")
            if isinstance(value, (dict, list, set)):
                f.write("\n")
                HTMLWriter.write_html_recursive(f, value)
                f.write("  ")
            else:
                f.write(f"<span>{value}</span>")
            f.write("</dd>\n")
        f.write("</dl>\n")


class JSONWriter:
    """A class to handle writing JSON content."""

    @staticmethod
    def write(outputpath: Path, prefix: str, count: int | None, filename: str, data: Any) -> None:
        """Write the data to a JSON file."""
        try:
            with outputpath.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("Successfully wrote JSON for %s items in filename: %s", count, filename)
        except TypeError:
            logger.exception("Failed to write JSON for %s, falling back to TXT.", prefix)


@dataclass(slots=True)
class Writers:
    """A dataclass to hold different types of writers for reporting."""

    text: TextWriter = field(default_factory=TextWriter)
    html: HTMLWriter = field(default_factory=HTMLWriter)
    json: JSONWriter = field(default_factory=JSONWriter)


@dataclass(slots=True)
class ReportWriter:
    """A class to handle reporting and writing output to files, including text, JSON, and HTML formats."""

    prefix: str
    data: Any
    subdir: str
    writer: Writers = field(default_factory=Writers)

    ext: ClassVar[str]
    output_dir: ClassVar[Path]

    @classmethod
    def configure(cls, args: Args, analyzer_dirs: LogseqAnalyzerDirs) -> None:
        """Configure the ReportWriter class with necessary settings.

        Args:
            args (Args): The command-line arguments.
            analyzer_dirs (LogseqAnalyzerDirs): The directories used by the Logseq Analyzer.

        """
        cls.ext = args.report_format
        cls.output_dir = analyzer_dirs.output_dir.path

    def write(self) -> None:
        """Write the report to a file in the configured format (TXT, JSON, or HTML)."""
        _data = self.data
        _prefix = self.prefix
        _ext = self.ext
        _writer = self.writer
        count = len(_data) if hasattr(_data, "__len__") else None
        filename = f"{_prefix}.{_ext}" if count else f"(EMPTY) {_prefix}.{_ext}"
        outputpath = self.get_output_path(filename)
        logger.info("Writing %s as %s", _prefix, _ext)
        write_method = {
            Format.TXT: _writer.text.write,
            Format.MD: _writer.text.write,
            Format.JSON: _writer.json.write,
            Format.HTML: _writer.html.write,
        }.get(_ext, _writer.text.write)

        write_method(outputpath, _prefix, count, filename, _data)

    def get_output_path(self, filename: str) -> Path:
        """Get the output path for the report file.

        Args:
            filename (str): The name of the file to be created.

        Returns:
            Path: The output path for the report file.

        """
        output_dir = self.output_dir / self.subdir if self.subdir else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename
