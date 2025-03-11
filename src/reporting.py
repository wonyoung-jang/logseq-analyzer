import logging
import csv
from pathlib import Path
from typing import Any, TextIO

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
    output_dir: Path,
    filename_prefix: str,
    items: Any,
    type_output: str = "",
) -> None:
    """
    Write the output to a file using a recursive helper to handle nested structures.

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
        write_recursive(f, items)


def write_csv_output(
    output_dir: Path,
    filename_prefix: str,
    items: Any,
    type_output: str = "",
) -> None:
    """
    Write the output to CSV file. For dictionaries, it flattens them to create CSV rows.
    For lists or sets, they are converted to comma-separated strings within a cell.

    Args:
        output_dir (Path): The output directory.
        filename_prefix (str): The prefix of the filename.
        items (Any): The data items to write to CSV. Assumed to be a dictionary
                     where keys are filenames and values are dictionaries of properties.
        type_output (str, optional):  The subdirectory for output. Defaults to "".
    """
    logging.info(f"Writing CSV output: {filename_prefix}...")

    count = len(items) if isinstance(items, (dict, list, set)) else 1
    filename = f"{filename_prefix}.csv" if count else f"{filename_prefix}_EMPTY.csv"

    if type_output:
        parent = output_dir / type_output
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        out_path = parent / filename
    else:
        out_path = output_dir / filename

    if not isinstance(items, dict): # Handle cases where 'items' is not a dictionary (e.g., list of strings)
        logging.warning(f"Data for CSV output '{filename_prefix}' is not a dictionary, attempting to write as list.")
        with out_path.open('w', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['value']) # Default header
            if isinstance(items, list) or isinstance(items, set):
                for item in items:
                    csv_writer.writerow([item])
            elif items: # For single values
                csv_writer.writerow([items])
        return


    # For dictionary data, assume keys of the dictionary are filenames,
    # and values are dictionaries of properties.
    with out_path.open('w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)

        if not items: # Handle empty dictionary
            csv_writer.writerow(['No data'])
            return

        # Extract headers from the first item's dictionary (assuming consistent structure)
        example_item_value = next(iter(items.values())) # Get the first value in the dict
        if isinstance(example_item_value, dict):
            headers = ['key'] + list(example_item_value.keys()) # Filename as first column
            csv_writer.writerow(headers)

            # Write data rows
            for filename_key, data_dict in items.items():
                row_data = [filename_key] # Start row with filename
                for header in headers[1:]: # Iterate through headers, skipping 'filename'
                    # Check attribute of data_dict
                    if not isinstance(data_dict, dict):
                        logging.warning(f"Data for key '{filename_key}' is not a dictionary, skipping.")
                        continue
                    value = data_dict.get(header, '')
                    if isinstance(value, (list, set)): # Convert lists/sets to comma-separated strings
                        value = ', '.join(map(str, value))
                    row_data.append(value)
                csv_writer.writerow(row_data)
        else: # If values are not dictionaries, write as filename and value columns
            logging.warning(f"Values in data for CSV '{filename_prefix}' are not dictionaries, writing as key-value pairs.")
            csv_writer.writerow(['key', 'value'])
            for filename_key, value in items.items():
                 csv_writer.writerow([filename_key, value])