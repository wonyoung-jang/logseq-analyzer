"""
Reporting module for writing output to files, including HTML reports.
"""

import json
import logging
from pathlib import Path
from typing import Any, TextIO

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.enums import Format
from .filesystem import OutputDirectory


class ReportWriter:
    """A class to handle reporting and writing output to files, including text, JSON, and HTML formats."""

    __slots__ = ("prefix", "data", "subdir")

    lac = LogseqAnalyzerConfig()
    od = OutputDirectory()

    def __init__(self, prefix: str, data: Any, subdir: str = "") -> None:
        """
        Initialize the ReportWriter class.

        Args:
            prefix (str): The prefix for the output filename.
            data (Any): The data to be written to the file.
            subdir (str): The type of output to be put into subfolder (e.g., "namespaces", "journals").
        """
        self.prefix = prefix
        self.data = data
        self.subdir = subdir

    def __repr__(self) -> str:
        """String representation of the ReportWriter object."""
        return f"{self.__class__.__qualname__}(prefix={self.prefix}, items=data, subdir={self.subdir})"

    def __str__(self) -> str:
        """String representation of the ReportWriter object."""
        return f"{self.__class__.__qualname__}: {self.prefix}, Items: data, Output Subdir: {self.subdir}"

    def write(self) -> None:
        """
        Write the report to a file in the configured format (TXT, JSON, or HTML).
        """
        ext = ReportWriter.lac.config["ANALYZER"]["REPORT_FORMAT"]
        prefix = self.prefix
        logging.info("Writing %s as %s", prefix, ext)
        data = self.data
        count = len(data) if hasattr(data, "__len__") else None
        filename = f"{prefix}{ext}" if count else f"___EMPTY___{prefix}{ext}"
        outputpath = self.get_output_path(filename)

        # JSON format
        if ext == Format.JSON.value:
            try:
                with outputpath.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except TypeError:
                logging.error("Failed to write JSON for %s, falling back to TXT.", prefix)

        # HTML format
        if ext == Format.HTML.value:
            with outputpath.open("w", encoding="utf-8") as f:
                f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
                f.write(f'  <meta charset="utf-8">\n  <title>{prefix}</title>\n')
                f.write(
                    """  <style> body { font-family: sans-serif; margin: 2em; } dl { margin-left: 1em; }
                    ol { margin-left: 1em; } span { display: inline-block; } </style>\n"""
                )
                f.write("</head>\n<body>\n")
                f.write(f"<h1>{prefix}</h1>\n")
                if count is not None:
                    f.write(f"<p>Count: {count}</p>\n")
                ReportWriter.write_html_recursive(f, data)
                f.write("</body>\n</html>\n")

        # TXT and MD format and fallback
        if ext in (Format.TXT.value, Format.MD.value):
            with outputpath.open("w", encoding="utf-8") as f:
                if count is not None:
                    f.write(f"{filename}\n")
                    f.write(f"Count: {count}\n")
                    f.write(f"Type: {type(data)}\n\n")
                ReportWriter.write_recursive(f, data)

        if ext not in (Format.TXT.value, Format.MD.value, Format.JSON.value, Format.HTML.value):
            logging.error("Unsupported output format: %s. Defaulted to text.", ext)

    def get_output_path(self, filename: str) -> Path:
        """
        Get the output path for the report file.

        Args:
            filename (str): The name of the file to be created.

        Returns:
            Path: The output path for the report file.
        """
        output_dir = ReportWriter.od.path
        if self.subdir:
            output_dir = output_dir / self.subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename

    @staticmethod
    def write_nested_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """
        Write nested dictionaries to a file with indentation.
        """
        for key, values in data.items():
            if isinstance(values, (list, set, dict)):
                f.write(f"{indent}{key}:\n")
                ReportWriter.write_recursive(f, values, indent_level + 1)
            else:
                f.write(f"{indent}{key:<60}: {values}\n")

    @staticmethod
    def write_nested_collection(f: TextIO, data: Any, indent: str, indent_level: int = 0) -> None:
        """
        Write collections (lists, sets) to a file with indentation.
        """
        for index, item in enumerate(data, 1):
            if isinstance(item, (list, set, dict)):
                f.write(f"{indent}{index}:\n")
                ReportWriter.write_recursive(f, item, indent_level + 1)
            else:
                f.write(f"{indent}{index}\t|\t{item}\n")

    @staticmethod
    def write_nested_other(f: TextIO, data: Any, indent: str) -> None:
        """
        Write other types of data to a file with indentation.
        """
        f.write(f"{indent}{data}\n")

    @staticmethod
    def write_values_is_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """
        Write values of a dictionary to a file with indentation.
        """
        for key, values in data.items():
            if not isinstance(values, (list, set, dict)):
                f.write(f"{indent}\t{key:<60}: {values}\n")
            else:
                f.write(f"{indent}\t{key:<60}:\n")
                ReportWriter.write_recursive(f, values, indent_level + 2)
        f.write("\n" + "-" * 180 + "\n")
        f.write("\n")

    @staticmethod
    def write_values_is_collection(f: TextIO, values: Any, indent: str) -> None:
        """
        Write values of a collection to a file with indentation.
        """
        f.write(f"{indent}Values ({len(values)}):\n")
        for index, value in enumerate(values, 1):
            f.write(f"{indent}\t{index}\t|\t{value}\n")
        f.write("\n")

    @staticmethod
    def write_values_is_other(f: TextIO, values: Any, indent: str) -> None:
        """
        Write values to a file with indentation.
        """
        f.write(f"{indent}Value: {values}\n\n")

    @staticmethod
    def write_toplevel_dict_key(f: TextIO, key: str, indent: str) -> None:
        """
        Write the top-level dictionary key to a file.
        """
        f.write(f"{indent}Key: {key}\n")

    @staticmethod
    def get_indent(indent_level: int) -> str:
        """
        Get the indentation string for a given level.
        """
        return "\t" * indent_level

    @staticmethod
    def check_is_toplevel_dict(data: Any, indent_level: int) -> bool:
        """
        Check if the data is a top-level dictionary.
        """
        return isinstance(data, dict) and indent_level == 0

    @staticmethod
    def write_toplevel_dict(f: TextIO, data: dict, indent: str, indent_level: int = 0) -> None:
        """
        Write the top-level dictionary to a file.
        """
        for key, values in data.items():
            ReportWriter.write_toplevel_dict_key(f, key, indent)
            if isinstance(values, dict):
                ReportWriter.write_values_is_dict(f, values, indent, indent_level)
            elif isinstance(values, (list, set)):
                ReportWriter.write_values_is_collection(f, values, indent)
            else:
                ReportWriter.write_values_is_other(f, values, indent)

    @staticmethod
    def write_not_toplevel_dict(f: TextIO, data: Any, indent: str, indent_level: int = 0) -> None:
        """
        Write the non-top-level dictionary to a file.
        """
        if isinstance(data, dict):
            ReportWriter.write_nested_dict(f, data, indent, indent_level)
        elif isinstance(data, (list, set)):
            ReportWriter.write_nested_collection(f, data, indent, indent_level)
        else:
            ReportWriter.write_nested_other(f, data, indent)

    @staticmethod
    def write_recursive(f: TextIO, data: Any, indent_level: int = 0) -> None:
        """
        Recursive function to write nested data structures to plain text files.
        """
        indent = ReportWriter.get_indent(indent_level)
        if ReportWriter.check_is_toplevel_dict(data, indent_level):
            ReportWriter.write_toplevel_dict(f, data, indent, indent_level)
        else:
            ReportWriter.write_not_toplevel_dict(f, data, indent, indent_level)

    @staticmethod
    def write_html_recursive(f: TextIO, data: Any) -> None:
        """
        Recursive helper to write nested data structures into HTML format.
        Uses <dl> for dicts, <ol> for lists/sets, and <span> for simple values.
        """
        if isinstance(data, dict):
            f.write("<dl>\n")
            for key, value in data.items():
                f.write(f"  <dt><strong>{key}</strong></dt>\n")
                f.write("  <dd>")
                if isinstance(value, (dict, list, set)):
                    f.write("\n")
                    ReportWriter.write_html_recursive(f, value)
                    f.write("  ")
                else:
                    f.write(f"<span>{value}</span>")
                f.write("</dd>\n")
            f.write("</dl>\n")

        elif isinstance(data, (list, set)):
            f.write("<ol>\n")
            for item in data:
                f.write("  <li>")
                if isinstance(item, (dict, list, set)):
                    f.write("\n")
                    ReportWriter.write_html_recursive(f, item)
                    f.write("  ")
                else:
                    f.write(f"<span>{item}</span>")
                f.write("</li>\n")
            f.write("</ol>\n")

        else:
            f.write(f"<span>{data}</span>\n")
