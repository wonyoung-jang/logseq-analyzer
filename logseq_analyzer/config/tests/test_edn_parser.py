"""
Tests for LogseqConfigEDN.
"""

import pytest

from ..edn_parser import loads, tokenize


def test_tokenize_skips_comments_and_commas():
    """Test that tokenize skips comments and commas."""
    edn = "1, 2 ; comment\n 3"
    tokens = list(tokenize(edn))
    assert tokens == ["1", "2", "3"]


@pytest.mark.parametrize(
    "edn, expected",
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
def test_simple_values(edn, expected):
    """Test that simple values are parsed correctly."""
    assert loads(edn) == expected


@pytest.mark.parametrize(
    "edn, expected",
    [
        ("[1 2 3]", [1, 2, 3]),
        ("(4 5 6)", [4, 5, 6]),
        ("#{7 8 9}", {7, 8, 9}),
        ("{:a 1 :b 2}", {":a": 1, ":b": 2}),
    ],
)
def test_collections(edn, expected):
    """Test that collections are parsed correctly."""
    assert loads(edn) == expected


def test_nested_structures():
    """Test that nested structures are parsed correctly."""
    edn = "{:a [1 (2 3) #{4}] :b {:c 5}}"
    result = loads(edn)
    assert result[":a"] == [1, [2, 3], {4}]
    assert result[":b"] == {":c": 5}


def test_unhashable_keys_in_map():
    """Test that unhashable keys in a map raise an error."""
    edn = '{[1 2] "value"}'
    result = loads(edn)
    # The list [1,2] should be converted to tuple (1,2) for hashing
    assert list(result.keys()) == [(1, 2)]
    assert result[(1, 2)] == "value"


def test_map_key_map():
    """Test that a map with a map as a key is parsed correctly."""
    edn = "{{:x 10} :val}"
    result = loads(edn)
    # The map {:x 10} should become a frozenset of its items as the key
    key = frozenset({(":x", 10)})
    assert key in result
    assert result[key] == ":val"


def test_unexpected_end():
    """Test that an unexpected end of input raises an error."""
    with pytest.raises(ValueError, match="Unexpected end of EDN input"):
        loads("")


def test_extra_data():
    """Test that extra data after a valid EDN structure raises an error."""
    with pytest.raises(ValueError, match="Unexpected extra EDN data: 2"):
        loads("1 2")


def test_invalid_number_as_symbol():
    """Test that invalid numbers are parsed as symbols."""
    # Tokens that look like invalid numbers should be parsed as symbols
    assert loads("1.2.3") == "1.2.3"


def test_string_with_spaces_and_commas():
    """Test that strings with spaces and commas are parsed correctly."""
    edn = '"a, b, c"'
    tokens = list(tokenize(edn))
    assert tokens == ['"a, b, c"']
    assert loads(edn) == "a, b, c"
