"""
Reporting module for writing output to files, including HTML reports.
"""

from typing import Any, TextIO
import json
import logging

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.enums import Format
from .filesystem import OutputDirectory


class ReportWriter:
    """
    A class to handle reporting and writing output to files, including text, JSON, and HTML formats.
    """

    def __init__(self, filename_prefix: str, items: Any, type_output: str = "") -> None:
        """
        Initialize the ReportWriter class.

        Args:
            filename_prefix (str): The prefix for the output filename.
            items (Any): The data to be written to the file.
            type_output (str): The type of output to be put into subfolder (e.g., "namespaces", "journals").
        """
        self.filename_prefix = filename_prefix
        self.items = items
        self.type_output = type_output

    def __repr__(self) -> str:
        """String representation of the ReportWriter object."""
        return f"ReportWriter(filename_prefix={self.filename_prefix}, items=data, type_output={self.type_output})"

    def __str__(self) -> str:
        """String representation of the ReportWriter object."""
        return f"ReportWriter: {self.filename_prefix}, Items: data, Type Output: {self.type_output}"

    def write(self) -> None:
        """
        Write the report to a file in the configured format (TXT, JSON, or HTML).
        """
        ac = LogseqAnalyzerConfig()
        output_format = ac.config["ANALYZER"]["REPORT_FORMAT"]
        logging.info("Writing %s as %s", self.filename_prefix, output_format)

        count = len(self.items) if hasattr(self.items, "__len__") else None
        print(f"Name: {self.filename_prefix}, Items: {count}")
        ext = output_format
        filename = f"{self.filename_prefix}{ext}" if count else f"___EMPTY___{self.filename_prefix}{ext}"

        # Determine output path
        out_directory = OutputDirectory()
        output_dir = out_directory.path
        if self.type_output:
            output_dir = output_dir / self.type_output
            output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / filename

        # Handle JSON format
        if output_format == Format.JSON.value:
            try:
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(self.items, f, indent=4)
                return
            except TypeError:
                logging.error("Failed to write JSON for %s, falling back to TXT.", self.filename_prefix)

        # Handle HTML format
        if output_format == Format.HTML.value:
            with out_path.open("w", encoding="utf-8") as f:
                # HTML header
                f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n')
                f.write(f'  <meta charset="utf-8">\n  <title>{self.filename_prefix}</title>\n')
                f.write(
                    "  <style> body { font-family: sans-serif; margin: 2em; } dl { margin-left: 1em; } ol { margin-left: 1em; } span { display: inline-block; } </style>\n"
                )
                f.write("</head>\n<body>\n")
                f.write(f"<h1>{self.filename_prefix}</h1>\n")
                if count is not None:
                    f.write(f"<p>Items: {count}</p>\n")
                # Recursive content
                ReportWriter.write_html_recursive(f, self.items)
                f.write("</body>\n</html>\n")
            return

        # Handle TXT format and fallback
        with out_path.open("w", encoding="utf-8") as f:
            if count is not None:
                f.write(f"{filename} | Items: {count}\n\n")
            ReportWriter.write_recursive(f, self.items)

        if output_format not in (Format.TXT.value, Format.JSON.value, Format.HTML.value):
            logging.warning("Unsupported output format: %s. Defaulted to text.", output_format)

    @staticmethod
    def write_recursive(f: TextIO, data: Any, indent_level: int = 0) -> None:
        """
        Recursive function to write nested data structures to plain text files.
        """
        indent = "\t" * indent_level
        if indent_level == 0 and isinstance(data, dict):
            for key, values in data.items():
                f.write(f"{indent}Key: {key}\n")
                if isinstance(values, (list, set)):
                    f.write(f"{indent}Values ({len(values)}):\n")
                    for index, value in enumerate(values, start=1):
                        f.write(f"{indent}\t{index}\t|\t{value}\n")
                    f.write("\n")
                    continue

                if isinstance(values, dict):
                    for k, v in values.items():
                        if not isinstance(v, (list, set, dict)):
                            f.write(f"{indent}\t{k:<60}: {v}\n")
                            continue
                        f.write(f"{indent}\t{k:<60}:\n")
                        ReportWriter.write_recursive(f, v, indent_level + 2)
                    f.write("\n")
                    continue

                f.write(f"{indent}Value: {values}\n\n")
        else:
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (list, set, dict)):
                        f.write(f"{indent}{k}:\n")
                        ReportWriter.write_recursive(f, v, indent_level + 1)
                        continue
                    f.write(f"{indent}{k:<60}: {v}\n")
            elif isinstance(data, (list, set)):
                try:
                    for index, item in enumerate(sorted(data), start=1):
                        if isinstance(item, (list, set, dict)):
                            f.write(f"{indent}{index}:\n")
                            ReportWriter.write_recursive(f, item, indent_level + 1)
                            continue
                        f.write(f"{indent}{index}\t|\t{item}\n")
                except TypeError:
                    for index, item in enumerate(data, start=1):
                        f.write(f"{indent}{index}\t|\t{item}\n")
            else:
                f.write(f"{indent}{data}\n")

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
