import logging
from pathlib import Path
from typing import Dict, Pattern, Set, Any, Tuple, List, Optional

from src.filedata import extract_file_metadata, read_file_content
from src.contentdata import process_content_data
from src.summarydata import process_summary_data


class LogseqFile:
    """
    Represents a Logseq file and encapsulates its metadata, content, and analysis data.
    """

    def __init__(self, file_path: Path, patterns: Dict[str, Pattern], built_in_properties: Set[str]):
        """
        Initializes a LogseqFile object.

        Args:
            file_path (Path): Path to the Logseq file.
            patterns (Dict[str, Pattern]): Dictionary of compiled regex patterns.
            built_in_properties (Set[str]): Set of built-in properties.
        """
        self.file_path = file_path
        self.metadata: Dict[str, Any] = {}
        self.content: Optional[str] = None
        self.content_data: Dict[str, Any] = {}
        self.summary_data: Dict[str, Any] = {}
