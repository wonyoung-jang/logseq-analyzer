"""
Process content data for Logseq.
"""

from collections import defaultdict
from typing import Any, Dict, List, Pattern, Set, Tuple
import logging

from ._global_objects import PATTERNS, ANALYZER_CONFIG


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def create_alphanum(list_lookup: Set[str]) -> Dict[str, Set[str]]:
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
    built_in = ANALYZER_CONFIG.built_in_properties
    builtin_props = [prop for prop in properties if prop in built_in]
    user_props = [prop for prop in properties if prop not in built_in]
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


def post_processing_content_namespaces(
    content_data: Dict[str, Any], name: str, data: Dict[str, Any], ns_sep: str
) -> Dict[str, Any]:
    """
    Post-process namespaces in the content data.
    """
    namespace_parts_list = name.split(ns_sep)
    namespace_level = data["namespace_level"]
    ns_root = data["namespace_root"]
    ns_parent = ns_sep.join(namespace_parts_list[:-1])

    if ns_root in content_data:
        root = content_data[ns_root]
        root_level = root.get("namespace_level", 0)
        root["namespace_level"] = max(1, root_level)
        root.setdefault("namespace_children", set()).add(name)
        root["namespace_size"] = len(root["namespace_children"])

    if namespace_level > 2:
        if ns_parent in content_data:
            parent = content_data[ns_parent]
            parent_level = parent.get("namespace_level", 0)
            direct_level = namespace_level - 1
            parent["namespace_level"] = max(direct_level, parent_level)
            parent.setdefault("namespace_children", set()).add(name)
            parent["namespace_size"] = len(parent["namespace_children"])

    return content_data
