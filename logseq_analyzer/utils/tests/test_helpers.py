"""
Unit tests for helpers.py module.
"""

import logging
import pytest

from ..helpers import (
    iter_files,
    process_aliases,
    sort_dict_by_value,
)


def test_iter_files(tmp_path, caplog):
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
    f_org = target1 / "file1.org"
    f_org.write_text("org-mode")

    caplog.set_level(logging.INFO)
    got = list(iter_files(root, {"target1", "target2"}))

    assert set(got) == {f1, f2}
    assert any("Skipping directory" in rec.getMessage() for rec in caplog.records)


def test_sort_dict_by_value():
    d = {"a": 3, "b": 2, "c": 1}
    sorted_dict = sort_dict_by_value(d)
    assert list(sorted_dict.keys()) == ["a", "b", "c"]
    assert list(sorted_dict.values()) == [3, 2, 1]

    sorted_dict_desc = sort_dict_by_value(d, reverse=False)
    assert list(sorted_dict_desc.keys()) == ["c", "b", "a"]
    assert list(sorted_dict_desc.values()) == [1, 2, 3]

    nested_dict = {"a": {"value": 3}, "b": {"value": 2}, "c": {"value": 1}}
    sorted_nested_dict = sort_dict_by_value(nested_dict, value="value")
    assert list(sorted_nested_dict.keys()) == ["a", "b", "c"]
    assert list(sorted_nested_dict.values()) == [{"value": 3}, {"value": 2}, {"value": 1}]


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
    assert list(process_aliases(input_str)) == expected
