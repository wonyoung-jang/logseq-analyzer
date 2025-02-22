import argparse
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Pattern, Generator, Set, Tuple, List
from urllib.parse import unquote

from __init__ import init_logging, init_output_directory
from compile_re import compile_regex_patterns
from reporting import write_output
import logseq_config


def process_journal_key(key: str) -> str:
    '''
    Process the journal key by converting it to a page title format.
    
    Args:
        key (str): The journal key (filename stem).

    Returns:
        str: Processed journal key as a page title.
    '''
    page_title_format = getattr(logseq_config, 'JOURNAL_PAGE_TITLE_FORMAT', 'MMM do, yyyy')
    file_name_format = getattr(logseq_config, 'JOURNAL_FILE_NAME_FORMAT', 'yyyy_MM_dd')
    py_file_name_format = convert_format(file_name_format)
    py_page_title_format = convert_format(page_title_format)
    
    try: 
        date_object = datetime.strptime(key, py_file_name_format)
        page_title = date_object.strftime(py_page_title_format).lower()
        return page_title
    except ValueError:
        logging.warning(f'Could not parse journal key as date: {key}. Returning original key.')
        return key


def convert_format(cljs_format: str) -> str:
    '''
    Convert a Clojure-style date format to a Python-style date format.
    
    Args:
        cljs_format (str): Clojure-style date format.
        
    Returns:
        str: Python-style date format.
    '''
    token_map = getattr(logseq_config, 'TOKEN_MAP', {})
    token_pattern = re.compile('|'.join(re.escape(k) for k in sorted(token_map, key=len, reverse=True)))
    def replace_token(match):
        token = match.group(0)
        return token_map.get(token, token)
    py_format = token_pattern.sub(replace_token, cljs_format)
    return py_format


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
        return process_journal_key(key)
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
    name = process_key_name(file_path.stem, parent)
    suffix = file_path.suffix.lower() if file_path.suffix else None
    now = datetime.now().replace(microsecond=0)
    
    try:
        date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
    except AttributeError:
        date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
        logging.warning(f'File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.')

    date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)
    
    time_existed = now - date_created
    time_unmodified = now - date_modified
    
    metadata = {
        'id': name[:2].lower() if len(name) > 1 else f'!{name[0].lower()}',
        'name': name,
        'name_secondary': f'{name} {parent} + {suffix}'.lower(),
        'file_path': str(file_path),
        'file_path_parent_name': parent.lower(),
        'file_path_name': name.lower(),
        'file_path_suffix': suffix.lower() if suffix else None,
        'file_path_parts': file_path.parts,
        'date_created': date_created,
        'date_modified': date_modified,
        'time_existed': time_existed,
        'time_unmodified': time_unmodified,
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
        logging.warning(f'File not found: {file_path}') # More specific logging for file not found
        return None
    except Exception as e:
        logging.warning(f'Failed to read file {file_path}: {e}')
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
        return 
    
    for path in directory.rglob('*'):
        if path.is_file():
            if target_dirs:
                if path.parent.name in target_dirs:
                    yield path
                else:
                    logging.info(f'Skipping file {path} outside target directories')
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


def process_content_data(content: Dict[str, str], patterns: Dict[str, Pattern], props: Set[str]) -> Tuple[Dict[str, Any], Dict[str, Set[str]], List[str]]:
    '''
    Process file content to extract links, tags, properties, and namespace information.

    Args:
        content (Dict[str, str]): Dictionary of file names to content.
        patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.
        props (Set[str]): Set of built-in properties.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Set[str]]]:
            - content_data: Dictionary of content-based metrics for each file.
            - alphanum_dict: Dictionary for quick lookup of linked references.
            - dangling_links: List of sorted dangling links (linked, but no file).
    '''
    content_data = defaultdict(lambda: defaultdict(list))
    alphanum_dict = defaultdict(set)
    unique_linked_references = set()
    
    for name, text in content.items():
        if not text:
            logging.debug(f'Skipping content processing for "{name}" due to empty content.')
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
            content_data[name]['external_links'] = []
            content_data[name]['external_links_internet'] = []
            content_data[name]['external_links_alias'] = []
            content_data[name]['embedded_links'] = []
            content_data[name]['embedded_links_internet'] = []
            content_data[name]['embedded_links_asset'] = []
            continue
        
        # Page references
        page_references = [page_ref.lower() for page_ref in patterns['page_reference'].findall(text)]
        tags = [tag.lower() for tag in patterns['tag'].findall(text)]
        tagged_backlinks = [tag.lower() for tag in patterns['tagged_backlink'].findall(text)]
        assets = [asset.lower() for asset in patterns['asset'].findall(text)]
        draws = [draw.lower() for draw in patterns['draw'].findall(text)]
        external_links = [link.lower() for link in patterns['external_link'].findall(text)]
        embedded_links = [link.lower() for link in patterns['embedded_link'].findall(text)]
        page_properties, block_properties = extract_page_block_properties(text, patterns)
        
        content_data[name]['page_references'] = page_references
        content_data[name]['tags'] = tags
        content_data[name]['tagged_backlinks'] = tagged_backlinks
        content_data[name]['assets'] = assets
        content_data[name]['draws'] = draws
        
        (   content_data[name]["properties_page_builtin"], 
            content_data[name]["properties_page_user"]
        ) = split_builtin_user_properties(page_properties, props)
        
        (   content_data[name]["properties_block_builtin"], 
            content_data[name]["properties_block_user"]
        ) = split_builtin_user_properties(block_properties, props)

        # Namespace
        if '/' in name:
            namespace_parts = name.split('/')
            namespace_level = len(namespace_parts)
            namespace_root = namespace_parts[0]
            namespace_parent = '/'.join(namespace_parts[:-1])
            
            content_data[name]['namespace_root'] = namespace_root
            content_data[name]['namespace_parent'] = namespace_parent
            content_data[name]['namespace_level'] = namespace_level
            
            unique_linked_references.update([namespace_root, name])
            
        unique_linked_references.update(page_references, tags, tagged_backlinks, page_properties, block_properties)

        # External links
        if external_links:
            content_data[name]['external_links'] = external_links
            external_links_internet = [link.lower() for link in patterns['external_link_internet'].findall(text)]
            if external_links_internet:
                content_data[name]['external_links_internet'] = external_links_internet
            external_links_alias = [link.lower() for link in patterns['external_link_alias'].findall(text)]
            if external_links_alias:
                content_data[name]['external_links_alias'] = external_links_alias

        # Embedded links
        if embedded_links:
            content_data[name]['embedded_links'] = embedded_links
            embedded_links_internet = [link.lower() for link in patterns['embedded_link_internet'].findall(text)]
            if embedded_links_internet:
                content_data[name]['embedded_links_internet'] = embedded_links_internet
            embedded_links_asset = [link.lower() for link in patterns['embedded_link_asset'].findall(text)]
            if embedded_links_asset:
                content_data[name]['embedded_links_asset'] = embedded_links_asset

    # Create alphanum dictionary
    for linked_reference in unique_linked_references:
        if linked_reference:
            first_char_id = linked_reference[:2] if len(linked_reference) > 1 else f'!{linked_reference[0]}'
            alphanum_dict[first_char_id].add(linked_reference)
        else: 
            logging.info(f'Empty linked reference: {linked_reference}')
    
    # Check for dangling links (linked, but no file)
    all_filenames = list(content.keys())
    alphanum_filenames = defaultdict(set)
    for filename in all_filenames:
        if filename:
            first_char_id = filename[:2] if len(filename) > 1 else f'!{filename[0]}'
            alphanum_filenames[first_char_id].add(filename)
        else:
            logging.info(f'Empty filename: {filename}')
    alphanum_dict = dict(sorted(alphanum_dict.items()))
    alphanum_filenames = dict(sorted(alphanum_filenames.items()))
    dangling_links = set()
    for id, reference in alphanum_dict.items():
        if id not in alphanum_filenames:
            dangling_links.update(reference)
        else:
            for ref in reference:
                if ref not in alphanum_filenames[id]:
                    dangling_links.add(ref)
    dangling_links = sorted(dangling_links)
            
    return content_data, alphanum_dict, dangling_links


def extract_page_block_properties(text: str, patterns: Dict[str, Pattern]) -> Tuple[list, list]:
    '''Helper function to extract page and block properties from text.'''
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
    block_properties = [prop.lower() for prop in patterns['property'].findall(block_text)]
    return page_properties, block_properties


def split_builtin_user_properties(properties: list, built_in_props: Set[str]) -> Tuple[list, list]:
    '''Helper function to split properties into built-in and user-defined.'''
    builtin_props = [prop for prop in properties if prop in built_in_props]
    user_props = [prop for prop in properties if prop not in built_in_props]
    return builtin_props, user_props


def process_summary_data(graph_meta_data: Dict[str, Any], graph_content_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]]) -> Dict[str, Any]:
    '''
    Process summary data for each file based on metadata and content analysis.

    Categorizes files and determines node types (root, leaf, branch, orphan).

    Args:
        graph_meta_data (Dict[str, Any]): Metadata for each file.
        graph_content_data (Dict[str, Any]): Content-based data for each file.
        alphanum_dict (Dict[str, Set[str]]): Dictionary for quick lookup of linked references.

    Returns:
        Dict[str, Any]: Summary data for each file.
    '''
    graph_summary_data = defaultdict(lambda: defaultdict(bool))
    
    for name, meta_data in graph_meta_data.items():
        content_info = graph_content_data.get(name, {})
        has_content = bool(content_info)
        has_links = any(content_info.get(key) for key in [
            'page_references', 
            'tags', 
            'tagged_backlinks',
            'properties_page_builtin',
            'properties_page_user',
            'properties_block_builtin',
            'properties_block_user'
        ])
        has_external_links = any(content_info.get(key) for key in [
            'external_links', 
            'external_links_internet', 
            'external_links_alias'
        ])
        has_embedded_links = any(content_info.get(key) for key in [
            'embedded_links', 
            'embedded_links_internet', 
            'embedded_links_asset'
        ])
            
        file_path_suffix = meta_data['file_path_suffix']
        file_path_parent_name = meta_data['file_path_parent_name']
        file_path_parts = meta_data['file_path_parts']
        
        is_markdown = file_path_suffix == '.md'
        is_asset = file_path_parent_name == 'assets' or 'assets' in file_path_parts
        is_draw = file_path_parent_name == 'draws'
        is_journal = file_path_parent_name == 'journals'
        is_page = file_path_parent_name == 'pages'
        is_whiteboard = file_path_parent_name == 'whiteboards'
        is_other = not any([is_markdown, is_asset, is_draw, is_journal, is_page, is_whiteboard])
            
        is_backlinked = check_is_backlinked(name, meta_data, alphanum_dict)
        if is_markdown:
            is_orphan_true, is_orphan_graph, is_node_root, is_node_leaf, is_node_branch = determine_node_type(
                has_content, is_backlinked, has_links
            )
        else:
            is_orphan_true = is_orphan_graph = is_node_root = is_node_leaf = is_node_branch = False
            
        graph_summary_data[name]['has_content'] = has_content
        graph_summary_data[name]['has_links'] = has_links
        graph_summary_data[name]['has_external_links'] = has_external_links
        graph_summary_data[name]['has_embedded_links'] = has_embedded_links
        graph_summary_data[name]['is_markdown'] = is_markdown
        graph_summary_data[name]['is_asset'] = is_asset
        graph_summary_data[name]['is_draw'] = is_draw
        graph_summary_data[name]['is_journal'] = is_journal
        graph_summary_data[name]['is_page'] = is_page
        graph_summary_data[name]['is_whiteboard'] = is_whiteboard
        graph_summary_data[name]['is_other'] = is_other
        graph_summary_data[name]['is_backlinked'] = is_backlinked
        graph_summary_data[name]['is_orphan_true'] = is_orphan_true
        graph_summary_data[name]['is_orphan_graph'] = is_orphan_graph
        graph_summary_data[name]['is_node_root'] = is_node_root
        graph_summary_data[name]['is_node_leaf'] = is_node_leaf
        graph_summary_data[name]['is_node_branch'] = is_node_branch
        
    return graph_summary_data


def check_is_backlinked(name: str, meta_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]]) -> bool:
    '''Helper function to check if a file is backlinked.'''
    id_key = meta_data['id']
    if id_key in alphanum_dict:
        for page_ref in alphanum_dict[id_key]:
            if name == page_ref or str(name + '/') in page_ref:
                return True
    return False


def determine_node_type(has_content: bool, is_backlinked: bool, has_links: bool) -> Tuple[bool, bool, bool, bool, bool]:
    '''Helper function to determine node type based on summary data.'''
    is_orphan_true = False
    is_orphan_graph = False
    is_node_root = False
    is_node_leaf = False
    is_node_branch = False

    if has_content:
        if is_backlinked:
            if has_links:
                is_node_branch = True
            else:
                is_node_leaf = True
        else:
            if has_links:
                is_node_root = True
            else:
                is_orphan_graph = True # Orphan within the graph (has content but no backlinks or graph links)
    else:
        if not is_backlinked:
            is_orphan_true = True # Truly orphan (no content, no backlinks)
        else:
            is_node_leaf = True # Treat as leaf if backlinked but no content

    return is_orphan_true, is_orphan_graph, is_node_root, is_node_leaf, is_node_branch


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
    parser = argparse.ArgumentParser(description='Logseq Analyzer')
    parser.add_argument('-g', '--graph-folder', type=str, help='Path to the Logseq graph folder')
    parser.add_argument('-o', '--output-folder', type=str, help='Path to the output folder')
    parser.add_argument('-l', '--log-file', type=str, help='Path to the log file')
    parser.add_argument('-t', '--target-dirs', type=str, nargs='+', help='Target directories to analyze')
    args = parser.parse_args()
    
    logseq_graph_folder = Path(args.graph_folder) if args.graph_folder else Path('C:/Logseq')
    output_dir = Path(args.output_folder) if args.output_folder else Path('output')
    log_file = Path(args.log_file) if args.log_file else Path('___logseq_analyzer___.log')
    target_dirs = set(args.target_dirs) if args.target_dirs else logseq_config.TARGET_DIRS
    
    init_logging(log_file)
    logging.info('Starting Logseq Analyzer.')
    init_output_directory(output_dir)
    patterns = compile_regex_patterns()
    target_dirs = logseq_config.TARGET_DIRS
    
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
    
    built_in_properties = logseq_config.BUILT_IN_PROPERTIES
    graph_content_data, meta_alphanum_dictionary, meta_dangling_links = process_content_data(meta_graph_content, patterns, built_in_properties)
    graph_summary_data = process_summary_data(graph_meta_data, graph_content_data, meta_alphanum_dictionary)
    
    write_output(output_dir, '___meta_alphanum_dictionary', meta_alphanum_dictionary)
    write_output(output_dir, '___meta_dangling_links', meta_dangling_links)
    write_output(output_dir, '___meta_graph_content', meta_graph_content)
    write_output(output_dir, '__graph_content_data', graph_content_data)
    write_output(output_dir, '__graph_meta_data', graph_meta_data)
    write_output(output_dir, '__graph_summary_data', graph_summary_data)
    
    summary_categories = {
        '_summary_has_content':         {'has_content': True},
        '_summary_has_links':           {'has_links': True},
        '_summary_has_external_links':  {'has_external_links': True},
        '_summary_has_embedded_links':  {'has_embedded_links': True},
        '_summary_is_markdown':         {'is_markdown': True},
        '_summary_is_asset':            {'is_asset': True},
        '_summary_is_draw':             {'is_draw': True},
        '_summary_is_journal':          {'is_journal': True},
        '_summary_is_page':             {'is_page': True},
        '_summary_is_whiteboard':       {'is_whiteboard': True},
        '_summary_is_other':            {'is_other': True},
        '_summary_is_backlinked':       {'is_backlinked': True},
        '_summary_is_orphan_true':      {'is_orphan_true': True},
        '_summary_is_orphan_graph':     {'is_orphan_graph': True},
        '_summary_is_node_root':        {'is_node_root': True},
        '_summary_is_node_leaf':        {'is_node_leaf': True},
        '_summary_is_node_branch':      {'is_node_branch': True},
    }

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = summary_subset
        write_output(output_dir, output_name, summary_subset)
    
    # Asset Handling
    summary_is_asset = summary_data_subsets['_summary_is_asset']
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
    summary_is_draw = summary_data_subsets['_summary_is_draw']
    for name, content_data in graph_content_data.items():
        if not content_data['draws']:
            continue
        for draw in content_data['draws']:
            if draw in summary_is_draw:
                summary_is_draw[draw]['is_backlinked'] = True    
    write_output(output_dir, '_summary_is_draw', summary_is_draw) # overwrites
    
    # TODO Whiteboards Handling (content)
    # summary_is_whiteboard = summary_data_subsets['_summary_is_whiteboard']
    # write_output(output_dir, '_summary_is_whiteboard', summary_is_whiteboard)
    
    logging.info('Logseq Analyzer completed.')
    
    
if __name__ == '__main__':
    main()
    # TODO Implement a GUI
    
    # TODO Implement configurable inputs
    
    # TODO Implement custom journal date formats
    
    # TODO Implement configurable outputs
    # TODO Implement saving settings
    # TODO Implement saving logs
    # TODO Implement saving outputs
    # TODO Implement more global output measurements
