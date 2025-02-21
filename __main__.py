import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Pattern, Generator, Set, Tuple
from urllib.parse import unquote

from __init__ import init_logging, init_output_directory
from compile_re import compile_regex_patterns
from reporting import write_output
import built_in_logseq


def process_key_name(key: str, parent: str) -> str:
    '''
    Process the key name by removing the parent name and formatting it.

    For 'journals' parent, it formats the key as 'day-month-year dayOfWeek'.
    For other parents, it unquotes URL-encoded characters and replaces '___' with '/'.

    Args:
        key (str): The key name (filename stem).
        parent (str): The parent directory name.

    Returns:
        str: Processed key name.
    '''
    if key.endswith('/'):
        key = key[:-1]

    if parent == 'journals':
        try:
            date_object = datetime.strptime(key, '%Y_%m_%d')
            day_of_week = date_object.strftime('%A')
            return f'{key.replace('_', '-').lower()} {day_of_week}'.lower() # Ensure final output is lowercase
        except ValueError:
            logging.warning(f'Could not parse journal key as date: {key}. Returning original key.')
            return key.replace('_', '-').lower() # Still process and lowercase even if parsing fails
    else:
        return unquote(key).replace('___', '/').lower()


def extract_file_metadata(file_path: Path) -> Dict[str, Any]:
    '''
    Extract metadata from a file.

    Metadata includes: id, name, name_secondary, file paths, dates (creation, modification),
    time since creation, and size.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Dict[str, Any]: A dictionary with file metadata.
    '''
    stat = file_path.stat()
    parent = file_path.parent.name
    original_name = file_path.stem
    name = process_key_name(file_path.stem, parent)
    suffix = file_path.suffix.lower() if file_path.suffix else None
    
    try:
        date_created = datetime.fromtimestamp(stat.st_birthtime)
    except AttributeError:
        date_created = datetime.fromtimestamp(stat.st_ctime)
        logging.warning(f'File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.')

    date_modified = datetime.fromtimestamp(stat.st_mtime)
    
    metadata = {
        'id': name[:2].lower() if len(name) > 1 else f'!{name[0].lower()}',
        'name': name,
        'name_secondary': f'{original_name} {parent} + {suffix}'.lower(),
        'file_path': str(file_path),
        'file_path_parent_name': parent.lower(),
        'file_path_name': name.lower(),
        'file_path_suffix': suffix.lower() if suffix else None,
        'file_path_parts': file_path.parts,
        'date_created': date_created,
        'date_modified': date_modified,
        'time_unmodified': date_modified - date_created,
        'size': stat.st_size
    }
    return metadata


def read_file_content(file_path: Path) -> Optional[str]:
    '''
    Read the text content of a file using UTF-8 encoding.

    Args:
        file_path (Path): The path to the file.

    Returns:
        Optional[str]: The file content as a string if successful; otherwise, None.
    '''
    try:
        return file_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logging.error(f'File not found: {file_path}') # More specific logging for file not found
        return None
    except Exception as e:
        logging.exception('Failed to read file %s: %s', file_path, e)
        return None


def iter_files(directory: Path, target_dirs: Optional[Set[str]] = None) -> Generator[Path, None, None]:
    '''
    Recursively iterate over files in the given directory.

    If target_dirs is provided, only yield files that reside within directories
    whose names are in the target_dirs set.

    Args:
        directory (Path): The root directory to search.
        target_dirs (Optional[Set[str]]): Set of allowed parent directory names.

    Yields:
        Path: File paths that match the criteria.
    '''
    if not directory.is_dir():
        logging.error(f'Directory not found: {directory}')
        return  # Stop iteration if directory doesn't exist
    
    for path in directory.rglob('*'):
        if path.is_file():
            if target_dirs:
                if path.parent.name in target_dirs:
                    yield path
                else:
                    logging.debug('Skipping file %s outside target directories', path)
            else:
                yield path


def process_single_file(file_path: Path, patterns: Dict[str, Pattern]) -> Tuple[Dict[str, Any], Optional[str]]:
    '''
    Process a single file: extract metadata, read content, and compute content-based metrics.

    Metrics computed are character count and bullet count using provided regex patterns.

    Args:
        file_path (Path): The file path to process.
        patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.

    Returns:
        Tuple[Dict[str, Any], Optional[str]]: A tuple containing metadata dictionary and file content (or None if reading failed).
    '''
    metadata = extract_file_metadata(file_path)
    content = read_file_content(file_path)
    
    if content:
        metadata['char_count'] = len(content)
        bullet_count = len(patterns['bullet'].findall(content))
        metadata['bullet_count'] = bullet_count
        metadata['bullet_density'] = metadata['char_count'] // bullet_count if bullet_count > 0 else 0
    else:
        metadata['char_count'] = 0
        metadata['bullet_count'] = 0
        metadata['bullet_density'] = 0
    return metadata, content


def process_content_data(content: Dict[str, str], patterns: Dict[str, Pattern], props) -> Dict[str, Any]:
    content_data = defaultdict(lambda: defaultdict(int))
    alphanum_dict = defaultdict(set)
    unique_linked_references = set()
    for name, text in content.items():
        content_data[name]['page_references'] = []
        content_data[name]['tags'] = []
        content_data[name]['tagged_backlinks'] = []
        content_data[name]['properties_page_builtin'] = []
        content_data[name]['properties_page_user'] = []
        content_data[name]['properties_block_builtin'] = []
        content_data[name]['properties_block_user'] = []
        content_data[name]['assets'] = []
        content_data[name]['draws'] = []
        content_data[name]['namespace_root'] = ''
        content_data[name]['namespace_parent'] = ''
        content_data[name]['namespace_level'] = -1
        content_data[name]['external_links_internet'] = []
        content_data[name]['external_links_alias'] = []
        content_data[name]['embedded_links_internet'] = []
        content_data[name]['embedded_links_asset'] = []
        if text:
            # Page references
            page_references = [page_ref.lower() for page_ref in patterns['page_reference'].findall(text)]
            if page_references:
                content_data[name]['page_references'] = page_references
                unique_linked_references.update(page_references)

            # Tags
            tags = [tag.lower() for tag in patterns['tag'].findall(text)]
            if tags:
                content_data[name]['tags'] = tags
                unique_linked_references.update(tags)
            tagged_backlinks = [tag.lower() for tag in patterns['tagged_backlink'].findall(text)]
            if tagged_backlinks:
                content_data[name]['tagged_backlinks'] = tagged_backlinks
                unique_linked_references.update(tagged_backlinks)

            # Properties
            heading_match = re.search(r'^\s*#+\s', text, re.MULTILINE)
            bullet_match = re.search(r'^\s*-\s', text, re.MULTILINE)
            if heading_match:
                page_text = text[: heading_match.start()]
                block_text = text[heading_match.start() :]
            elif bullet_match:
                page_text = text[: bullet_match.start()]
                block_text = text[bullet_match.start() :]
            else:
                page_text = text
                block_text = ''
            page_properties = [prop.lower() for prop in patterns['property'].findall(page_text)]
            if page_properties:
                properties_page_builtin = [prop for prop in page_properties if prop in props]
                if properties_page_builtin:
                    content_data[name]['properties_page_builtin'] = properties_page_builtin
                properties_page_user = [prop for prop in page_properties if prop not in props]
                if properties_page_user:
                    content_data[name]['properties_page_user'] = properties_page_user
                unique_linked_references.update(page_properties)
            block_properties = [prop.lower() for prop in patterns['property'].findall(block_text)]
            if block_properties:
                properties_block_builtin = [prop for prop in block_properties if prop in props]
                if properties_block_builtin:
                    content_data[name]['properties_block_builtin'] = properties_block_builtin
                properties_block_user = [prop for prop in block_properties if prop not in props]
                if properties_block_user:
                    content_data[name]['properties_block_user'] = properties_block_user
                unique_linked_references.update(block_properties)

            # Assets (general)
            assets = [asset.lower() for asset in patterns['asset'].findall(text)]
            if assets:
                content_data[name]['assets'] = assets
                
            # Draws (Excalidraw)
            draws = [draw.lower() for draw in patterns['draw'].findall(text)]
            if draws:
                content_data[name]['draws'] = draws
            
            # Namespace
            if '/' in name:
                namespace_parts = name.split('/')
                namespace_level = len(namespace_parts)
                namespace_root = namespace_parts[0]
                namespace_parent = '/'.join(namespace_parts[:-1])
                content_data[name]['namespace_root'] = namespace_root
                content_data[name]['namespace_parent'] = namespace_parent
                content_data[name]['namespace_level'] = namespace_level
                unique_linked_references.add(namespace_root)
                unique_linked_references.add(name)

            # External links
            external_links = [link.lower() for link in patterns['external_link'].findall(text)]
            if external_links:
                external_links_internet = [link.lower() for link in patterns['external_link_internet'].findall(text)]
                if external_links_internet:
                    content_data[name]['external_links_internet'] = external_links_internet
                external_links_alias = [link.lower() for link in patterns['external_link_alias'].findall(text)]
                if external_links_alias:
                    content_data[name]['external_links_alias'] = external_links_alias

            # Embedded links
            embedded_links = [link.lower() for link in patterns['embedded_link'].findall(text)]
            if embedded_links:
                embedded_links_internet = [link.lower() for link in patterns['embedded_link_internet'].findall(text)]
                if embedded_links_internet:
                    content_data[name]['embedded_links_internet'] = embedded_links_internet
                embedded_links_asset = [link.lower() for link in patterns['embedded_link_asset'].findall(text)]
                if embedded_links_asset:
                    content_data[name]['embedded_links_asset'] = embedded_links_asset

    # Create alphanum dictionary
    for linked_reference in unique_linked_references:
        if linked_reference:
            first_char = linked_reference[:2] if len(linked_reference) > 1 else f'!{linked_reference[0]}'
            alphanum_dict[first_char].add(linked_reference)
            
    alphanum_dict = dict(sorted(alphanum_dict.items()))
    return content_data, alphanum_dict


def process_summary_data(graph_meta_data: Dict[str, Any], graph_content_data: Dict[str, str], alphanum_dict: Dict[str, Set], target_dirs_dict: Dict[str, str]) -> Dict[str, Any]:
    '''
    Process summary data.
    '''
    graph_summary_data = defaultdict(lambda: defaultdict(int))
    for name, meta_data in graph_meta_data.items():
        graph_summary_data[name]['has_content'] = False
        graph_summary_data[name]['has_links'] = False
        graph_summary_data[name]['has_external_links'] = False
        graph_summary_data[name]['has_embedded_links'] = False
        graph_summary_data[name]['is_markdown'] = False
        graph_summary_data[name]['is_asset'] = False
        graph_summary_data[name]['is_draw'] = False
        graph_summary_data[name]['is_journal'] = False
        graph_summary_data[name]['is_page'] = False
        graph_summary_data[name]['is_whiteboard'] = False
        graph_summary_data[name]['is_other'] = False
        graph_summary_data[name]['is_backlinked'] = False
        graph_summary_data[name]['is_orphan_true'] = False
        graph_summary_data[name]['is_orphan_graph'] = False
        graph_summary_data[name]['is_node_root'] = False
        graph_summary_data[name]['is_node_leaf'] = False
        graph_summary_data[name]['is_node_branch'] = False
        
        if name in graph_content_data:
            graph_summary_data[name]['has_content'] = True
            if graph_content_data[name]['page_references']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['tags']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['tagged_backlinks']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['properties_page_builtin']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['properties_page_user']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['properties_block_builtin']:
                graph_summary_data[name]['has_links'] = True
            elif graph_content_data[name]['properties_block_user']:
                graph_summary_data[name]['has_links'] = True
            
            if graph_content_data[name]['external_links_internet']:
                graph_summary_data[name]['has_external_links'] = True
            elif graph_content_data[name]['external_links_alias']:
                graph_summary_data[name]['has_external_links'] = True
            
            if graph_content_data[name]['embedded_links_internet']:
                graph_summary_data[name]['has_embedded_links'] = True
            elif graph_content_data[name]['embedded_links_asset']:
                graph_summary_data[name]['has_embedded_links'] = True
        
        id_key = meta_data['id']
        if id_key in alphanum_dict:
            for page_ref in alphanum_dict[id_key]:
                if name == page_ref or str(name + '/') in page_ref:  # Capture root namespaces
                    graph_summary_data[name]['is_backlinked'] = True
                    break
            
        file_path_suffix = meta_data['file_path_suffix']
        file_path_parent_name = meta_data['file_path_parent_name']
        file_path_parts = meta_data['file_path_parts']
        
        if file_path_suffix == '.md':
            graph_summary_data[name]['is_markdown'] = True
            
        if graph_summary_data[name]['is_markdown']:
            if graph_summary_data[name]['has_content']:
                if graph_summary_data[name]['is_backlinked']:
                    if graph_summary_data[name]['has_links']:
                        graph_summary_data[name]['is_node_branch'] = True
                    else:
                        graph_summary_data[name]['is_node_leaf'] = True
                else:
                    if graph_summary_data[name]['has_links']:
                        graph_summary_data[name]['is_node_root'] = True
                    else:
                        graph_summary_data[name]['is_orphan_graph'] = True
            else:
                if graph_summary_data[name]['is_backlinked']:
                    graph_summary_data[name]['is_node_leaf'] = True
                else:
                    graph_summary_data[name]['is_orphan_true'] = True

        if file_path_parent_name == target_dirs_dict['assets_path']:
            graph_summary_data[name]['is_asset'] = True
        elif 'assets' in file_path_parts:
            graph_summary_data[name]['is_asset'] = True
            logging.info('Nested asset file found in: %s', file_path_parts)
        elif file_path_parent_name == target_dirs_dict['draws_path']:
            graph_summary_data[name]['is_draw'] = True
        elif file_path_parent_name == target_dirs_dict['journals_path']:
            graph_summary_data[name]['is_journal'] = True
        elif file_path_parent_name == target_dirs_dict['pages_path']:
            graph_summary_data[name]['is_page'] = True
        elif file_path_parent_name == target_dirs_dict['whiteboards_path']:
            graph_summary_data[name]['is_whiteboard'] = True
        else:
            graph_summary_data[name]['is_other'] = True
    return graph_summary_data


def extract_summary_subset(graph_summary_data: Dict[str, Any], **criteria: Any) -> Dict[str, Any]:
    '''
    Extract a subset of the summary data based on multiple criteria (key-value pairs).

    Args:
        graph_summary_data (Dict[str, Any]): The complete summary data.
        **criteria: Keyword arguments specifying the criteria for subset extraction.

    Returns:
        Dict[str, Any]: A subset of the summary data matching the criteria.
    '''
    return {
        k: v for k, v in graph_summary_data.items()
        if all(v.get(key) == expected for key, expected in criteria.items())
    }


def main():    
    '''
    Main function to run the Logseq analyzer.

    Initializes logging, output directory, regex patterns, processes files,
    generates summary data, and writes output to files.
    '''
    log_file = Path('___logseq_analyzer___.log')
    init_logging(log_file)
    logging.info('Starting Logseq Analyzer.')
    
    output_dir = Path('output')
    init_output_directory(output_dir)
    
    patterns = compile_regex_patterns()

    logseq_graph_folder = Path('C:/Logseq')  # folder = input('Enter folder path: ') or 'C:/Logseq'
    
    target_dirs = built_in_logseq.TARGET_DIRS
    target_dirs_dict = {
        'assets_path': built_in_logseq.ASSETS_PATH_NAME,
        'draws_path': built_in_logseq.DRAWS_PATH_NAME,
        'journals_path': built_in_logseq.JOURNALS_PATH_NAME,
        'pages_path': built_in_logseq.PAGES_PATH_NAME,
        'whiteboards_path': built_in_logseq.WHITEBOARDS_PATH_NAME
    }
    
    # Outputs
    meta_alphanum_dictionary    = {}
    meta_graph_content          = {} 
    graph_meta_data             = {}
    graph_content_data          = {}
    graph_summary_data          = {}
    
    for file_path in iter_files(logseq_graph_folder, target_dirs):
        meta_data, graph_content = process_single_file(file_path, patterns)
        name = meta_data['name']
        if name in graph_meta_data:
            name = meta_data['name_secondary']
        graph_meta_data[name] = meta_data
        meta_graph_content[name] = graph_content
    
    built_in_properties = built_in_logseq.BUILT_IN_PROPERTIES
    graph_content_data, meta_alphanum_dictionary = process_content_data(meta_graph_content, patterns, built_in_properties)
    graph_summary_data = process_summary_data(graph_meta_data, graph_content_data, meta_alphanum_dictionary, target_dirs_dict)
    
    write_output(output_dir, '___meta_alphanum_dictionary', meta_alphanum_dictionary)
    write_output(output_dir, '___meta_graph_content', meta_graph_content)
    write_output(output_dir, '__graph_content_data', graph_content_data)
    write_output(output_dir, '__graph_meta_data', graph_meta_data)
    write_output(output_dir, '__graph_summary_data', graph_summary_data)
    
    summary_categories = {
        "_summary_has_content":         {"has_content": True},
        "_summary_has_links":           {"has_links": True},
        "_summary_has_external_links":  {"has_external_links": True},
        "_summary_has_embedded_links":  {"has_embedded_links": True},
        "_summary_is_markdown":         {"is_markdown": True},
        "_summary_is_asset":            {"is_asset": True},
        "_summary_is_draw":             {"is_draw": True},
        "_summary_is_journal":          {"is_journal": True},
        "_summary_is_page":             {"is_page": True},
        "_summary_is_whiteboard":       {"is_whiteboard": True},
        "_summary_is_other":            {"is_other": True},
        "_summary_is_backlinked":       {"is_backlinked": True},
        "_summary_is_orphan_true":      {"is_orphan_true": True},
        "_summary_is_orphan_graph":     {"is_orphan_graph": True},
        "_summary_is_node_root":        {"is_node_root": True},
        "_summary_is_node_leaf":        {"is_node_leaf": True},
        "_summary_is_node_branch":      {"is_node_branch": True},
    }

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = summary_subset
        write_output(output_dir, output_name, summary_subset)
    
    # Asset Handling
    summary_is_asset = summary_data_subsets["_summary_is_asset"]
    not_referenced_assets_keys = list(summary_is_asset.keys())
    for name, content_data in graph_content_data.items():
        if not content_data['assets']: 
            continue
        for non_asset in not_referenced_assets_keys:
            non_asset_secondary = graph_meta_data[non_asset]['name']
            for asset_mention in content_data['assets']:
                if non_asset in asset_mention or non_asset_secondary in asset_mention:
                    graph_summary_data[non_asset]['is_backlinked'] = True
                    break
    summary_is_asset_backlinked = extract_summary_subset(graph_summary_data, is_asset=True, is_backlinked=True)
    summary_is_asset_not_backlinked = extract_summary_subset(graph_summary_data, is_asset=True, is_backlinked=False)
    write_output(output_dir, '_summary_is_asset_backlinked', summary_is_asset_backlinked)
    write_output(output_dir, '_summary_is_asset_not_backlinked', summary_is_asset_not_backlinked)
    
    # Draws Handling
    summary_is_draw = summary_data_subsets["_summary_is_draw"]
    for name, content_data in graph_content_data.items():
        if not content_data['draws']:
            continue
        for draw in content_data['draws']:
            if draw in summary_is_draw:
                summary_is_draw[draw]['is_backlinked'] = True    
    write_output(output_dir, '_summary_is_draw', summary_is_draw) # overwrites
    
    # TODO Whiteboards Handling (content)
    # summary_is_whiteboard = summary_data_subsets["_summary_is_whiteboard"]
    # write_output(output_dir, '_summary_is_whiteboard', summary_is_whiteboard)
    
    
if __name__ == '__main__':
    print('Start: Logseq Analyzer')
    main()
    print('End: Logseq Analyzer')
    