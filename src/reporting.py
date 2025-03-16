import logging
from pathlib import Path
from typing import Any, TextIO

from src import config


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
                for index, value in enumerate(values):
                    f.write(f"{indent}\t{index}\t-\t{value}\n")
                f.write("\n")
            elif isinstance(values, dict):
                for k, v in values.items():
                    if not isinstance(v, (list, set, dict)):
                        f.write(f"{indent}\t{k:<60}: {v}\n")
                    else:
                        f.write(f"{indent}\t{k:<60}:\n")
                        write_recursive(f, v, indent_level + 2)
                f.write("\n")
            else:
                f.write(f"{indent}Value: {values}\n\n")
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (list, set, dict)):
                    f.write(f"{indent}{k}:\n")
                    write_recursive(f, v, indent_level + 1)
                else:
                    f.write(f"{indent}{k:<60}: {v}\n")
        elif isinstance(data, (list, set)):
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
        else:
            f.write(f"{indent}{data}\n")


def write_output(
    output_dir: str,
    filename_prefix: str,
    items: Any,
    type_output: str = "",
) -> None:
    """
    Write the output to a file using a recursive helper to handle nested structures.

    Args:
        output_dir (str): The output directory.
        filename_prefix (str): The prefix of the filename.
        items (Any): The items to write.
        type_output (str, optional): The type of output. Defaults to "".
    """
    logging.info(f"Writing {filename_prefix}...")

    count = len(items)
    filename = f"{filename_prefix}.txt" if count else f"{filename_prefix}_EMPTY.txt"
    output_dir = Path(output_dir)

    if type_output:
        parent = output_dir / type_output
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        out_path = parent / filename
    else:
        out_path = output_dir / filename

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"{filename} | Items: {count}\n\n")
        write_recursive(f, items)


def write_many_outputs(args, target=config.OUTPUT_DIR_TEST, **kwargs) -> None:
    """
    Write initial outputs for graph analysis to specified directories.

    Args:
        args (argparse.Namespace): The command line arguments.
        **kwargs: Additional keyword arguments for output data.
    """
    if kwargs:
        for name, items in kwargs.items():
            if name == "graph_content_bullets" and args.write_graph:
                write_output(config.DEFAULT_OUTPUT_DIR, name, items, target)
                continue
            write_output(config.DEFAULT_OUTPUT_DIR, name, items, target)
