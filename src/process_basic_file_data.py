"""
Process basic file data for Logseq files.
"""

from urllib.parse import unquote

from ._global_objects import ANALYZER_CONFIG
from .logseq_journals import process_logseq_journal_key


def process_logseq_filename_key(key: str, parent: str) -> str:
    """
    Process the key name by removing the parent name and formatting it.

    For 'journals' parent, it formats the key as 'day-month-year dayOfWeek'.
    For other parents, it unquotes URL-encoded characters and replaces '___' with '/'.

    Args:
        key (str): The key name (filename stem).
        parent (str): The parent directory name.

    Returns:
        str: Processed key name.
    """
    ns_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")
    ns_file_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP")
    dir_journals = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_JOURNALS")

    if key.endswith(ns_file_sep):
        key = key.rstrip(ns_file_sep)

    if parent == dir_journals:
        return process_logseq_journal_key(key)

    return unquote(key).replace(ns_file_sep, ns_sep).lower()
