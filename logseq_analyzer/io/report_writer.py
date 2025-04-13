"""
Reporting module for writing output to files.
"""

from pathlib import Path
from typing import Any, TextIO
import json
import logging

from ..config.analyzer_config import LogseqAnalyzerConfig
from .path_validator import LogseqAnalyzerPathValidator

ANALYZER_CONFIG = LogseqAnalyzerConfig()
JSON_FORMAT = ANALYZER_CONFIG.config["CONST"]["REPORT_FORMAT_JSON"]
TXT_FORMAT = ANALYZER_CONFIG.config["CONST"]["REPORT_FORMAT_TXT"]


class ReportWriter:
    """
    A class to handle reporting and writing output to files.
    """

    def __init__(self, filename_prefix: str, items: Any, type_output: str = "") -> None:
        """
        Initialize the ReportWriter class.
        """
        self._paths = LogseqAnalyzerPathValidator()
        self.filename_prefix = filename_prefix
        self.items = items
        self.type_output = type_output
        self.output_format = ANALYZER_CONFIG.config["ANALYZER"]["REPORT_FORMAT"]

    @staticmethod
    def write_recursive(f: TextIO, data: Any, indent_level: int = 0) -> None:
        """
        Recursive function to write nested data structures to a file.

        Args:
            f (TextIO): The file object to write to.
            data (Any): The data to write.
            indent_level (int, optional): The current indentation level. Defaults to 0.
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

    def write(self) -> None:
        """
        Write the output to a file using a recursive helper to handle nested structures.
        """
        logging.info("Writing %s as %s", self.filename_prefix, self.output_format)
        count = len(self.items)
        filename = (
            f"{self.filename_prefix}{self.output_format}"
            if count
            else f"___EMPTY___{self.filename_prefix}{self.output_format}"
        )

        if self.type_output:
            parent = self._paths.dir_output.path / self.type_output
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
            out_path = Path(parent) / filename
        else:
            out_path = self._paths.dir_output.path / filename

        # For JSON format, re-open and dump JSON if that is the requested format
        if self.output_format == JSON_FORMAT:
            try:
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(self.items, f, indent=4)
            except TypeError:
                logging.error("Failed to write JSON for %s.", self.filename_prefix)
                if out_path.exists():
                    out_path.unlink()
                filename = f"{self.filename_prefix}{TXT_FORMAT}"
                if self.type_output:
                    out_path = Path(parent) / filename
                with out_path.open("w", encoding="utf-8") as f:
                    f.write(f"{filename} | Items: {count}\n\n")
                    ReportWriter.write_recursive(f, self.items)
        elif self.output_format == TXT_FORMAT:
            with out_path.open("w", encoding="utf-8") as f:
                f.write(f"{filename} | Items: {count}\n\n")
                ReportWriter.write_recursive(f, self.items)
        else:
            logging.error(
                "Unsupported output format: %s. Defaulting to text.",
                self.output_format,
            )
            with out_path.open("w", encoding="utf-8") as f:
                f.write(f"{filename} | Items: {count}\n\n")
                ReportWriter.write_recursive(f, self.items)
