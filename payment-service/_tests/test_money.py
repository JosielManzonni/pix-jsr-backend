from __future__ import annotations

from decimal import Decimal

import pytest

from money import InvalidAmountError, parse_amount


def test_parse_valid_amount():
    assert parse_amount("1234.56") == Decimal("1234.56")


def test_parse_preserves_precision_exactly():
    value = parse_amount("1234.56")
    assert value == Decimal("1234.56")
    assert value.as_tuple().exponent == -2
    assert str(value) == "1234.56"


def test_parse_accepts_upper_bound():
    assert parse_amount("9999999.99") == Decimal("9999999.99")


def test_parse_rejects_zero():
    with pytest.raises(InvalidAmountError):
        parse_amount("0.00")


def test_parse_accepts_smallest_positive():
    assert parse_amount("0.01") == Decimal("0.01")


def test_parse_rejects_above_max():
    with pytest.raises(InvalidAmountError):
        parse_amount("99999999.99")


def test_parse_rejects_negative():
    with pytest.raises(InvalidAmountError):
        parse_amount("-5.00")


def test_parse_rejects_single_decimal():
    with pytest.raises(InvalidAmountError):
        parse_amount("12.5")


def test_parse_rejects_three_decimals():
    with pytest.raises(InvalidAmountError):
        parse_amount("12.567")


def test_parse_rejects_no_decimals():
    with pytest.raises(InvalidAmountError):
        parse_amount("12")


def test_parse_rejects_non_string_inputs():
    for value in (1234.56, 1234, None, b"12.00"):
        with pytest.raises(InvalidAmountError):
            parse_amount(value)


def test_parse_rejects_empty_and_whitespace():
    for value in ("", "  12.00 "):
        with pytest.raises(InvalidAmountError):
            parse_amount(value)