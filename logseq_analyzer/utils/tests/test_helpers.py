"""
Unit tests for helpers.py module.
"""

import os
import re
import logging
import pytest
from pathlib import Path

from ..helpers import (
    iter_files,
    get_or_create_file_or_dir,
    find_all_lower,
    process_aliases,
)


def test_iter_files(tmp_path, caplog, monkeypatch):
    monkeypatch.setattr(Path, "walk", os.walk)
    # Create directory tree:
    # tmp/root/
    #   dirA/target1/file1.txt
    #        /target2/file2.txt
    #        /other/file3.txt
    root = tmp_path / "root"
    target1 = root / "target1"
    target2 = root / "target2"
    other = root / "other"
    for d in (target1, target2, other):
        d.mkdir(parents=True)

    f1 = target1 / "file1.txt"
    f1.write_text("hello")
    f2 = target2 / "file2.txt"
    f2.write_text("world")
    f3 = other / "file3.txt"
    f3.write_text("skip")

    caplog.set_level(logging.INFO)
    got = list(iter_files(root, {"target1", "target2"}))

    assert set(got) == {f1, f2}
    assert any("Skipping directory" in rec.getMessage() for rec in caplog.records)


def test_get_or_create_exists(tmp_path):
    p = tmp_path / "exists"
    p.mkdir()
    assert get_or_create_file_or_dir(p) == p


def test_get_or_create_new(tmp_path, caplog):
    p = tmp_path / "newdir"
    assert not p.exists()
    caplog.set_level(logging.INFO)

    ret = get_or_create_file_or_dir(p)
    assert ret == p
    assert p.exists()
    msgs = [rec.getMessage() for rec in caplog.records]
    assert any("Creating path" in m for m in msgs)
    assert any("Created path" in m for m in msgs)


def test_get_or_create_permission_error(tmp_path, monkeypatch, caplog):
    p = tmp_path / "perm"

    def fake_mkdir(*args, **kwargs):
        raise PermissionError

    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    caplog.set_level(logging.ERROR)
    ret = get_or_create_file_or_dir(p)
    assert ret is None
    assert any("Permission denied" in rec.getMessage() for rec in caplog.records)


def test_get_or_create_os_error(tmp_path, monkeypatch, caplog):
    p = tmp_path / "oserr"

    def fake_mkdir(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    caplog.set_level(logging.ERROR)
    ret = get_or_create_file_or_dir(p)
    assert ret is None
    assert any("Error creating path" in rec.getMessage() for rec in caplog.records)


def test_find_all_lower_simple():
    text = "Foo BAR baz"
    pattern = re.compile(r"\b\w+\b")
    got = find_all_lower(pattern, text)
    assert got == ["foo", "bar", "baz"]


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("a,b,c", ["a", "b", "c"]),
        ("  A  ,  B  ", ["a", "b"]),
        ("[[a,b]],c", ["a,b", "c"]),
        ("alias1 [[alias2,alias3]], alias4", ["alias1 alias2,alias3", "alias4"]),
        ("x,,y,", ["x", "y"]),
    ],
)
def test_process_aliases_various(input_str, expected):
    assert process_aliases(input_str) == expected
