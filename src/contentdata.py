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
            - dangling_links: List of dangling links (linked, but no file).
    """
    content_data = {}
    unique_linked_references = set()
    unique_aliases = set()

    # Process each file's content
    for name, text in content.items():
        content_data[name] = {}
        content_data[name]["aliases"] = []
        content_data[name]["namespace_root"] = ""
        content_data[name]["namespace_parent"] = ""
        content_data[name]["namespace_parts"] = {}
        content_data[name]["namespace_level"] = -1

        content_data[name]["page_references"] = []
        content_data[name]["tagged_backlinks"] = []
        content_data[name]["tags"] = []

        content_data[name]["properties_values"] = []
        content_data[name]["properties_page_builtin"] = []
        content_data[name]["properties_page_user"] = []
        content_data[name]["properties_block_builtin"] = []
        content_data[name]["properties_block_user"] = []

        content_data[name]["assets"] = []
        content_data[name]["draws"] = []

        content_data[name]["external_links"] = []
        content_data[name]["external_links_internet"] = []
        content_data[name]["external_links_alias"] = []
        content_data[name]["embedded_links"] = []
        content_data[name]["embedded_links_internet"] = []
        content_data[name]["embedded_links_asset"] = []

        content_data[name]["blockquotes"] = []
        content_data[name]["flashcards"] = []
        content_data[name]["multiline_code_block"] = []
        content_data[name]["calc_block"] = []
        content_data[name]["multiline_code_lang"] = []
        content_data[name]["reference"] = []
        content_data[name]["block_reference"] = []
        content_data[name]["embed"] = []
        content_data[name]["page_embed"] = []
        content_data[name]["block_embed"] = []
        content_data[name]["namespace_queries"] = []
        content_data[name]["clozes"] = []
        content_data[name]["simple_queries"] = []
        content_data[name]["query_functions"] = []
        content_data[name]["advanced_commands"] = []

        if not text:
            logging.debug(f'Skipping content processing for "{name}" due to empty content.')
            continue

        # Page references
        page_references = [page_ref.lower() for page_ref in patterns["page_reference"].findall(text)]
        tagged_backlinks = [tag.lower() for tag in patterns["tagged_backlink"].findall(text)]
        tags = [tag.lower() for tag in patterns["tag"].findall(text)]
        assets = [asset.lower() for asset in patterns["asset"].findall(text)]
        draws = [draw.lower() for draw in patterns["draw"].findall(text)]
        external_links = [link.lower() for link in patterns["external_link"].findall(text)]
        embedded_links = [link.lower() for link in patterns["embedded_link"].findall(text)]

        blockquotes = [quote.lower() for quote in patterns["blockquote"].findall(text)]
        flashcards = [flashcard.lower() for flashcard in patterns["flashcard"].findall(text)]
        multiline_code_blocks = [code.lower() for code in patterns["multiline_code_block"].findall(text)]
        calc_blocks = [calc.lower() for calc in patterns["calc_block"].findall(text)]
        multiline_code_langs = [lang.lower() for lang in patterns["multiline_code_lang"].findall(text)]
        references_general = [ref.lower() for ref in patterns["reference"].findall(text)]
        block_references = [block_ref.lower() for block_ref in patterns["block_reference"].findall(text)]
        embeds = [embed.lower() for embed in patterns["embed"].findall(text)]
        page_embeds = [page_embed.lower() for page_embed in patterns["page_embed"].findall(text)]
        block_embeds = [block_embed.lower() for block_embed in patterns["block_embed"].findall(text)]
        namespace_queries = [ns_query.lower() for ns_query in patterns["namespace_query"].findall(text)]
        clozes = [cloze.lower() for cloze in patterns["cloze"].findall(text)]
        simple_queries = [simple_query.lower() for simple_query in patterns["simple_query"].findall(text)]
        query_functions = [query_function.lower() for query_function in patterns["query_function"].findall(text)]
        advanced_commands = [adv_cmd.lower() for adv_cmd in patterns["advanced_command"].findall(text)]

        properties_values = {prop: value for prop, value in patterns["property_value"].findall(text)}
        page_properties, block_properties = extract_page_block_properties(text, patterns)
        aliases = properties_values.get("alias", [])
        processed_aliases = []
        if aliases:
            processed_aliases = process_aliases(aliases)
            content_data[name]["aliases"] = processed_aliases

        content_data[name]["page_references"] = page_references
        content_data[name]["properties_values"] = properties_values

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

            if namespace_level >= 1:
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
            processed_aliases, draws, page_references, tags, tagged_backlinks, page_properties, block_properties
        )
        unique_aliases.update(processed_aliases)

        # External links
        process_external_links(patterns, content_data, name, external_links)

        # Embedded links
        process_embedded_links(patterns, content_data, name, embedded_links)

    # Create alphanum lookups and identify dangling links
    alphanum_dict = create_alphanum(sorted(unique_linked_references))
    alphanum_filenames = create_alphanum(sorted(content.keys()))
    dangling_links = identify_dangling_links(unique_aliases, alphanum_dict, alphanum_filenames)

    return content_data, alphanum_dict, dangling_links


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
            first_char_id = item[:2] if len(item) > 1 else f"!{item[0]}"
            alphanum_dict[first_char_id].add(item)
        else:
            logging.error(f"Empty item: {item}")
    return alphanum_dict


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


def process_aliases(aliases):
    results = []
    current = []
    inside_brackets = False
    i = 0
    while i < len(aliases):
        # Detect the start of a bracketed section.
        if aliases[i : i + 2] == "[[":
            inside_brackets = True
            i += 2
            continue
        # Detect the end of a bracketed section.
        elif aliases[i : i + 2] == "]]":
            inside_brackets = False
            i += 2
            continue
        # If we hit a comma and are not inside brackets, split.
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

    # Append the last alias if exists.
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
