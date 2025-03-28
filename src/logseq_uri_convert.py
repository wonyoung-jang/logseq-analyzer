"""
Convert a file URI to a Logseq URL and open it in the default web browser.
"""

from pathlib import Path
import webbrowser

from .config_loader import get_config

CONFIG = get_config()


def convert_uri_to_logseq_url(uri):
    """
    Convert a file URI to a Logseq URL.

    Args:
        uri (str): The file URI to convert.

    Returns:
        str: The Logseq URL corresponding to the given file URI.
    """

    len_uri = len(Path(uri).parts)
    len_graph_dir = len(Path(CONFIG.get("CONSTANTS", "GRAPH_DIR")).parts)
    target_index = len_uri - len_graph_dir
    target_segment = Path(uri).parts[target_index]
    prefix = f"file:///C:/Logseq/{target_segment}/"
    if not uri.startswith(prefix):
        return ""
    len_suffix = len(Path(uri).suffix)
    path_without_prefix = uri[len(prefix) : -(len_suffix)]
    path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
    encoded_path = path_with_slashes
    target_segment = target_segment[:-1]
    return f"logseq://graph/Logseq?{target_segment}={encoded_path}"


def open_logseq_url_in_graph(logseq_url):
    """
    Open the Logseq URL in the default web browser.

    Args:
        logseq_url (str): The Logseq URL to open.
    """
    webbrowser.open(logseq_url)
