"""
Process content data for Logseq.
"""

from typing import List, Pattern, Tuple

from ._global_objects import PATTERNS, ANALYZER_CONFIG


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def split_builtin_user_properties(properties: list) -> Tuple[list, list]:
    """Helper function to split properties into built-in and user-defined."""
    builtin_props = [prop for prop in properties if prop in ANALYZER_CONFIG.built_in_properties]
    user_props = [prop for prop in properties if prop not in ANALYZER_CONFIG.built_in_properties]
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


def process_external_links(
    external_links: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """Process external links and categorize them."""
    internet = []
    alias = []
    if external_links:
        for _ in range(len(external_links)):
            link = external_links[-1]
            if PATTERNS.ext_links["external_link_internet"].match(link):
                internet.append(link)
                external_links.pop()
                continue

            if PATTERNS.ext_links["external_link_alias"].match(link):
                alias.append(link)
                external_links.pop()
                continue
    return external_links, internet, alias


def process_embedded_links(
    embedded_links: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """Process embedded links and categorize them."""
    internet = []
    asset = []
    if embedded_links:
        for _ in range(len(embedded_links)):
            link = embedded_links[-1]
            if PATTERNS.emb_links["embedded_link_internet"].match(link):
                internet.append(link)
                embedded_links.pop()
                continue

            if PATTERNS.emb_links["embedded_link_asset"].match(link):
                asset.append(link)
                embedded_links.pop()
                continue
    return embedded_links, internet, asset
