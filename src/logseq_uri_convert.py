import webbrowser


def convert_uri_to_logseq_url(uri):
    """
    Convert a file URI to a Logseq URL.

    Args:
        uri (str): The file URI to convert.

    Returns:
        str: The Logseq URL corresponding to the given file URI.
    """
    prefix = "file:///C:/Logseq/pages/"
    if not uri.startswith(prefix):
        return ""

    path_without_prefix = uri[len(prefix) :]
    if path_without_prefix.endswith(".md"):
        path_without_prefix = path_without_prefix[:-3]

    path_with_slashes = path_without_prefix.replace("___", "/")

    segments = path_with_slashes.split("/")
    encoded_path = "%2F".join(segments)

    return f"logseq://graph/Logseq?page={encoded_path}"


def open_logseq_url_in_graph(logseq_url):
    """
    Open the Logseq URL in the default web browser.

    Args:
        logseq_url (str): The Logseq URL to open.
    """
    webbrowser.open(logseq_url)
