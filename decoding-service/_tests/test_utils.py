from __future__ import annotations

import pytest

import utils
from fixtures import P5_DYNAMIC
from models import DecodeErrorCode

# Verified CRC16-CCITT known-answer vectors. The trailing 4 hex chars of each
# string are the expected CRC of the preceding bytes (which include the literal
# "6304" tag+length bytes). p1's expected CRC was recomputed (B659) because the
# reviewer-supplied value (325F) does not match the supplied payload under the
# standard algorithm; see the implementation report.
VERIFIED_VECTORS = [
    (
        "00020101021226580014br.gov.bcb.pix013671d6c6e1-64ea-4a11-9560-a10870c40ca2"
        "520400005303986540512.305802BR5912COMPANY1DATA62150511NFeTEST00016304A5C7",
        "A5C7",
    ),
    (
        "00020101021226580014br.gov.bcb.pix013671d6c6e1-64ea-4a11-9560-a10870c40ca2"
        "520400005303986540512.305802BR5912COMPANY1DATA62070503***6304F1E4",
        "F1E4",
    ),
    (
        "00020101021226580014br.gov.bcb.pix013671d6c6e1-64ea-4a11-9560-a10870c40ca2"
        "5204000053039865802BR5912COMPANY1DATA62070503***630490CA",
        "90CA",
    ),
    (
        "00020101021126690014br.gov.bcb.pix0114+55279957710220229Doacao Livre / "
        "QRCODE - PYPIX52040000530398654045.005802BR5905Teste6009Cariacica"
        "61082914861362130509PIXMP00016304B659",
        "B659",
    ),
    (
        "00020101021126910014br.gov.bcb.pix0136b5fe1edc-d108-410f-b966-eccaaca75e4f"
        "0229Doacao Livre / QRCODE - PYPIX52040000530398654030.05802BR5921Cleiton "
        "Leonel Creton6009Cariacica62070503***63049182",
        "9182",
    ),
    (
        P5_DYNAMIC,
        "2D75",
    ),
]


def _tlv(tag: str, value: str) -> str:
    return tag + f"{len(value):02d}" + value


def _crc(crc_hex: str) -> str:
    return "6304" + crc_hex


# --- CRC16 ----------------------------------------------------------------


@pytest.mark.parametrize(("payload", "expected"), VERIFIED_VECTORS)
def test_crc16_ccitt_matches_verified_vectors(payload, expected):
    assert f"{utils.crc16_ccitt(payload[:-4].encode('ascii')):04X}" == expected


def test_crc16_scope_excludes_only_final_four_hex_chars():
    payload, expected = VERIFIED_VECTORS[0]
    computed = f"{utils.crc16_ccitt(payload[:-4].encode('ascii')):04X}"
    assert computed == expected
    assert payload[-4:] == expected


def test_crc16_is_deterministic_and_sensitive_to_input():
    a = utils.crc16_ccitt(b"hello")
    assert a == utils.crc16_ccitt(b"hello")
    assert a != utils.crc16_ccitt(b"hellp")


# --- TLV parsing (raw ASCII: 2-digit tag, 2-digit DECIMAL length, value) ---


def test_parse_emv_tlv_parses_flat_raw_chain():
    parsed = utils.parse_emv_tlv(_tlv("59", "COMPANY1DATA") + _tlv("60", "SAO PAULO"))
    assert parsed == [("59", "COMPANY1DATA"), ("60", "SAO PAULO")]


def test_parse_emv_tlv_parses_reference_form():
    assert utils.parse_emv_tlv("5912COMPANY1DATA") == [("59", "COMPANY1DATA")]
    assert utils.parse_emv_tlv("62070503***") == [("62", "0503***")]


def test_parse_emv_tlv_value_remains_opaque_for_sub_tlv_tag_26():
    sub = "0014" + "br.gov.bcb.pix" + "0136" + "123e4567-e12b-12d1-a456-426655440000"
    payload = _tlv("26", sub) + _crc("ABCD")
    parsed = utils.parse_emv_tlv(payload)
    assert parsed[0] == ("26", sub)
    assert parsed[1] == ("63", "ABCD")


def test_parse_emv_tlv_rejects_non_digit_tag():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("5A02ab")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_non_digit_length():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("591Xa")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_fullwidth_digit_tag():
    # U+FF15 is a full-width "5"; str.isdigit() accepts it but the tag must be
    # exactly ASCII [0-9].
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("５902ab")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_fullwidth_digit_length():
    # U+FF12 is a full-width "2"; must be ASCII [0-9] in the length field.
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("590２ab")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_truncated_tag_or_length():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("59")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_length_overrun():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv("5914" + "short")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_duplicate_known_tag():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("59", "A") + _tlv("59", "B"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_allows_repeated_unknown_tag():
    # Ascending order (59 -> 99 -> 99) so the canonical-ordering rule holds.
    parsed = utils.parse_emv_tlv(_tlv("59", "A") + _tlv("99", "ab") + _tlv("99", "cd"))
    assert ("99", "ab") in parsed
    assert ("99", "cd") in parsed


def test_parse_emv_tlv_rejects_descending_top_level_order():
    # Canonical EMV ordering: tag 60 after 59 would be fine, but 59 after 60 is
    # strictly descending -> malformed.
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("60", "A") + _tlv("59", "B"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_allows_equal_unknown_tags_out_of_order_is_unknown_only():
    # Equal numeric tags are allowed (unknown duplicate); only strict descent
    # is malformed. Unknown tags need not be distinct.
    parsed = utils.parse_emv_tlv(_tlv("59", "A") + _tlv("99", "ab") + _tlv("99", "cd"))
    assert len([pair for pair in parsed if pair[0] == "99"]) == 2


def test_parse_emv_tlv_rejects_descending_unknown_tag_before_known():
    # Ordinary descending order (unknown 99 before known 59) is still malformed;
    # only the final CRC tag is exempt from the ordering comparison.
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("99", "ab") + _tlv("59", "B"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_allows_unknown_tag_above_crc_before_crc():
    # The final CRC tag (63) is exempt from numeric ordering, so an unknown tag
    # numerically above it (64) may legally precede it.
    parsed = utils.parse_emv_tlv(_tlv("59", "A") + _tlv("64", "ab") + _crc("F1E4"))
    assert ("64", "ab") in parsed
    assert parsed[-1] == ("63", "F1E4")


def test_parse_emv_tlv_rejects_descending_nested_order():
    # The same ordering rule applies at a nested (26/62) level via known_tags.
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(
            _tlv("01", "52998224725") + _tlv("00", "br.gov.bcb.pix"),
            known_tags=utils.constants.KNOWN_SUB_TAGS_26,
            crc_field=False,
        )
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


# --- CRC field finality and form -------------------------------------------


def test_parse_emv_tlv_accepts_final_crc_field():
    parsed = utils.parse_emv_tlv(_tlv("59", "A") + _crc("F1E4"))
    assert parsed[-1] == ("63", "F1E4")


def test_parse_emv_tlv_rejects_non_final_crc_field():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_crc("F1E4") + _tlv("59", "A"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_lowercase_crc():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("59", "A") + "6304f1e4")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_truncated_crc():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("59", "A") + "6304F1E")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_trailing_data_after_crc():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("59", "A") + "6304F1E4X")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_parse_emv_tlv_rejects_crc_field_with_wrong_length():
    with pytest.raises(utils.DecodeError) as excinfo:
        utils.parse_emv_tlv(_tlv("59", "A") + "6305" + "F1E40")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV
