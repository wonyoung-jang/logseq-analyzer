"""
Process content data for Logseq.
"""

from collections import defaultdict
from typing import Dict, List, Pattern, Set, Tuple
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


def process_external_links(links: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Process external links and categorize them."""
    internet = []
    alias = []
    if links:
        for _ in range(len(links)):
            link = links[-1]
            if PATTERNS.content["external_link_internet"].match(link):
                internet.append(link)
                links.pop()
                continue

            if PATTERNS.content["external_link_alias"].match(link):
                alias.append(link)
                links.pop()
                continue

    return links, internet, alias


def process_embedded_links(links: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Process embedded links and categorize them."""
    internet = []
    asset = []
    if links:
        for _ in range(len(links)):
            link = links[-1]
            if PATTERNS.content["embedded_link_internet"].match(link):
                internet.append(link)
                links.pop()
                continue

            if PATTERNS.content["embedded_link_asset"].match(link):
                asset.append(link)
                links.pop()
                continue

    return links, internet, asset
