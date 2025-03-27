"""
Reporting module for writing output to files.
"""

import json
import logging
from pathlib import Path
from typing import Any, TextIO

from .config_loader import get_config


CONFIG = get_config()


def write_output(
    output_dir: str,
    filename_prefix: str,
    items: Any,
    type_output="",
) -> None:
    """
    Write the output to a file using a recursive helper to handle nested structures.

    Args:
        output_dir (str): The output directory.
        filename_prefix (str): The prefix of the filename.
        items (Any): The items to write.
        type_output (str, optional): The type of output. Defaults to "".
    """
    json_format = CONFIG.get("CONSTANTS", "REPORT_FORMAT_JSON")
    txt_format = CONFIG.get("CONSTANTS", "REPORT_FORMAT_TXT")
    output_format = CONFIG.get("REPORTING", "REPORT_FORMAT")

    logging.info("Writing %s as %s", filename_prefix, output_format)
    count = len(items)
    filename = f"{filename_prefix}{output_format}" if count else f"{filename_prefix}_EMPTY{output_format}"
    output_dir = Path(output_dir)

    if type_output:
        parent = output_dir / type_output
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        out_path = Path(parent) / filename
    else:
        out_path = output_dir / filename

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"{filename} | Items: {count}\n\n")
        write_recursive(f, items)

    if output_format == json_format:
        try:
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(items, f, indent=4)
        except TypeError:
            logging.error("Failed to write JSON for %s.", filename_prefix)
            if out_path.exists():
                out_path.unlink()
            filename = f"{filename_prefix}{txt_format}"
            if type_output:
                out_path = Path(parent) / filename
            with out_path.open("w", encoding="utf-8") as f:
                f.write(f"{filename} | Items: {count}\n\n")
                write_recursive(f, items)
    elif output_format == txt_format:
        with out_path.open("w", encoding="utf-8") as f:
            f.write(f"{filename} | Items: {count}\n\n")
            write_recursive(f, items)
    else:
        logging.error("Unsupported output format: %s. Defaulting to text.", output_format)
        with out_path.open("w", encoding="utf-8") as f:
            f.write(f"{filename} | Items: {count}\n\n")
            write_recursive(f, items)


def write_recursive(f: TextIO, data: Any, indent_level: int = 0) -> None:
    """
    Recursive function to write nested data structures to a file.
    (Refactored - Branching reduced using type dispatch)
    """
    handler = _get_data_handler(data, indent_level)
    handler(f, data, indent_level)


def _get_data_handler(data: Any, indent_level: int):
    """Returns the appropriate handler function based on data type and indent level."""
    if indent_level == 0 and isinstance(data, dict):
        return _write_top_level_dict

    if isinstance(data, dict):
        return _write_dict

    if isinstance(data, (list, set)):
        return _write_list_or_set

    return _write_simple_value


def _get_value_handler(values: Any):
    """Returns the appropriate handler for values within a top-level dictionary."""
    if isinstance(values, (list, set)):
        return _write_list_set_value

    if isinstance(values, dict):
        return _write_dict_value

    return _write_simple_value_in_dict


def _write_top_level_dict(f: TextIO, data: dict, indent_level: int):
    """Handles writing a top-level dictionary (indent_level 0)."""
    indent = "\t" * indent_level
    for key, values in data.items():
        f.write(f"{indent}Key: {key}\n")
        value_handler = _get_value_handler(values)
        value_handler(f, values, indent_level)
        f.write("\n")


def _write_list_set_value(f: TextIO, values: list | set, indent_level: int):
    """Handles writing list or set values within a top-level dictionary."""
    indent = "\t" * indent_level
    f.write(f"{indent}Values ({len(values)}):\n")
    for index, value in enumerate(values):
        f.write(f"{indent}\t{index}\t-\t{value}\n")


def _write_dict_value(f: TextIO, values: dict, indent_level: int):
    """Handles writing dictionary values within a top-level dictionary."""
    indent = "\t" * indent_level
    for k, v in values.items():
        if not isinstance(v, (list, set, dict)):
            f.write(f"{indent}\t{k:<60}: {v}\n")
        else:
            f.write(f"{indent}\t{k:<60}:\n")
            write_recursive(f, v, indent_level + 2)


def _write_dict(f: TextIO, data: dict, indent_level: int):
    """Handles writing a dictionary (not top-level)."""
    indent = "\t" * indent_level
    for k, v in data.items():
        if isinstance(v, (list, set, dict)):
            f.write(f"{indent}{k}:\n")
            write_recursive(f, v, indent_level + 1)
        else:
            f.write(f"{indent}{k:<60}: {v}\n")


def _write_list_or_set(f: TextIO, data: list | set, indent_level: int):
    """Handles writing a list or set."""
    indent = "\t" * indent_level
    try:
        for index, item in enumerate(sorted(data)):
            if isinstance(item, (list, set, dict)):
                f.write(f"{indent}{index}:\n")
                write_recursive(f, item, indent_level + 1)
            else:
                f.write(f"{indent}{index}\t-\t{item}\n")
    except TypeError:
        for index, item in enumerate(data):
            f.write(f"{indent}{index}\t-\t{item}\n")


def _write_simple_value(f: TextIO, data: Any, indent_level: int):
    """Handles writing a simple value (not dict, list, or set)."""
    indent = "\t" * indent_level
    f.write(f"{indent}{data}\n")


def _write_simple_value_in_dict(f: TextIO, data: dict, indent_level: int):
    """Handles writing dictionary values within a top-level dictionary."""
    indent_level = 0
    indent = "\t" * indent_level
    f.write(f"{indent}Value: {data}\n")
