"""
File information for Logseq files.
"""

from dataclasses import dataclass, field

from ..utils.enums import Node


@dataclass(slots=True)
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = field(default=False, init=False)
    backlinked: bool = field(default=False, init=False)
    backlinked_ns_only: bool = field(default=False, init=False)
    node_type: str = field(default=Node.OTHER, init=False)

    def check_backlinked(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked and update the node state."""
        if not self.backlinked:
            self.backlinked = NodeType._check_for_backlinks(name, lookup)

    def check_backlinked_ns_only(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked only in its namespace and update the node state."""
        if not self.backlinked_ns_only and NodeType._check_for_backlinks(name, lookup):
            self.backlinked_ns_only = True
            self.backlinked = False

    @staticmethod
    def _check_for_backlinks(name: str, lookup: set[str]) -> bool:
        """Helper function to check if a file is backlinked."""
        try:
            lookup.remove(name)
            return True
        except KeyError:
            return False

    def determine_node_type(self, has_content: bool) -> None:
        """Helper function to determine node type based on summary data."""
        has_backlinks = self.has_backlinks
        backlinked = self.backlinked
        backlinked_ns_only = self.backlinked_ns_only
        match (has_content, has_backlinks, backlinked, backlinked_ns_only):
            case (True, True, True, True):
                n = Node.BRANCH
            case (True, True, True, False):
                n = Node.BRANCH
            case (True, True, False, True):
                n = Node.BRANCH
            case (True, True, False, False):
                n = Node.ROOT
            case (True, False, True, True):
                n = Node.LEAF
            case (True, False, True, False):
                n = Node.LEAF
            case (True, False, False, True):
                n = Node.ORPHAN_NAMESPACE
            case (True, False, False, False):
                n = Node.ORPHAN_GRAPH
            case (False, False, True, True):
                n = Node.LEAF
            case (False, False, True, False):
                n = Node.LEAF
            case (False, False, False, True):
                n = Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False, False):
                n = Node.ORPHAN_TRUE
        self.node_type = n


@dataclass(slots=True)
class JournalFormats:
    """Formats for Logseq journal files and pages."""

    file: str
    page: str
    page_title: str


@dataclass(slots=True)
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float
    time_unmodified: float
    date_created: str
    date_modified: str


@dataclass(slots=True)
class SizeInfo:
    """File size information class."""

    size: int
    human_readable_size: str
    has_content: bool


@dataclass(slots=True)
class NamespaceInfo:
    """NamespaceInfo class."""

    parent_full: str
    parent: str
    parts: dict[str, int]
    root: str
    stem: str
    is_namespace: bool
    children: set[str] = field(default_factory=set)


@dataclass(slots=True)
class BulletInfo:
    """Bullet statistics class."""

    chars: int
    bullets: int
    empty_bullets: int
    char_per_bullet: float | None


@dataclass(slots=True)
class LogseqFileInfo:
    """LogseqFileInfo class."""

    timestamp: TimestampInfo
    size: SizeInfo
    namespace: NamespaceInfo
    bullet: BulletInfo
