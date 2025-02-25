# reporting.py
import logging
from pathlib import Path
from typing import Any


def write_output(
    output_dir: Path,
    filename_prefix: str,
    items: Any,
    type_output: str = "",
    dont_sort: bool = False,
) -> None:
    """
    Args:
        filename_prefix:    Prefix for the output file.
        items:              Dictionary or list of items to write to the output file.
    """
    logging.info(f"Writing {filename_prefix}...")

    instance_type = str(type(items))
    count = len(items) if isinstance(items, (list, set)) else len(items.keys())
    filename_prefix = (
        f"{filename_prefix}.txt" if count else f"{filename_prefix}_EMPTY.txt"
    )

    if type_output:
        out_path = output_dir / type_output / filename_prefix

        if not Path(output_dir / type_output).exists():
            Path(output_dir / type_output).mkdir(parents=True, exist_ok=True)
    else:
        out_path = output_dir / filename_prefix

    with out_path.open("w", encoding="UTF-8") as f:
        f.write(f"{filename_prefix} | Items: {count} | Type: {instance_type}\n\n")

        if isinstance(items, dict):
            for key, values in items.items():
                f.write(f"Key: {key}\n")
                if isinstance(values, (list, set)):
                    f.write(f"Values ({len(values)}): {values}\n\n")
                elif isinstance(values, dict):
                    for k, v in values.items():
                        f.write(f"\t{k:<40}: {v}\n")
                    f.write("\n")
                else:
                    f.write(f"Value: {values}\n\n")
        else:
            if not dont_sort:
                items = sorted(items)
            for index, item in enumerate(items):
                f.write(f"{index:05d}\t-\t{item}\n")
