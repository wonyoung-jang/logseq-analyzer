import pytest

from logseq_analyzer.utils.helpers import format_bytes


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1.00 KiB"),
        (2048, "2.00 KiB"),
        (1048576, "1.00 MiB"),
        (1073741824, "1.00 GiB"),
        (1099511627776, "1.00 TiB"),
        (1125899906842624, "1.00 PiB"),
    ],
)
def test_format_bytes_iec(value, expected) -> None:
    """Test the format_bytes function with IEC units."""
    assert format_bytes(value, "iec") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1.02 kB"),
        (1000, "1.00 kB"),
        (2000, "2.00 kB"),
        (1000000, "1.00 MB"),
        (1000000000, "1.00 GB"),
        (1000000000000, "1.00 TB"),
        (1000000000000000, "1.00 PB"),
    ],
)
def test_format_bytes_si(value, expected) -> None:
    """Test the format_bytes function with SI units."""
    assert format_bytes(value, "si") == expected
