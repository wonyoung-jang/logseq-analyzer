import logging
from collections import defaultdict
from typing import Any, Dict, List, Pattern, Set, Tuple

from src import config


def process_content_data(
    data: Dict[str, Any], content: str, patterns: Dict[str, Pattern], primary_bullet
) -> Dict[str, Any]:
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

    data["page_references"] = page_references
    data["tagged_backlinks"] = tagged_backlinks
    data["tags"] = tags
    data["assets"] = assets
    data["draws"] = draws
    data["blockquotes"] = blockquotes
    data["flashcards"] = flashcards
    data["multiline_code_block"] = multiline_code_blocks
    data["calc_block"] = calc_blocks
    data["multiline_code_lang"] = multiline_code_langs
    data["reference"] = references_general
    data["block_reference"] = block_references
    data["embed"] = embeds
    data["page_embed"] = page_embeds
    data["block_embed"] = block_embeds
    data["namespace_queries"] = namespace_queries
    data["clozes"] = clozes
    data["simple_queries"] = simple_queries
    data["query_functions"] = query_functions
    data["advanced_commands"] = advanced_commands

    # Extract all properties: values pairs
    properties_values = {prop: value for prop, value in patterns["property_value"].findall(content)}
    aliases = properties_values.get("alias", [])
    if aliases:
        aliases = process_aliases(aliases)
    data["aliases"] = aliases
    data["properties_values"] = properties_values

    # Extract page/block properties
    page_properties = []
    primary_bullet_is_page_props = process_primary_bullet(primary_bullet)
    if primary_bullet_is_page_props:
        page_properties = find_all_lower(patterns["property"], primary_bullet)
        content = content.replace(primary_bullet, "")
    block_properties = find_all_lower(patterns["property"], content)
    built_in_props = config.BUILT_IN_PROPERTIES
    properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties, built_in_props)
    properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties, built_in_props)
    data["properties_page_builtin"] = properties_page_builtin
    data["properties_page_user"] = properties_page_user
    data["properties_block_builtin"] = properties_block_builtin
    data["properties_block_user"] = properties_block_user

    # Process external and embedded links
    external_links = find_all_lower(patterns["external_link"], content)
    embedded_links = find_all_lower(patterns["embedded_link"], content)
    process_external_links(patterns, data, external_links)
    process_embedded_links(patterns, data, embedded_links)

    # Process namespaces
    if config.NAMESPACE_SEP in data["name"]:
        namespace_parts_list = data["name"].split(config.NAMESPACE_SEP)
        namespace_level = len(namespace_parts_list) - 1
        namespace_root = namespace_parts_list[0]
        namespace_parent = namespace_parts_list[-2] if namespace_level > 1 else namespace_root
        namespace_parts = {part: level for level, part in enumerate(namespace_parts_list)}
        data["namespace_root"] = namespace_root
        data["namespace_parent"] = namespace_parent
        data["namespace_parts"] = namespace_parts
        data["namespace_level"] = namespace_level

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


def process_external_links(
    patterns: Dict[str, Pattern], content_data: Dict[str, Any], external_links: List[str]
) -> None:
    """Process external links and categorize them."""
    if external_links:
        content_data["external_links"] = external_links
        external_links_str = "\n".join(external_links)

        external_links_internet = [
            link.lower() for link in patterns["external_link_internet"].findall(external_links_str)
        ]
        if external_links_internet:
            content_data["external_links_internet"] = external_links_internet

        external_links_alias = [link.lower() for link in patterns["external_link_alias"].findall(external_links_str)]
        if external_links_alias:
            content_data["external_links_alias"] = external_links_alias


def process_embedded_links(
    patterns: Dict[str, Pattern], content_data: Dict[str, Any], embedded_links: List[str]
) -> None:
    """Process embedded links and categorize them."""
    if embedded_links:
        content_data["embedded_links"] = embedded_links
        embedded_links_str = "\n".join(embedded_links)

        embedded_links_internet = [
            link.lower() for link in patterns["embedded_link_internet"].findall(embedded_links_str)
        ]
        if embedded_links_internet:
            content_data["embedded_links_internet"] = embedded_links_internet

        embedded_links_asset = [link.lower() for link in patterns["embedded_link_asset"].findall(embedded_links_str)]
        if embedded_links_asset:
            content_data["embedded_links_asset"] = embedded_links_asset


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

        # Update aliases and linked references
        unique_aliases.update(data["aliases"])
        unique_linked_references.update(
            unique_aliases,
            data["draws"],
            data["page_references"],
            data["tags"],
            data["tagged_backlinks"],
            data["properties_page_builtin"],
            data["properties_page_user"],
            data["properties_block_builtin"],
            data["properties_block_user"],
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
