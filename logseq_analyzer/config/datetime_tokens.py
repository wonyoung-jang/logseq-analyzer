"""
Logseq DateTime Tokens Module
"""

import logging
import re

logger = logging.getLogger(__name__)

__all__ = ["get_token_map", "compile_token_pattern", "convert_cljs_date_to_py"]


def get_token_map() -> dict[str, str]:
    """
    Get the date token map.
    """
    return {
        "yyyy": "%Y",
        "xxxx": "%Y",
        "yy": "%y",
        "xx": "%y",
        "MMMM": "%B",
        "MMM": "%b",
        "MM": "%m",
        "M": "%#m",
        "dd": "%d",
        "d": "%#d",
        "D": "%j",
        "EEEE": "%A",
        "EEE": "%a",
        "EE": "%a",
        "E": "%a",
        "e": "%u",
        "HH": "%H",
        "H": "%H",
        "hh": "%I",
        "h": "%I",
        "mm": "%M",
        "m": "%#M",
        "ss": "%S",
        "s": "%#S",
        "SSS": "%f",
        "a": "%p",
        "A": "%p",
        "Z": "%z",
        "ZZ": "%z",
    }


def compile_token_pattern(token_map: dict[str, str]) -> re.Pattern:
    """
    Set the regex pattern for date tokens.
    """
    tokenkeys = token_map.keys()
    pattern = "|".join(re.escape(k) for k in sorted(tokenkeys, key=len, reverse=True))
    return re.compile(pattern)


def convert_cljs_date_to_py(cljs_format: str, token_map: dict[str, str], token_pattern: re.Pattern) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.
    """
    cljs_format = cljs_format.replace("o", "")

    def replace_token(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return token_map.get(token, token)

    return token_pattern.sub(replace_token, cljs_format)
