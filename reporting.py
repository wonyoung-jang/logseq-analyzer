# reporting.py
import logging
from pathlib import Path
from typing import Any

def write_output(output_dir: Path, filename_prefix: str, items: Any, type_output: str='', dont_sort: bool=False) -> None:
    '''
    Args:
        filename_prefix:    Prefix for the output file.
        items:              Dictionary or list of items to write to the output file.
    '''
    logging.info('Writing %s...', filename_prefix)
    
    count = len(items) if isinstance(items, list) else len(items.keys())
    instance_type = str(type(items))
    
    if type_output:
        if count:
            out_path = output_dir / type_output / f'{filename_prefix}.txt'
        else:
            out_path = output_dir / type_output / f'{filename_prefix}_EMPTY.txt'
    else:
        if count:
            out_path = output_dir / f'{filename_prefix}.txt'
        else:
            out_path = output_dir / f'{filename_prefix}_EMPTY.txt'

    with out_path.open('w', encoding='UTF-8') as f:
        f.write(f'{filename_prefix} | Items: {count} | Type: {instance_type}\n\n')

        if isinstance(items, dict):
            for key, values in items.items():
                f.write(f'Key: {key}\n')
                if isinstance(values, list):
                    f.write(f'Values ({len(values)}): {values}\n\n')
                elif isinstance(values, dict):
                    for k, v in values.items():
                        f.write(f'\t{k:<40}: {v}\n')
                    f.write('\n')
                else:
                    f.write(f'Value: {values}\n\n')
        else:
            if not dont_sort:
                items = sorted(items)
            for index, item in enumerate(items):
                f.write(f'{index:05d}\t-\t{item}\n')
