"""
File information for Logseq files.
"""

from dataclasses import dataclass, field


@dataclass
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float
    time_unmodified: float
    date_created: str
    date_modified: str


@dataclass
class SizeInfo:
    """File size information class."""

    size: int
    human_readable_size: str
    has_content: bool


@dataclass
class NamespaceInfo:
    """NamespaceInfo class."""

    parent_full: str
    parent: str
    parts: dict[str, int]
    root: str
    stem: str
    children: set[str] = field(default_factory=set)


@dataclass
class BulletInfo:
    """Bullet statistics class."""

    chars: int
    bullets: int
    empty_bullets: int
    char_per_bullet: float | None


@dataclass
class LogseqFileInfo:
    """LogseqFileInfo class."""

    timestamp: TimestampInfo
    size: SizeInfo
    namespace: NamespaceInfo
    bullet: BulletInfo
