"""
Convert a file URI to a Logseq URL and open it in the default web browser.
"""

import webbrowser


def open_logseq_url_in_graph(logseq_url):
    """
    Open the Logseq URL in the default web browser.

    Args:
        logseq_url (str): The Logseq URL to open.
    """
    webbrowser.open(logseq_url)
