"""Tests for LogseqConfigEDN."""

from typing import Any

import pytest

from logseq_analyzer.adapter.ednconfig import EDNParser, parse_edn, tokenize


def test_tokenize_skips_comments_and_commas() -> None:
    """Test that tokenize skips comments and commas."""
    edn = "1, 2 ; comment\n 3"
    tokens = list(tokenize(edn))
    assert tokens == ["1", "2", "3"]


@pytest.mark.parametrize(
    ("edn", "expected"),
    [
        ("42", 42),
        ("-7", -7),
        ("3.14", 3.14),
        ("6.022e23", 6.022e23),
        ("true", True),
        ("false", False),
        ("nil", None),
        ('"hello"', "hello"),
        (r'"a\nb"', "a\nb"),
        (":kw", ":kw"),
        ("foo", "foo"),
    ],
)
def test_simple_values(edn: str, expected: Any) -> None:
    """Test that simple values are parsed correctly."""
    assert parse_edn(edn) == expected


@pytest.mark.parametrize(
    ("edn", "expected"),
    [
        ("[1 2 3]", [1, 2, 3]),
        ("(4 5 6)", [4, 5, 6]),
        ("#{7 8 9}", {7, 8, 9}),
        ("{:a 1 :b 2}", {":a": 1, ":b": 2}),
    ],
)
def test_collections(edn: str, expected: Any) -> None:
    """Test that collections are parsed correctly."""
    assert parse_edn(edn) == expected


def test_nested_structures() -> None:
    """Test that nested structures are parsed correctly."""
    edn = "{:a [1 (2 3) #{4}] :b {:c 5}}"
    result = parse_edn(edn)
    assert type(result) is dict
    assert result[":a"] == [1, [2, 3], {4}]
    assert result[":b"] == {":c": 5}


def test_unhashable_keys_in_map() -> None:
    """Test that unhashable keys in a map raise an error."""
    edn = '{[1 2] "value"}'
    result = parse_edn(edn)
    # The list [1,2] should be converted to tuple (1,2) for hashing
    assert type(result) is dict
    assert list(result.keys()) == [(1, 2)]
    assert result[(1, 2)] == "value"


def test_parse_map_key_set() -> None:
    """Test that a map with a set as a key is parsed correctly."""
    edn = "{#{1 2} :val}"
    result = parse_edn(edn)
    # The set {1, 2} should become a frozenset of its items as the key
    key = frozenset({1, 2})
    assert type(result) is dict
    assert key in result
    assert result[key] == ":val"


def test_map_key_map() -> None:
    """Test that a map with a map as a key is parsed correctly."""
    edn = "{{:x 10} :val}"
    result = parse_edn(edn)
    # The map {:x 10} should become a frozenset of its items as the key
    key = frozenset({(":x", 10)})
    assert type(result) is dict
    assert key in result
    assert result[key] == ":val"


def test_unexpected_end() -> None:
    """Test that an unexpected end of input raises an error."""
    with pytest.raises(ValueError, match="Unexpected end of EDN input"):
        parse_edn("")


def test_extra_data() -> None:
    """Test that extra data after a valid EDN structure raises an error."""
    with pytest.raises(ValueError, match="Unexpected extra EDN data: 2"):
        parse_edn("1 2")


def test_invalid_number_as_symbol() -> None:
    """Test that invalid numbers are parsed as symbols."""
    # Tokens that look like invalid numbers should be parsed as symbols
    assert parse_edn("1.2.3") == "1.2.3"


def test_string_with_spaces_and_commas() -> None:
    """Test that strings with spaces and commas are parsed correctly."""
    edn = '"a, b, c"'
    tokens = list(tokenize(edn))
    assert tokens == ['"a, b, c"']
    assert parse_edn(edn) == "a, b, c"


def test_tokenize() -> None:
    """Test that the tokenize function works correctly."""
    edn = "1, 2 ; comment\n 3"
    tokens = tokenize(edn)
    edn_class = EDNParser(list(tokens))
    assert edn_class.tokens == ["1", "2", "3"]
