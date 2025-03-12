import logging
from collections import defaultdict
from typing import Any, Dict, List, Pattern, Set, Tuple

import src.config as config


def init_content_data() -> Dict[str, Any]:
    """
    Initialize an empty content data dictionary.


    Returns:
        Dict[str, Any]: An empty dictionary for content data.
    """
    return {
        "aliases": [],
        "namespace_root": "",
        "namespace_parent": "",
        "namespace_parts": {},
        "namespace_level": -1,
        "page_references": [],
        "tagged_backlinks": [],
        "tags": [],
        "properties_values": [],
        "properties_page_builtin": [],
        "properties_page_user": [],
        "properties_block_builtin": [],
        "properties_block_user": [],
        "assets": [],
        "draws": [],
        "external_links": [],
        "external_links_internet": [],
        "external_links_alias": [],
        "embedded_links": [],
        "embedded_links_internet": [],
        "embedded_links_asset": [],
        "blockquotes": [],
        "flashcards": [],
        "multiline_code_block": [],
        "calc_block": [],
        "multiline_code_lang": [],
        "reference": [],
        "block_reference": [],
        "embed": [],
        "page_embed": [],
        "block_embed": [],
        "namespace_queries": [],
        "clozes": [],
        "simple_queries": [],
        "query_functions": [],
        "advanced_commands": [],
    }


def process_content_data(
    content: Dict[str, str], patterns: Dict[str, Pattern], meta_primary_bullet: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Set[str]], List[str]]:
    """
    Process file content to extract links, tags, properties, and namespace information.

    Args:
        content (Dict[str, str]): Dictionary of file names to content.
        patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.
        meta_primary_bullet (Dict[str, Any]): Metadata for primary bullets.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Set[str]]]:
            - content_data: Dictionary of content-based metrics for each file.
            - alphanum_dict: Dictionary for quick lookup of linked references.
            - dangling_links: List of dangling links (linked, but no file).
    """
    content_data = {}
    unique_linked_references = set()
    unique_aliases = set()
    props = config.BUILT_IN_PROPERTIES

    # Process each file's content
    for name, text in content.items():
        # Initialize content data for each file
        content_data[name] = init_content_data()

        # If no content, skip processing
        if not text:
            logging.warning(f'Skipping content processing for "{name}" due to empty content.')
            continue

        # Extract basic data
        page_references = find_all_lower(patterns["page_reference"], text)
        tagged_backlinks = find_all_lower(patterns["tagged_backlink"], text)
        tags = find_all_lower(patterns["tag"], text)
        assets = find_all_lower(patterns["asset"], text)
        draws = find_all_lower(patterns["draw"], text)
        external_links = find_all_lower(patterns["external_link"], text)
        embedded_links = find_all_lower(patterns["embedded_link"], text)
        blockquotes = find_all_lower(patterns["blockquote"], text)
        flashcards = find_all_lower(patterns["flashcard"], text)
        multiline_code_blocks = find_all_lower(patterns["multiline_code_block"], text)
        calc_blocks = find_all_lower(patterns["calc_block"], text)
        multiline_code_langs = find_all_lower(patterns["multiline_code_lang"], text)
        references_general = find_all_lower(patterns["reference"], text)
        block_references = find_all_lower(patterns["block_reference"], text)
        embeds = find_all_lower(patterns["embed"], text)
        page_embeds = find_all_lower(patterns["page_embed"], text)
        block_embeds = find_all_lower(patterns["block_embed"], text)
        namespace_queries = find_all_lower(patterns["namespace_query"], text)
        clozes = find_all_lower(patterns["cloze"], text)
        simple_queries = find_all_lower(patterns["simple_query"], text)
        query_functions = find_all_lower(patterns["query_function"], text)
        advanced_commands = find_all_lower(patterns["advanced_command"], text)

        content_data[name]["page_references"] = page_references
        content_data[name]["tagged_backlinks"] = tagged_backlinks
        content_data[name]["tags"] = tags
        content_data[name]["assets"] = assets
        content_data[name]["draws"] = draws
        content_data[name]["blockquotes"] = blockquotes
        content_data[name]["flashcards"] = flashcards
        content_data[name]["multiline_code_block"] = multiline_code_blocks
        content_data[name]["calc_block"] = calc_blocks
        content_data[name]["multiline_code_lang"] = multiline_code_langs
        content_data[name]["reference"] = references_general
        content_data[name]["block_reference"] = block_references
        content_data[name]["embed"] = embeds
        content_data[name]["page_embed"] = page_embeds
        content_data[name]["block_embed"] = block_embeds
        content_data[name]["namespace_queries"] = namespace_queries
        content_data[name]["clozes"] = clozes
        content_data[name]["simple_queries"] = simple_queries
        content_data[name]["query_functions"] = query_functions
        content_data[name]["advanced_commands"] = advanced_commands

        # Extract all properties: values pairs
        properties_values = {prop: value for prop, value in patterns["property_value"].findall(text)}
        aliases = properties_values.get("alias", [])
        content_data[name]["aliases"] = process_aliases(aliases) if aliases else []
        content_data[name]["properties_values"] = properties_values

        # Extract page/block properties
        page_properties = []
        primary_bullet = meta_primary_bullet.get(name)
        primary_bullet_is_page_props = process_primary_bullet(primary_bullet)
        if primary_bullet_is_page_props:
            page_properties = find_all_lower(patterns["property"], primary_bullet)
            text = text.replace(primary_bullet, "")
        block_properties = find_all_lower(patterns["property"], text)
        properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties, props)
        properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties, props)

        content_data[name]["properties_page_builtin"] = properties_page_builtin
        content_data[name]["properties_page_user"] = properties_page_user
        content_data[name]["properties_block_builtin"] = properties_block_builtin
        content_data[name]["properties_block_user"] = properties_block_user

        # Process namespaces
        if config.NAMESPACE_SEP in name:
            namespace_parts_list = name.split(config.NAMESPACE_SEP)
            namespace_level = len(namespace_parts_list) - 1
            namespace_root = namespace_parts_list[0]
            namespace_parent = namespace_parts_list[-2] if namespace_level > 1 else namespace_root
            namespace_parts = {part: level for level, part in enumerate(namespace_parts_list)}
            content_data[name]["namespace_root"] = namespace_root
            content_data[name]["namespace_parent"] = namespace_parent
            content_data[name]["namespace_parts"] = namespace_parts
            content_data[name]["namespace_level"] = namespace_level
            unique_linked_references.update([namespace_root, name])

            if namespace_level > 0:
                if namespace_root in content_data:
                    root_level = content_data[namespace_root]["namespace_level"]
                    direct_level = 0
                    if direct_level > root_level:
                        content_data[namespace_root]["namespace_level"] = direct_level

                parent_joined = config.NAMESPACE_SEP.join(namespace_parts_list[:-1])
                if parent_joined in content_data:
                    parent_level = content_data[parent_joined]["namespace_level"]
                    direct_level = namespace_level - 1
                    if direct_level > parent_level:
                        content_data[parent_joined]["namespace_level"] = direct_level

        unique_linked_references.update(
            aliases, draws, page_references, tags, tagged_backlinks, page_properties, block_properties
        )
        unique_aliases.update(aliases)

        # Process external and embedded links
        process_external_links(patterns, content_data, name, external_links)
        process_embedded_links(patterns, content_data, name, embedded_links)

    # Create alphanum lookups and identify dangling links
    alphanum_dict = create_alphanum(sorted(unique_linked_references))
    alphanum_filenames = create_alphanum(sorted(content.keys()))
    dangling_links = identify_dangling_links(unique_aliases, alphanum_dict, alphanum_filenames)

    return content_data, alphanum_dict, dangling_links


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def identify_dangling_links(
    unique_aliases: Set[str], alphanum_dict: Dict[str, Set[str]], alphanum_filenames: Dict[str, Set[str]]
) -> Set[str]:
    """Identify dangling links in the alphanum lookups and aliases."""
    dangling_links = set()
    for id, references in alphanum_dict.items():
        if id not in alphanum_filenames:
            dangling_links.update(references)
        else:
            dangling_links.update([ref for ref in references if ref not in alphanum_filenames[id]])
    dangling_links -= unique_aliases
    return dangling_links


def create_alphanum(list_lookup: List[str]) -> Dict[str, Set[str]]:
    """Create alphanum dictionary from a list of strings."""
    alphanum_dict = defaultdict(set)
    for item in list_lookup:
        if item:
            id = item[:2] if len(item) > 1 else f"!{item[0]}"
            alphanum_dict[id].add(item)
        else:
            logging.error(f"Empty item: {item}")
    return alphanum_dict


def split_builtin_user_properties(properties: list, built_in_props: Set[str]) -> Tuple[list, list]:
    """Helper function to split properties into built-in and user-defined."""
    builtin_props = [prop for prop in properties if prop in built_in_props]
    user_props = [prop for prop in properties if prop not in built_in_props]
    return builtin_props, user_props


def process_aliases(aliases: str) -> List[str]:
    """Process aliases to extract individual aliases."""
    results = []
    current = []
    inside_brackets = False
    i = 0
    while i < len(aliases):
        if aliases[i : i + 2] == "[[":
            inside_brackets = True
            i += 2
            continue
        elif aliases[i : i + 2] == "]]":
            inside_brackets = False
            i += 2
            continue
        elif aliases[i] == "," and not inside_brackets:
            part = "".join(current).strip().lower()
            if part:
                results.append(part)
            current = []
            i += 1
            continue
        else:
            current.append(aliases[i])
            i += 1

    part = "".join(current).strip().lower()
    if part:
        results.append(part)
    return results


def process_external_links(
    patterns: Dict[str, Pattern], content_data: Dict[str, Any], name: str, external_links: List[str]
) -> None:
    """Process external links and categorize them."""
    if external_links:
        content_data[name]["external_links"] = external_links
        external_links_str = "\n".join(external_links)

        external_links_internet = [
            link.lower() for link in patterns["external_link_internet"].findall(external_links_str)
        ]
        if external_links_internet:
            content_data[name]["external_links_internet"] = external_links_internet

        external_links_alias = [link.lower() for link in patterns["external_link_alias"].findall(external_links_str)]
        if external_links_alias:
            content_data[name]["external_links_alias"] = external_links_alias


def process_embedded_links(
    patterns: Dict[str, Pattern], content_data: Dict[str, Any], name: str, embedded_links: List[str]
) -> None:
    """Process embedded links and categorize them."""
    if embedded_links:
        content_data[name]["embedded_links"] = embedded_links
        embedded_links_str = "\n".join(embedded_links)

        embedded_links_internet = [
            link.lower() for link in patterns["embedded_link_internet"].findall(embedded_links_str)
        ]
        if embedded_links_internet:
            content_data[name]["embedded_links_internet"] = embedded_links_internet

        embedded_links_asset = [link.lower() for link in patterns["embedded_link_asset"].findall(embedded_links_str)]
        if embedded_links_asset:
            content_data[name]["embedded_links_asset"] = embedded_links_asset


def process_primary_bullet(primary_bullet: Dict[str, Any]) -> bool:
    """
    Process primary bullet data.

    Args:
        primary_bullet (Dict[str, Any]): The primary bullet data.

    Returns:
        bool: True if the primary bullet is page properties, False otherwise.
    """
    primary_bullet = primary_bullet.strip()
    if not primary_bullet or primary_bullet.startswith("#"):
        return False
    return True
