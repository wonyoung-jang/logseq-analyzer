"""
Process content data for Logseq.
"""

from collections import defaultdict
from typing import Any, Dict, List, Pattern, Set, Tuple
import logging

from ._global_objects import PATTERNS, CONFIG


def process_content_data(
    data: Dict[str, Any],
    content: str,
    primary_bullet: Dict[str, Any],
    content_bullets: List[str],
) -> Dict[str, Any]:
    """
    Process content data to extract various elements like backlinks, tags, and properties.

    Args:
        data (Dict[str, Any]): The initial data dictionary.
        content (str): The content to process.
        primary_bullet (Dict[str, Any]): The primary bullet data.
        content_bullets (List[str]): The list of bullet points extracted from the content.

    Returns:
        Dict[str, Any]: The updated data dictionary with extracted elements.
    """
    # Process namespaces
    ns_sep = CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")
    if ns_sep in data["name"]:
        for key, value in process_content_namespace_data(data, ns_sep):
            data[key] = value

    # If no content, return data
    if not content:
        return data

    # Extract basic data
    advanced_commands = find_all_lower(PATTERNS.content["advanced_command"], content)
    assets = find_all_lower(PATTERNS.content["asset"], content)
    block_embeds = find_all_lower(PATTERNS.content["block_embed"], content)
    block_references = find_all_lower(PATTERNS.content["block_reference"], content)
    blockquotes = find_all_lower(PATTERNS.content["blockquote"], content)
    calc_blocks = find_all_lower(PATTERNS.content["calc_block"], content)
    clozes = find_all_lower(PATTERNS.content["cloze"], content)
    draws = find_all_lower(PATTERNS.content["draw"], content)
    embeds = find_all_lower(PATTERNS.content["embed"], content)
    flashcards = find_all_lower(PATTERNS.content["flashcard"], content)
    multiline_code_blocks = find_all_lower(PATTERNS.content["multiline_code_block"], content)
    multiline_code_langs = find_all_lower(PATTERNS.content["multiline_code_lang"], content)
    namespace_queries = find_all_lower(PATTERNS.content["namespace_query"], content)
    page_embeds = find_all_lower(PATTERNS.content["page_embed"], content)
    page_references = find_all_lower(PATTERNS.content["page_reference"], content)
    query_functions = find_all_lower(PATTERNS.content["query_function"], content)
    references_general = find_all_lower(PATTERNS.content["reference"], content)
    simple_queries = find_all_lower(PATTERNS.content["simple_query"], content)
    tagged_backlinks = find_all_lower(PATTERNS.content["tagged_backlink"], content)
    tags = find_all_lower(PATTERNS.content["tag"], content)

    # Extract all properties: values pairs
    properties_values = {}
    property_value_all = PATTERNS.content["property_value"].findall(content)
    for prop, value in property_value_all:
        properties_values.setdefault(prop, value)

    aliases = properties_values.get("alias", "")
    if aliases:
        aliases = process_aliases(aliases)

    # Extract page/block properties
    page_properties = []
    primary_bullet_is_page_props = is_primary_bullet_page_properties(primary_bullet)
    if primary_bullet_is_page_props:
        page_properties = find_all_lower(PATTERNS.content["property"], primary_bullet)
        content = "\n".join(content_bullets)
    block_properties = find_all_lower(PATTERNS.content["property"], content)

    properties_page_builtin, properties_page_user = split_builtin_user_properties(page_properties)
    properties_block_builtin, properties_block_user = split_builtin_user_properties(block_properties)

    # Process external and embedded links
    external_links = find_all_lower(PATTERNS.content["external_link"], content)
    embedded_links = find_all_lower(PATTERNS.content["embedded_link"], content)
    external_links_other, external_links_internet, external_links_alias = process_ext_emb_links(
        external_links, "external"
    )
    embedded_links_other, embedded_links_internet, embedded_links_asset = process_ext_emb_links(
        embedded_links, "embedded"
    )

    primary_data = {
        "advanced_commands": advanced_commands,
        "aliases": aliases,
        "assets": assets,
        "block_embeds": block_embeds,
        "block_references": block_references,
        "blockquotes": blockquotes,
        "calc_blocks": calc_blocks,
        "clozes": clozes,
        "draws": draws,
        "embedded_links_asset": embedded_links_asset,
        "embedded_links_internet": embedded_links_internet,
        "embedded_links_other": embedded_links_other,
        "embeds": embeds,
        "external_links_alias": external_links_alias,
        "external_links_internet": external_links_internet,
        "external_links_other": external_links_other,
        "flashcards": flashcards,
        "multiline_code_blocks": multiline_code_blocks,
        "multiline_code_langs": multiline_code_langs,
        "namespace_queries": namespace_queries,
        "page_embeds": page_embeds,
        "page_references": page_references,
        "properties_block_builtin": properties_block_builtin,
        "properties_block_user": properties_block_user,
        "properties_page_builtin": properties_page_builtin,
        "properties_page_user": properties_page_user,
        "properties_values": properties_values,
        "query_functions": query_functions,
        "references_general": references_general,
        "simple_queries": simple_queries,
        "tagged_backlinks": tagged_backlinks,
        "tags": tags,
    }

    for key, value in primary_data.items():
        if value:
            data[key] = value

    return data


def process_content_namespace_data(data: Dict[str, Any], ns_sep: str):
    """
    Process namespaces in the data dictionary.
    """
    namespace_parts_list = data["name"].split(ns_sep)
    namespace_level = len(namespace_parts_list)
    namespace_root = namespace_parts_list[0]
    namespace_stem = namespace_parts_list[-1]
    namespace_parent = namespace_root
    if namespace_level > 2:
        namespace_parent = namespace_parts_list[-2]

    namespace_parts = {part: level for level, part in enumerate(namespace_parts_list, start=1)}
    namespace_data = {
        "namespace_root": namespace_root,
        "namespace_parent": namespace_parent,
        "namespace_stem": namespace_stem,
        "namespace_parts": namespace_parts,
        "namespace_level": namespace_level,
    }

    for key, value in namespace_data.items():
        if value:
            yield key, value


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
            logging.error("Empty item: %s", item)
    return alphanum_dict


def split_builtin_user_properties(properties: list) -> Tuple[list, list]:
    """Helper function to split properties into built-in and user-defined."""
    builtin_props = [prop for prop in properties if prop in CONFIG.get_built_in_properties()]
    user_props = [prop for prop in properties if prop not in CONFIG.get_built_in_properties()]
    return builtin_props, user_props


def process_aliases(aliases: str) -> List[str]:
    """Process aliases to extract individual aliases."""
    aliases = aliases.strip()
    results = []
    current = []
    inside_brackets = False
    i = 0
    while i < len(aliases):
        if aliases[i : i + 2] == "[[":
            inside_brackets = True
            i += 2
        elif aliases[i : i + 2] == "]]":
            inside_brackets = False
            i += 2
        elif aliases[i] == "," and not inside_brackets:
            part = "".join(current).strip().lower()
            if part:
                results.append(part)
            current = []
            i += 1
        else:
            current.append(aliases[i])
            i += 1

    part = "".join(current).strip().lower()
    if part:
        results.append(part)
    return results


def process_ext_emb_links(links: List[str], links_type: str) -> Tuple[str, str, str]:
    """Process external and embedded links and categorize them."""
    links_internet_pattern = f"{links_type}_link_internet"
    links_sub_pattern = ""
    if links_type == "external":
        links_sub_pattern = f"{links_type}_link_alias"
    elif links_type == "embedded":
        links_sub_pattern = f"{links_type}_link_asset"

    internet = []
    alias_or_asset = []
    if links:
        for _ in range(len(links)):
            link = links[-1]
            if PATTERNS.content[links_internet_pattern].match(link):
                internet.append(link)
                links.pop()
                continue

            if PATTERNS.content[links_sub_pattern].match(link):
                alias_or_asset.append(link)
                links.pop()
                continue

    return links, internet, alias_or_asset


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


def post_processing_content_namespaces(
    content_data: Dict[str, Any], name: str, data: Dict[str, Any], ns_sep: str
) -> Dict[str, Any]:
    """
    Post-process namespaces in the content data.
    """
    namespace_parts_list = name.split(ns_sep)
    namespace_root = data["namespace_root"]
    namespace_level = data["namespace_level"]

    if namespace_root in content_data:
        root_level = content_data[namespace_root].get("namespace_level", 0)
        direct_level = 1
        if direct_level > root_level:
            content_data[namespace_root]["namespace_level"] = direct_level
        content_data[namespace_root].setdefault("namespace_children", set())
        content_data[namespace_root]["namespace_children"].add(name)
        content_data[namespace_root]["namespace_size"] = len(content_data[namespace_root]["namespace_children"])

    parent_joined = ns_sep.join(namespace_parts_list[:-1])
    if parent_joined in content_data:
        parent_level = content_data[parent_joined].get("namespace_level", 0)
        direct_level = namespace_level - 1
        if direct_level > parent_level:
            content_data[parent_joined]["namespace_level"] = direct_level
        content_data[parent_joined].setdefault("namespace_children", set())
        content_data[parent_joined]["namespace_children"].add(name)
        content_data[parent_joined]["namespace_size"] = len(content_data[parent_joined]["namespace_children"])

    return content_data


def post_processing_content(
    content_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Set[str]], Dict[str, Set[str]], Set[str], Dict[str, Any]]:
    """
    Post-process content data to extract linked references and namespaces.

    Args:
        content_data (Dict[str, Any]): The content data to process.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Set[str]], Dict[str, Set[str]], Set[str], Dict[str, Any]]:
            Processed content data, alphanum dicts, dangling links, and all linked references.
    """
    all_linked_references = {}
    unique_linked_references = set()
    unique_linked_references_namespaces = set()
    unique_aliases = set()

    # Process each file's content
    ns_sep = CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")

    for name, data in content_data.items():
        # Process namespaces
        if ns_sep in name:
            unique_linked_references_namespaces.update([data["namespace_root"], name])
            content_data = post_processing_content_namespaces(content_data, name, data, ns_sep)

        # Update aliases and linked references
        unique_aliases.update(data.get("aliases", []))
        ns_parent = data.get("namespace_parent", "")
        linked_references = [
            list(unique_aliases),
            data.get("draws", []),
            data.get("page_references", []),
            data.get("tags", []),
            data.get("tagged_backlinks", []),
            data.get("properties_page_builtin", []),
            data.get("properties_page_user", []),
            data.get("properties_block_builtin", []),
            data.get("properties_block_user", []),
            [ns_parent],
        ]

        linked_references = [item for sublist in linked_references for item in sublist if item]

        for item in linked_references:
            all_linked_references.setdefault(item, {})
            all_linked_references[item]["count"] = all_linked_references[item].get("count", 0) + 1
            all_linked_references[item].setdefault("found_in", []).append(name)

        if ns_parent:
            linked_references.remove(ns_parent)

        unique_linked_references.update(linked_references)

    # Create alphanum lookups and identify dangling links
    all_linked_references = dict(sorted(all_linked_references.items(), key=lambda item: item[1]["count"], reverse=True))
    unique_filenames = set(sorted(content_data.keys()))
    unique_aliases = set(sorted(unique_aliases))
    unique_linked_references = set(sorted(unique_linked_references))
    unique_linked_references_namespaces = set(sorted(unique_linked_references_namespaces))
    unique_linked_references_all = unique_linked_references.union(unique_linked_references_namespaces)
    dangling_links = unique_linked_references_all.copy()
    dangling_links.difference_update(unique_filenames)
    dangling_links.difference_update(unique_aliases)
    alphanum_dict = create_alphanum(unique_linked_references)
    alphanum_dict_ns = create_alphanum(unique_linked_references_namespaces)

    return content_data, alphanum_dict, alphanum_dict_ns, dangling_links, all_linked_references


def remove_double_brackets(text: str) -> str:
    """
    Remove double brackets from the text.

    Args:
        text (str): The text to process.

    Returns:
        str: The processed text without double brackets.
    """
    return text.replace("[[", "").replace("]]", "").strip()
