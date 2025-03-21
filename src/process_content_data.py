import logging
from collections import defaultdict
from typing import Any, Dict, List, Pattern, Set, Tuple

from src import config


def process_content_data(
    data: Dict[str, Any], content: str, patterns: Dict[str, Pattern], primary_bullet
) -> Dict[str, Any]:
    # Process namespaces
    data["namespace_level"] = 0
    if config.NAMESPACE_SEP in data["name"]:
        namespace_parts_list = data["name"].split(config.NAMESPACE_SEP)
        namespace_level = len(namespace_parts_list)
        namespace_root = namespace_parts_list[0]
        if namespace_level > 2:
            namespace_parent = namespace_parts_list[-2]
        else:
            namespace_parent = namespace_root
            
        namespace_parts = {part: level for level, part in enumerate(namespace_parts_list, start=1)}
        namespace_data = {
            "namespace_root": namespace_root,
            "namespace_parent": namespace_parent,
            "namespace_parts": namespace_parts,
            "namespace_level": namespace_level,
        }

        for key, value in namespace_data.items():
            if value:
                data[key] = value

    # If no content, return data
    if not content:
        return data

    # Extract basic data
    page_references = find_all_lower(patterns["page_reference"], content)
    tagged_backlinks = find_all_lower(patterns["tagged_backlink"], content)
    tags = find_all_lower(patterns["tag"], content)
    assets = find_all_lower(patterns["asset"], content)
    draws = find_all_lower(patterns["draw"], content)
    blockquotes = find_all_lower(patterns["blockquote"], content)
    flashcards = find_all_lower(patterns["flashcard"], content)
    multiline_code_blocks = find_all_lower(patterns["multiline_code_block"], content)
    calc_blocks = find_all_lower(patterns["calc_block"], content)
    multiline_code_langs = find_all_lower(patterns["multiline_code_lang"], content)
    references_general = find_all_lower(patterns["reference"], content)
    block_references = find_all_lower(patterns["block_reference"], content)
    embeds = find_all_lower(patterns["embed"], content)
    page_embeds = find_all_lower(patterns["page_embed"], content)
    block_embeds = find_all_lower(patterns["block_embed"], content)
    namespace_queries = find_all_lower(patterns["namespace_query"], content)
    clozes = find_all_lower(patterns["cloze"], content)
    simple_queries = find_all_lower(patterns["simple_query"], content)
    query_functions = find_all_lower(patterns["query_function"], content)
    advanced_commands = find_all_lower(patterns["advanced_command"], content)

    # Extract all properties: values pairs
    properties_values = {prop: value for prop, value in patterns["property_value"].findall(content)}
    aliases = properties_values.get("alias", [])
    if aliases:
        aliases = process_aliases(aliases)

    # Extract page/block properties
    page_properties = []
    primary_bullet_is_page_props = is_primary_bullet_page_properties(primary_bullet)
    if primary_bullet_is_page_props:
        page_properties = find_all_lower(patterns["property"], primary_bullet)
        content = content.replace(primary_bullet, "")
    block_properties = find_all_lower(patterns["property"], content)
    built_in_props = config.BUILT_IN_PROPERTIES
    properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties, built_in_props)
    properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties, built_in_props)

    # Process external and embedded links
    external_links = find_all_lower(patterns["external_link"], content)
    embedded_links = find_all_lower(patterns["embedded_link"], content)
    external_links_other, external_links_internet, external_links_alias = process_ext_emb_links(
        patterns, external_links, "external"
    )
    embedded_links_other, embedded_links_internet, embedded_links_asset = process_ext_emb_links(
        patterns, embedded_links, "embedded"
    )

    primary_data = {
        "page_references": page_references,
        "tagged_backlinks": tagged_backlinks,
        "tags": tags,
        "assets": assets,
        "draws": draws,
        "blockquotes": blockquotes,
        "flashcards": flashcards,
        "multiline_code_blocks": multiline_code_blocks,
        "calc_blocks": calc_blocks,
        "multiline_code_langs": multiline_code_langs,
        "references_general": references_general,
        "block_references": block_references,
        "embeds": embeds,
        "page_embeds": page_embeds,
        "block_embeds": block_embeds,
        "namespace_queries": namespace_queries,
        "clozes": clozes,
        "simple_queries": simple_queries,
        "query_functions": query_functions,
        "advanced_commands": advanced_commands,
        "aliases": aliases,
        "properties_values": properties_values,
        "properties_page_builtin": properties_page_builtin,
        "properties_page_user": properties_page_user,
        "properties_block_builtin": properties_block_builtin,
        "properties_block_user": properties_block_user,
        "external_links_other": external_links_other,
        "external_links_internet": external_links_internet,
        "external_links_alias": external_links_alias,
        "embedded_links_other": embedded_links_other,
        "embedded_links_internet": embedded_links_internet,
        "embedded_links_asset": embedded_links_asset,
    }

    for key, value in primary_data.items():
        if value:
            data[key] = value

    return data


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def create_alphanum(list_lookup: List[str]) -> Dict[str, Set[str]]:
    """Create alphanum dictionary from a list of strings."""
    alphanum_dict = defaultdict(set)
    for item in list_lookup:
        if item:
            id_key = item[:2] if len(item) > 1 else f"!{item[0]}"
            alphanum_dict[id_key].add(item)
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


def process_ext_emb_links(patterns: Dict[str, Pattern], links: List[str], links_type: str) -> Tuple[str, str, str]:
    """Process external and embedded links and categorize them."""
    links_other = f"{links_type}_links_other"
    links_internet = f"{links_type}_links_internet"
    links_internet_pattern = f"{links_type}_link_internet"
    if links_type == "external":
        links_subtype = f"{links_type}_links_alias"
        links_sub_pattern = f"{links_type}_link_alias"
    elif links_type == "embedded":
        links_subtype = f"{links_type}_links_asset"
        links_sub_pattern = f"{links_type}_link_asset"

    if links:
        internet = []
        alias_or_asset = []
        for _ in range(len(links)):
            link = links[0]
            if patterns[links_internet_pattern].match(link):
                internet.append(link)
            elif patterns[links_sub_pattern].match(link):
                alias_or_asset.append(link)
            links.pop(0)
    return links_other, links_internet, links_subtype


def is_primary_bullet_page_properties(primary_bullet: Dict[str, Any]) -> bool:
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


def post_processing_content(content_data):
    unique_linked_references = set()
    unique_linked_references_namespaces = set()
    unique_aliases = set()

    # Process each file's content
    for name, data in content_data.items():
        # Process namespaces
        if config.NAMESPACE_SEP in name:
            namespace_parts_list = name.split(config.NAMESPACE_SEP)
            namespace_root = data["namespace_root"]
            namespace_level = data["namespace_level"]
            unique_linked_references_namespaces.update([namespace_root, name])

            if namespace_root in content_data:
                root_level = content_data[namespace_root]["namespace_level"]
                direct_level = 1
                if direct_level > root_level:
                    content_data[namespace_root]["namespace_level"] = direct_level

            parent_joined = config.NAMESPACE_SEP.join(namespace_parts_list[:-1])
            if parent_joined in content_data:
                parent_level = content_data[parent_joined]["namespace_level"]
                direct_level = namespace_level - 1
                if direct_level > parent_level:
                    content_data[parent_joined]["namespace_level"] = direct_level

        # Update aliases and linked references
        unique_aliases.update(data.get("aliases", []))
        unique_linked_references.update(
            unique_aliases,
            data.get("draws", []),
            data.get("page_references", []),
            data.get("tags", []),
            data.get("tagged_backlinks", []),
            data.get("properties_page_builtin", []),
            data.get("properties_page_user", []),
            data.get("properties_block_builtin", []),
            data.get("properties_block_user", []),
        )

    # Create alphanum lookups and identify dangling links
    unique_filenames = set(sorted(content_data.keys()))
    unique_aliases = set(sorted(unique_aliases))
    unique_linked_references = set(sorted(unique_linked_references))
    unique_linked_references_namespaces = set(sorted(unique_linked_references_namespaces))
    unique_linked_references_all = unique_linked_references.union(unique_linked_references_namespaces)
    dangling_links = unique_linked_references_all.difference(unique_filenames, unique_aliases)
    alphanum_dict = create_alphanum(unique_linked_references)
    alphanum_dict_ns = create_alphanum(unique_linked_references_namespaces)

    return content_data, alphanum_dict, alphanum_dict_ns, dangling_links
