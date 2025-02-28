import re
import logging
import src.config as config
from collections import defaultdict
from typing import Dict, Pattern, Set, Any, Tuple, List


def process_content_data(
    content: Dict[str, str], patterns: Dict[str, Pattern], props: Set[str]
) -> Tuple[Dict[str, Any], Dict[str, Set[str]], List[str]]:
    """
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
    """
    content_data = defaultdict(lambda: defaultdict(list))
    alphanum_dict = defaultdict(set)
    unique_linked_references = set()

    for name, text in content.items():
        content_data[name]["page_references"] = []
        content_data[name]["tags"] = []
        content_data[name]["tagged_backlinks"] = []
        content_data[name]["properties"] = []
        content_data[name]["properties_page_builtin"] = []
        content_data[name]["properties_page_user"] = []
        content_data[name]["properties_block_builtin"] = []
        content_data[name]["properties_block_user"] = []
        content_data[name]["assets"] = []
        content_data[name]["draws"] = []
        content_data[name]["namespace_root"] = ""
        content_data[name]["namespace_parent"] = ""
        content_data[name]["namespace_parts"] = {}
        content_data[name]["namespace_level"] = -1
        content_data[name]["external_links"] = []
        content_data[name]["external_links_internet"] = []
        content_data[name]["external_links_alias"] = []
        content_data[name]["embedded_links"] = []
        content_data[name]["embedded_links_internet"] = []
        content_data[name]["embedded_links_asset"] = []

        if not text:
            logging.debug(f'Skipping content processing for "{name}" due to empty content.')
            continue

        # Page references
        page_references = [page_ref.lower() for page_ref in patterns["page_reference"].findall(text)]
        tags = [tag.lower() for tag in patterns["tag"].findall(text)]
        tagged_backlinks = [tag.lower() for tag in patterns["tagged_backlink"].findall(text)]
        assets = [asset.lower() for asset in patterns["asset"].findall(text)]
        draws = [draw.lower() for draw in patterns["draw"].findall(text)]
        external_links = [link.lower() for link in patterns["external_link"].findall(text)]
        embedded_links = [link.lower() for link in patterns["embedded_link"].findall(text)]
        properties = [prop.lower() for prop in patterns["property"].findall(text)]

        page_properties, block_properties = extract_page_block_properties(text, patterns)

        content_data[name]["page_references"] = page_references
        content_data[name]["tags"] = tags
        content_data[name]["tagged_backlinks"] = tagged_backlinks
        content_data[name]["properties"] = properties
        content_data[name]["assets"] = assets
        content_data[name]["draws"] = draws

        (
            content_data[name]["properties_page_builtin"],
            content_data[name]["properties_page_user"],
        ) = split_builtin_user_properties(page_properties, props)

        (
            content_data[name]["properties_block_builtin"],
            content_data[name]["properties_block_user"],
        ) = split_builtin_user_properties(block_properties, props)

        # Namespace
        if config.NAMESPACE_SEP in name:
            namespace_parts = name.split(config.NAMESPACE_SEP)
            namespace_level = len(namespace_parts)
            namespace_root = namespace_parts[0]
            namespace_parent = namespace_parts[-2] if namespace_level > 1 else namespace_root
            namespace_parts = {part: level for level, part in enumerate(namespace_parts)}
            content_data[name]["namespace_root"] = namespace_root
            content_data[name]["namespace_parent"] = namespace_parent
            content_data[name]["namespace_parts"] = namespace_parts
            content_data[name]["namespace_level"] = namespace_level
            unique_linked_references.update([namespace_root, name])

        unique_linked_references.update(draws, page_references, tags, tagged_backlinks, page_properties, block_properties)

        # External links
        if external_links:
            content_data[name]["external_links"] = external_links
            external_links_str = "\n".join(embedded_links)

            external_links_internet = [link.lower() for link in patterns["external_link_internet"].findall(external_links_str)]
            if external_links_internet:
                content_data[name]["external_links_internet"] = external_links_internet

            external_links_alias = [link.lower() for link in patterns["external_link_alias"].findall(external_links_str)]
            if external_links_alias:
                content_data[name]["external_links_alias"] = external_links_alias

        # Embedded links
        if embedded_links:
            content_data[name]["embedded_links"] = embedded_links
            embedded_links_str = "\n".join(embedded_links)

            embedded_links_internet = [link.lower() for link in patterns["embedded_link_internet"].findall(embedded_links_str)]
            if embedded_links_internet:
                content_data[name]["embedded_links_internet"] = embedded_links_internet

            embedded_links_asset = [link.lower() for link in patterns["embedded_link_asset"].findall(embedded_links_str)]
            if embedded_links_asset:
                content_data[name]["embedded_links_asset"] = embedded_links_asset

    # Create alphanum dictionary
    for linked_reference in unique_linked_references:
        if linked_reference:
            first_char_id = linked_reference[:2] if len(linked_reference) > 1 else f"!{linked_reference[0]}"
            alphanum_dict[first_char_id].add(linked_reference)
        else:
            logging.info(f"Empty linked reference: {linked_reference}")

    # Check for dangling links (linked, but no file)
    all_filenames = list(content.keys())
    alphanum_filenames = defaultdict(set)
    for filename in all_filenames:
        if filename:
            first_char_id = filename[:2] if len(filename) > 1 else f"!{filename[0]}"
            alphanum_filenames[first_char_id].add(filename)
        else:
            logging.info(f"Empty filename: {filename}")
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
    """Extract page and block properties from text using a combined regex search."""
    # The regex groups a heading marker or a bullet marker.
    split_match = re.search(r"^\s*(#+\s|-\s)", text, re.MULTILINE)

    if split_match:
        split_point = split_match.start()
        page_text = text[:split_point]
        block_text = text[split_point:]
    else:
        page_text = text
        block_text = ""

    page_properties = [prop.lower() for prop in patterns["property"].findall(page_text)]
    block_properties = [prop.lower() for prop in patterns["property"].findall(block_text)]
    return page_properties, block_properties


def split_builtin_user_properties(properties: list, built_in_props: Set[str]) -> Tuple[list, list]:
    """Helper function to split properties into built-in and user-defined."""
    builtin_props = [prop for prop in properties if prop in built_in_props]
    user_props = [prop for prop in properties if prop not in built_in_props]
    return builtin_props, user_props
