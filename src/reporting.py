import logging
from pathlib import Path
from typing import Any


def write_output(
    output_dir: Path,
    filename_prefix: str,
    items: Any,
    type_output: str = "",
) -> None:
    """
    Write the output to a file.

    Args:
        output_dir (Path): The output directory.
        filename_prefix (str): The prefix of the filename.
        items (Any): The items to write.
        type_output (str, optional): The type of output. Defaults to "".
    """
    logging.info(f"Writing {filename_prefix}...")

    count = len(items)
    filename = f"{filename_prefix}.txt" if count else f"{filename_prefix}_EMPTY.txt"

    if type_output:
        parent = output_dir / type_output
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        out_path = parent / filename
    else:
        out_path = output_dir / filename

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"{filename} | Items: {count}\n\n")

        if isinstance(items, dict):
            for key, values in items.items():
                f.write(f"Key: {key}\n")
                if isinstance(values, (list, set)):
                    f.write(f"Values ({len(values)}):\n")
                    for index, value in enumerate(values):
                        f.write(f"\t{index:02d}\t-\t{value}\n")
                    f.write("\n")
                elif isinstance(values, dict):
                    for k, v in values.items():
                        f.write(f"\t{k:<60}: {v}\n")
                    f.write("\n")
                else:
                    f.write(f"Value: {values}\n\n")
        else:
            items = sorted(items)
            for index, item in enumerate(items):
                f.write(f"{index:02d}\t-\t{item}\n")
