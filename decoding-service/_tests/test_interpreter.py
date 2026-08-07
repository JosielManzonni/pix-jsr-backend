from __future__ import annotations

import pytest

import interpreter
from fixtures import (
    P1_STATIC,
    P5_DYNAMIC,
    VALID_CNPJ,
    VALID_CPF,
    VALID_EVP,
    _build,
    _dynamic,
    _dynamic_parts,
    _dynamic_vector,
    _tlv,
)
from models import DecodeErrorCode, KeyType, Mode
from utils import DecodeError


def _tamper_crc(payload: str) -> str:
    last = payload[-1]
    return payload[:-1] + ("0" if last != "0" else "1")


# --- Valid vectors ---------------------------------------------------------


def test_v1_decodes_dynamic_instruction():
    payload = _dynamic_vector(txid="NFeTEST0001", amount="12.30")
    result = interpreter.interpret(payload)
    assert result.mode is Mode.dynamic
    assert result.txid == "NFeTEST0001"
    assert result.amount == "12.30"
    assert result.key_type is KeyType.evp
    assert result.mcc == "0000"
    assert result.merchant_name == "COMPANY1DATA"
    assert result.merchant_city == "SAO PAULO"
    assert result.crc_valid


def test_v2_decodes_dynamic_with_txid_stars():
    payload = _dynamic_vector(txid="***", amount="12.30")
    result = interpreter.interpret(payload)
    assert result.mode is Mode.dynamic
    assert result.txid == "***"
    assert result.amount == "12.30"


def test_v3_decodes_dynamic_without_amount():
    payload = _dynamic_vector(txid="***", amount=None)
    result = interpreter.interpret(payload)
    assert result.mode is Mode.dynamic
    assert result.amount is None


def test_p1_decodes_static_phone_key():
    result = interpreter.interpret(P1_STATIC)
    assert result.mode is Mode.static
    assert result.key_type is KeyType.phone
    assert result.txid == "PIXMP0001"
    assert result.description == "Doacao Livre / QRCODE - PYPIX"
    assert result.mcc == "0000"
    assert result.amount == "5.00"


def test_p2_decodes_static_evp_key():
    payload = _dynamic(
        pim="11",
        key="b5fe1edc-d108-410f-b966-eccaaca75e4f",
        amount="0.00",
        txid="***",
    )
    result = interpreter.interpret(payload)
    assert result.mode is Mode.static
    assert result.key_type is KeyType.evp
    assert result.amount == "0.00"
    assert result.txid == "***"


def test_static_without_pim_is_static_and_drops_txid():
    payload = _dynamic(pim=None, txid=None)
    result = interpreter.interpret(payload)
    assert result.mode is Mode.static
    assert result.txid is None


# --- Dynamic location (Finding 1) -----------------------------------------


def test_dynamic_location_decodes():
    result = interpreter.interpret(
        _dynamic(key=None, location="bitsorbyte.com.br/login")
    )
    assert result.mode is Mode.dynamic
    assert result.key is None
    assert result.key_type is None
    assert result.location == "bitsorbyte.com.br/login"
    assert result.txid == "TXID123"


def test_p5_dynamic_location_vector_decodes():
    result = interpreter.interpret(P5_DYNAMIC)
    assert result.mode is Mode.dynamic
    assert result.key is None
    assert result.key_type is None
    assert result.location == "bitsorbyte.com.br/login"
    assert result.txid == "***"
    assert result.merchant_name == "TESOURO NACIONAL"


def test_dynamic_with_key_and_location_is_invalid():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=VALID_CPF, location="x"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_dynamic_with_neither_key_nor_location_is_missing():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=None, location=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_dynamic_with_empty_location_is_invalid():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=None, location=""))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_static_without_key_is_missing():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(pim="11", key=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_static_ignores_present_location_when_key_is_authoritative():
    result = interpreter.interpret(_dynamic(pim="11", key=VALID_CPF, location="ignored"))
    assert result.mode is Mode.static
    assert result.key == VALID_CPF
    assert result.location is None


def test_dynamic_location_with_description_decodes():
    result = interpreter.interpret(
        _dynamic(key=None, location="bitsorbyte.com.br/login", description="ref")
    )
    assert result.location == "bitsorbyte.com.br/login"
    assert result.description == "ref"


def test_unknown_tag_above_crc_before_crc_is_ignored():
    # Unknown tag "64" (numerically above the CRC tag 63) sits immediately
    # before the final CRC. It must be ignored, not rejected by the ordering
    # rule, which exempts the final CRC tag.
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12")
        + _tlv("26", _tlv("00", "br.gov.bcb.pix") + _tlv("01", VALID_CPF))
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "Merchant")
        + _tlv("60", "BRASILIA") + _tlv("62", _tlv("05", "TXID123"))
        + _tlv("64", "ab")
    )
    result = interpreter.interpret(payload)
    assert result.mode is Mode.dynamic
    assert result.key == VALID_CPF


# --- Key type detection (Finding 9 / 10) -----------------------------------


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (VALID_CPF, KeyType.cpf),
        (VALID_CNPJ, KeyType.cnpj),
        ("+5527995771022", KeyType.phone),
        ("contato@empresa.com.br", KeyType.email),
        ("b5fe1edc-d108-410f-b966-eccaaca75e4f", KeyType.evp),
    ],
)
def test_key_type_detection(key, expected):
    result = interpreter.interpret(_dynamic(key=key))
    assert result.key_type is expected


@pytest.mark.parametrize(
    "bad_key",
    [
        "12345678901",  # CPF shape but invalid check digits
        "12345678901234",  # CNPJ shape but invalid check digits
        "notakey!",  # no recognized shape
        "a@b@c.com",  # more than one '@'
        "contato@empresa",  # domain without a '.'
        "contato@",  # empty domain
        "00000000-0000-0000-0000-000000000000",  # UUID shape, version 0 (not 4)
    ],
)
def test_invalid_keys_are_rejected(bad_key):
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=bad_key))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_non_rfc_variant_uuid_is_rejected():
    # 'c' variant nibble -> RESERVED_MICROSOFT, not RFC_4122.
    key = "123e4567-e89b-12d1-c456-426655440000"
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=key))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_non_v4_uuid_is_rejected():
    # Valid RFC_4122 variant but version 1, not 4.
    key = "123e4567-e89b-12d1-a456-426655440000"
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=key))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_unrecognized_key_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key="notakey!"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_repeated_digit_cpf_is_rejected():
    # All-equal-digit CPFs pass the mod-11 check digits; they are not real keys.
    for key in ("00000000000", "11111111111"):
        with pytest.raises(DecodeError) as excinfo:
            interpreter.interpret(_dynamic(key=key))
        assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_repeated_digit_cnpj_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key="00000000000000"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


def test_compact_uuid_evp_is_rejected():
    # A compact (no-hyphen) UUID parses via uuid.UUID but is not the canonical
    # hyphenated Pix EVP form.
    key = VALID_EVP.replace("-", "")
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=key))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_KEY


# --- Validation error codes ------------------------------------------------


def test_tampered_crc_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_tamper_crc(_dynamic()))
    assert excinfo.value.code == DecodeErrorCode.DECODING_CRC_MISMATCH


def test_non_brl_currency_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(currency="840"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_UNSUPPORTED_CURRENCY


def test_missing_merchant_name_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(name=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_missing_currency_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(currency=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_missing_key_or_location_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(key=None, location=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_dynamic_without_txid_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(txid=None))
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_invalid_pim_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(pim="13"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_too_long_payload_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret("0" * 513)
    assert excinfo.value.code == DecodeErrorCode.DECODING_PAYLOAD_TOO_LONG


def test_empty_payload_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret("")
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_non_printable_value_is_rejected():
    payload = _dynamic(name="Mer\x7fchant")
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_CHARSET


def test_invalid_gui_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(gui="notpix"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


# --- Empty and overlength mandatory fields (Finding 2) ---------------------


def test_empty_merchant_name_is_invalid():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(name=""))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_empty_merchant_city_is_invalid():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(city=""))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_merchant_name_lengths_at_boundary_are_accepted():
    for size in (1, 25):
        result = interpreter.interpret(_dynamic(name="x" * size))
        assert result.merchant_name == "x" * size


def test_merchant_city_lengths_at_boundary_are_accepted():
    for size in (1, 15):
        result = interpreter.interpret(_dynamic(city="x" * size))
        assert result.merchant_city == "x" * size


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "x" * 26},
        {"city": "x" * 16},
    ],
)
def test_overlength_mandatory_fields_are_rejected(overrides):
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(**overrides))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


# --- MCC format (Finding 3) ------------------------------------------------


def test_mcc_0000_is_accepted():
    result = interpreter.interpret(_dynamic(mcc="0000"))
    assert result.mcc == "0000"


@pytest.mark.parametrize("mcc", ["12", "12AB", "12345", ""])
def test_invalid_mcc_is_rejected(mcc):
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(mcc=mcc))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


# --- Nested sub-TLV handling (Finding 4) -----------------------------------


def test_malformed_nested_length_in_26_is_rejected():
    sub26 = "00" + "99" + "br.gov"
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12") + _tlv("26", sub26)
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
        + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
    )
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_nested_out_of_order_sub_tags_is_rejected():
    # Sub-tags inside 26 must be non-descending: "01" before "00" is descending.
    sub26 = _tlv("01", VALID_CPF) + _tlv("00", "br.gov.bcb.pix")
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12") + _tlv("26", sub26)
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
        + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
    )
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_non_digit_nested_tag_is_rejected():
    sub26 = "0A" + "02" + "ab" + _tlv("01", VALID_CPF)
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12") + _tlv("26", sub26)
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
        + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
    )
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_duplicate_known_sub_tag_in_26_is_rejected():
    sub26 = (
        _tlv("00", "br.gov.bcb.pix")
        + _tlv("00", "br.gov.bcb.pix")
        + _tlv("01", VALID_CPF)
    )
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12") + _tlv("26", sub26)
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
        + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
    )
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_MALFORMED_TLV


def test_unknown_sub_tags_are_ignored():
    sub26 = (
        _tlv("00", "br.gov.bcb.pix")
        + _tlv("01", VALID_CPF)
        + _tlv("03", "ab")
    )
    payload = _build(
        _tlv("00", "01") + _tlv("01", "12") + _tlv("26", sub26)
        + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
        + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
    )
    result = interpreter.interpret(payload)
    assert result.key == VALID_CPF


# --- Precedence (Finding 6a) -----------------------------------------------


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        # malformed nested TLV + bad CRC -> parse (step 3) beats CRC (step 6)
        pytest.param(
            _build(
                _tlv("00", "01") + _tlv("01", "12") + _tlv("26", "0099br.gov")
                + _tlv("53", "986") + _tlv("58", "BR") + _tlv("59", "M")
                + _tlv("60", "C") + _tlv("62", _tlv("05", "TX"))
            ),
            DecodeErrorCode.DECODING_MALFORMED_TLV,
            id="malformed-nested-beats-crc",
        ),
        # invalid charset + missing CRC -> charset (step 4) beats missing 63
        # (step 5)
        pytest.param(
            _dynamic_parts(name="Caf\xe9"),
            DecodeErrorCode.DECODING_INVALID_CHARSET,
            id="charset-beats-missing-crc",
        ),
        # missing mandatory (no 59) + CRC mismatch -> CRC (step 6) beats
        # presence (step 7)
        pytest.param(
            _tamper_crc(_dynamic(name=None)),
            DecodeErrorCode.DECODING_CRC_MISMATCH,
            id="crc-beats-presence",
        ),
        # both key+location in dynamic -> INVALID_PAYLOAD (step 9)
        pytest.param(
            _dynamic(key=VALID_CPF, location="x"),
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            id="key-and-location",
        ),
    ],
)
def test_validation_precedence(payload, expected):
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == expected


# --- Missing CRC / charset (A1 / A2) ---------------------------------------


def test_missing_crc_field_maps_to_missing_mandatory():
    payload = _dynamic_parts()  # no "6304" + CRC appended
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD


def test_non_ascii_value_maps_to_invalid_charset():
    payload = _dynamic_parts(name="Caf\xe9") + "6304ABCD"
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_CHARSET


def test_non_latin1_value_maps_to_invalid_charset():
    payload = _dynamic_parts(name="Mer\U0001F600chant") + "6304ABCD"
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_CHARSET


def test_repeated_unknown_tag_with_invalid_first_value_is_rejected():
    # Two unknown "03" tags (ascending, before the CRC); the FIRST occurrence
    # carries a non-printable byte. Charset must run over every parsed
    # occurrence, not only the last dict value.
    payload = _build(
        _tlv("00", "01")
        + _tlv("01", "12")
        + _tlv("03", "\x7f")
        + _tlv("03", "ok")
        + _tlv("26", _tlv("00", "br.gov.bcb.pix") + _tlv("01", VALID_CPF))
        + _tlv("53", "986")
        + _tlv("58", "BR")
        + _tlv("59", "M")
        + _tlv("60", "C")
        + _tlv("62", _tlv("05", "TX"))
    )
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(payload)
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_CHARSET


# --- PFI value + static txid rules ----------------------------------------


def test_non_standard_pfi_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(pfi="02"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_static_txid_with_invalid_char_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(pim="11", txid="bad*txid!"))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD


def test_static_overlength_txid_is_rejected():
    with pytest.raises(DecodeError) as excinfo:
        interpreter.interpret(_dynamic(pim="11", txid="A" * 26))
    assert excinfo.value.code == DecodeErrorCode.DECODING_INVALID_PAYLOAD
