"""SQLite-backed cache replacing shelve."""

import json
import logging
import sqlite3
import zlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.domain.model import LogseqFile

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

logger = logging.getLogger(__name__)

_SCHEMA = """\
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files (
    path          TEXT    PRIMARY KEY,
    mtime         REAL    NOT NULL,
    name          TEXT    NOT NULL,
    filetype      TEXT    NOT NULL,
    has_content   INTEGER NOT NULL,
    has_backlinks INTEGER NOT NULL,
    ns_root       TEXT    NOT NULL,
    ns_parent     TEXT    NOT NULL,
    ns_part       TEXT    NOT NULL,
    data          BLOB    NOT NULL
);
"""
_INSERT_FILE = """\
INSERT OR REPLACE INTO files
(path, mtime, name, filetype, has_content, has_backlinks, ns_root, ns_parent, ns_part, data)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _serialize(f: LogseqFile) -> tuple:
    return (
        str(f.path),
        f.path.stat().st_mtime,
        f.name,
        f.filetype,
        int(f.has_content),
        int(f.has_backlinks),
        f.ns_root,
        f.ns_parent,
        json.dumps(f.ns_part),
        zlib.compress(json.dumps(f.data, default=list).encode()),
    )


def _deserialize(row: sqlite3.Row) -> LogseqFile:
    return LogseqFile(
        path=Path(row["path"]),
        name=row["name"],
        filetype=row["filetype"],
        has_content=bool(row["has_content"]),
        has_backlinks=bool(row["has_backlinks"]),
        ns_root=row["ns_root"],
        ns_parent=row["ns_parent"],
        ns_part=json.loads(row["ns_part"]),
        data=json.loads(zlib.decompress(row["data"])),
    )


@dataclass(slots=True)
class Cache:
    """SQLite-backed cache for LogseqFile index and modification times."""

    path: Path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.executescript(_SCHEMA)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def save(self, index: set[LogseqFile]) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM files")
            con.executemany(_INSERT_FILE, (_serialize(f) for f in index))

    def reset(self) -> set:
        with self._connect() as con:
            con.execute("DELETE FROM files")
        return set()

    def load(self) -> set[LogseqFile]:
        with self._connect() as con:
            rows = con.execute("SELECT * FROM files").fetchall()
        return {_deserialize(r) for r in rows if Path(r["path"]).exists()}

    def get_modified(self, files: Iterator[Path]) -> Iterable[Path]:
        with self._connect() as con:
            existing: dict[str, float] = {
                r["path"]: r["mtime"] for r in con.execute("SELECT path, mtime FROM files").fetchall()
            }
        return [p for p in files if p.stat().st_mtime != existing.get(str(p))]
