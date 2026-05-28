"""SQLite-backed cache replacing shelve."""

import json
import sqlite3
import zlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.domain.model import LogseqNode

if TYPE_CHECKING:
    from collections.abc import Iterator


_SCHEMA = """\
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files (
    path            TEXT    PRIMARY KEY,
    name            TEXT    NOT NULL,
    filetype        TEXT    NOT NULL,
    nodetype        TEXT    NOT NULL,
    ns_root         TEXT    NOT NULL,
    ns_parent       TEXT    NOT NULL,
    has_content     INTEGER NOT NULL,
    has_backlinks   INTEGER NOT NULL,
    backlinked      INTEGER NOT NULL,
    backlinked_ns_only  INTEGER NOT NULL,
    is_ns           INTEGER NOT NULL,
    mtime           REAL    NOT NULL,
    data            BLOB    NOT NULL
);
"""
_INSERT_FILE = """\
INSERT OR REPLACE INTO files
(
    path,
    name,
    filetype,
    nodetype,
    ns_root,
    ns_parent,
    has_content,
    has_backlinks,
    backlinked,
    backlinked_ns_only,
    is_ns,
    mtime,
    data
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _serialize(node: LogseqNode) -> tuple:
    return (
        str(node.path),
        node.name,
        node.filetype,
        node.nodetype,
        node.ns_root,
        node.ns_parent,
        int(node.has_content),
        int(node.has_backlinks),
        int(node.backlinked),
        int(node.backlinked_ns_only),
        int(node.is_ns),
        node.path.stat().st_mtime,
        zlib.compress(json.dumps(node.data, default=list).encode()),
    )


def _deserialize(row: sqlite3.Row) -> LogseqNode:
    return LogseqNode(
        path=Path(row["path"]),
        name=row["name"],
        filetype=row["filetype"],
        nodetype=row["nodetype"],
        ns_root=row["ns_root"],
        ns_parent=row["ns_parent"],
        has_content=bool(row["has_content"]),
        has_backlinks=bool(row["has_backlinks"]),
        backlinked=bool(row["backlinked"]),
        backlinked_ns_only=bool(row["backlinked_ns_only"]),
        is_ns=bool(row["is_ns"]),
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

    def save(self, index: set[LogseqNode]) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM files")
            con.executemany(_INSERT_FILE, (_serialize(f) for f in index))

    def reset(self) -> set:
        with self._connect() as con:
            con.execute("DELETE FROM files")
        return set()

    def load(self) -> set[LogseqNode]:
        with self._connect() as con:
            rows = con.execute("SELECT * FROM files").fetchall()
        return {_deserialize(r) for r in rows if Path(r["path"]).exists()}

    def get(self, attr: str, cond_attr: str, value: object) -> list[object]:
        with self._connect() as con:
            rows = con.execute(f"SELECT {attr} FROM files WHERE {cond_attr} = ?", (value,)).fetchall()
        return [r[attr] for r in rows]

    def get_modified_path(self, files: Iterator[Path]) -> Iterator[Path]:
        with self._connect() as con:
            existing: dict[str, float] = {
                r["path"]: r["mtime"] for r in con.execute("SELECT path, mtime FROM files").fetchall()
            }
        yield from (p for p in files if p.exists() and p.stat().st_mtime != existing.get(str(p)))
