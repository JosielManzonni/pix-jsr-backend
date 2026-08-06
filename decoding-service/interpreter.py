"""Semantic interpretation and validation of a raw Pix BR Code payload.

Raw parse (``utils.parse_emv_tlv``) and semantic interpretation are separate
modules per design.md: the parser understands one flat TLV level, this module
understands Pix semantics and recursively parses the sub-TLV inside tags 26 and
62.
"""

from __future__ import annotations

import re
import uuid

import constants
from models import CrcValid, DecodedInstruction, DecodeErrorCode, KeyType, Mode
from utils import DecodeError, crc16_ccitt, parse_emv_tlv


def _printable(value: str) -> bool:
    return all(0x20 <= ord(char) <= 0x7E for char in value)


def _cpf_check_digits(digits: str) -> bool:
    """Standard CPF mod-11 check: weights 10..2 then 11..2.

    All-equal-digit CPFs (e.g. 00000000000) pass mod-11 but are not real keys;
    they are rejected up front.
    """
    if len(set(digits)) == 1:
        return False

    def _check(length: int) -> int:
        total = sum(int(digits[i]) * (length + 1 - i) for i in range(length))
        rest = total % 11
        return 0 if rest < 2 else 11 - rest

    return _check(9) == int(digits[9]) and _check(10) == int(digits[10])


# CNPJ mod-11 check weights (per the Pix / Receita Federal algorithm).
_CNPJ_WEIGHTS_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_WEIGHTS_2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _cnpj_check_digits(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False

    def _check(weights: tuple[int, ...]) -> int:
        total = sum(int(digits[i]) * weight for i, weight in enumerate(weights))
        rest = total % 11
        return 0 if rest < 2 else 11 - rest

    return _check(_CNPJ_WEIGHTS_1) == int(digits[12]) and _check(
        _CNPJ_WEIGHTS_2
    ) == int(digits[13])


def _is_valid_email(key: str) -> bool:
    """Linear email rule: exactly one '@', non-empty local, non-empty domain
    containing at least one '.'."""
    parts = key.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    return "." in domain


def _is_valid_evp(key: str) -> bool:
    try:
        value = uuid.UUID(key)
    except (ValueError, AttributeError):
        return False
    # Canonical Pix EVP keys are hyphenated lowercase UUID text. uuid.UUID also
    # accepts compact and brace-wrapped spellings, which are not valid keys.
    return (
        value.variant == uuid.RFC_4122
        and value.version == 4
        and str(value) == key.lower()
    )


def _detect_key_type(key: str) -> KeyType | None:
    """Detect the Pix key format, validating beyond shape.

    A shape match with an invalid structure (bad CPF/CNPJ check digits, an
    email violating the linear rule, a non-RFC-4122-v4 UUID) returns ``None`` so
    the caller maps it to ``DECODING_INVALID_KEY``.
    """
    if re.fullmatch(constants.CPF_RE, key):
        return KeyType.cpf if _cpf_check_digits(key) else None
    if re.fullmatch(constants.CNPJ_RE, key):
        return KeyType.cnpj if _cnpj_check_digits(key) else None
    if re.fullmatch(constants.PHONE_RE, key):
        return KeyType.phone
    if _is_valid_email(key):
        return KeyType.email
    if _is_valid_evp(key):
        return KeyType.evp
    return None


def interpret(payload: str) -> DecodedInstruction:
    """Validate and interpret a raw Pix payload into a payment instruction.

    Deterministic check order (per the council constraint):
      1. length > 512             -> DECODING_PAYLOAD_TOO_LONG
      2. empty payload            -> DECODING_MALFORMED_TLV
      3. TLV parse (non-descending ordering + CRC-final form)
                                  -> DECODING_MALFORMED_TLV
      4. charset (all occurrences via chained generator)
                                  -> DECODING_INVALID_CHARSET
      5. CRC field present        -> DECODING_MISSING_MANDATORY_FIELD
      6. CRC16 verification       -> DECODING_CRC_MISMATCH
      7. mandatory presence (00, 26 with GUI + key-or-location, 53, 58, 59, 60)
                                  -> DECODING_MISSING_MANDATORY_FIELD
      8. value rules (PFI "01", 59/60 non-empty + limits, 26.02 <= 72,
         MCC ^\\d{4}$, currency 986, country "BR", GUI case-insensitive)
                                  -> DECODING_INVALID_PAYLOAD /
                                     DECODING_UNSUPPORTED_CURRENCY
      9. mode / amount / txid / key-location XOR (key AND location both present)
                                  -> DECODING_INVALID_PAYLOAD
         (missing-recipient classification is owned by step 7)
     10. key detection (check digits / linear email / UUID v4)
                                  -> DECODING_INVALID_KEY
    """
    # 1. Length.
    if len(payload) > constants.MAX_PAYLOAD_LENGTH:
        raise DecodeError(
            DecodeErrorCode.DECODING_PAYLOAD_TOO_LONG,
            "The payload exceeds the maximum supported length.",
        )
    # 2. Empty.
    if not payload:
        raise DecodeError(DecodeErrorCode.DECODING_MALFORMED_TLV, "The payload is empty.")

    # 3. Parser enforces structure, duplicate known tags, canonical ordering,
    #    and the CRC field form. Keep the occurrence list (not a dict) so the
    #    charset step sees every unknown tag repeat, not just the last one.
    parsed = parse_emv_tlv(payload)
    fields = dict(parsed)

    sub26_parsed = parse_emv_tlv(
        fields.get("26", ""), known_tags=constants.KNOWN_SUB_TAGS_26, crc_field=False
    )
    sub62_parsed = parse_emv_tlv(
        fields.get("62", ""), known_tags=constants.KNOWN_SUB_TAGS_62, crc_field=False
    )
    sub26 = dict(sub26_parsed)
    sub62 = dict(sub62_parsed)

    # 4. Charset: printable ASCII (0x20-0x7E) over every parsed value, including
    #    nested sub-TLV and repeated unknown tags. Chained generator, no list
    #    materialization. Runs before CRC so non-latin-1 bytes never reach the
    #    CRC encoding.
    if not all(
        _printable(value)
        for level in (parsed, sub26_parsed, sub62_parsed)
        for _, value in level
    ):
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_CHARSET,
            "A field value contains non-printable ASCII characters.",
        )

    # 5. CRC field must be present.
    if "63" not in fields:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
            "Missing tag 63 (CRC).",
        )

    # 6. CRC is computed over the whole payload INCLUDING the literal "6304"
    #    tag+length bytes, EXCLUDING only the final 4 CRC characters. Charset
    #    already ran, so latin-1 encoding here cannot fail.
    computed = f"{crc16_ccitt(payload[:-4].encode('latin-1')):04X}"
    if computed != payload[-4:]:
        raise DecodeError(
            DecodeErrorCode.DECODING_CRC_MISMATCH,
            "The payload CRC does not match the computed CRC16.",
        )

    # 7. Mandatory field presence.
    if "00" not in fields:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD, "Missing tag 00 (PFI)."
        )
    if "26" not in fields:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
            "Missing tag 26 (merchant account info).",
        )
    if "00" not in sub26:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD, "Missing 26.00 (GUI)."
        )
    # 26 must carry a recipient: a key (26.01) and/or a location (26.25). Which
    # one is authoritative is resolved by mode in step 9.
    has_key = "01" in sub26
    has_location = "25" in sub26
    if not has_key and not has_location:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
            "Missing 26.01 (Pix key) and 26.25 (location).",
        )
    for required in ("53", "58", "59", "60"):
        if required not in fields:
            raise DecodeError(
                DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
                f"Missing mandatory tag {required}.",
            )

    # 8. Value rules.
    if fields["00"] != constants.PFI_VALUE:
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The payload format indicator must be 01.",
        )
    for tag, limit in (
        ("59", constants.LIMIT_MERCHANT_NAME),
        ("60", constants.LIMIT_MERCHANT_CITY),
    ):
        value = fields[tag]
        if not value:
            raise DecodeError(
                DecodeErrorCode.DECODING_INVALID_PAYLOAD,
                f"Mandatory tag {tag} must not be empty.",
            )
        if len(value) > limit:
            raise DecodeError(
                DecodeErrorCode.DECODING_INVALID_PAYLOAD,
                f"Mandatory tag {tag} exceeds its maximum length.",
            )
    if sub26.get("02") is not None and len(sub26["02"]) > constants.LIMIT_DESCRIPTION:
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The description (26.02) exceeds its maximum length.",
        )
    if fields.get("52") is not None and not re.fullmatch(
        constants.MCC_RE, fields["52"]
    ):
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The merchant category code (52) must be exactly 4 digits.",
        )
    if fields["53"] != constants.CURRENCY_BRL:
        raise DecodeError(
            DecodeErrorCode.DECODING_UNSUPPORTED_CURRENCY,
            "Only BRL (986) is supported.",
        )
    if fields["58"] != constants.COUNTRY_BR:
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The country must be BR.",
        )
    if sub26["00"].upper() != constants.GUI.upper():
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The merchant account GUI is not a Pix GUI.",
        )

    # 9. Mode, amount, txid, and key/location resolution.
    pim = fields.get("01")
    if pim is None or pim == constants.PIM_STATIC:
        mode = Mode.static
    elif pim == constants.PIM_DYNAMIC:
        mode = Mode.dynamic
    else:
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The point of initiation value is invalid.",
        )

    amount = fields.get("54")
    if amount is not None and not re.fullmatch(constants.AMOUNT_RE, amount):
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The amount must have up to 10 integer digits and exactly 2 decimals.",
        )

    txid = sub62.get("05")
    if mode is Mode.dynamic and txid is None:
        raise DecodeError(
            DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
            "Dynamic payloads require a txid (62.05).",
        )
    # txid rules apply to every present txid, in BOTH modes.
    if txid is not None and (
        len(txid) > constants.LIMIT_TXID or not re.fullmatch(constants.TXID_RE, txid)
    ):
        raise DecodeError(
            DecodeErrorCode.DECODING_INVALID_PAYLOAD,
            "The txid must be at most 25 characters in [a-zA-Z0-9*].",
        )

    if mode is Mode.static:
        # Static: key is authoritative; a present 26.25 location is IGNORED
        # (deliberate — key wins, response location stays null).
        if not has_key:
            raise DecodeError(
                DecodeErrorCode.DECODING_MISSING_MANDATORY_FIELD,
                "Static payloads require a Pix key (26.01).",
            )
        key = sub26["01"]
        location = None
    else:
        # Dynamic: key XOR location.
        if has_key and has_location:
            raise DecodeError(
                DecodeErrorCode.DECODING_INVALID_PAYLOAD,
                "Dynamic payloads must carry a key OR a location, not both.",
            )
        if has_key:
            key = sub26["01"]
            location = None
        else:
            location = sub26["25"]
            if not location:
                raise DecodeError(
                    DecodeErrorCode.DECODING_INVALID_PAYLOAD,
                    "The location (26.25) must not be empty.",
                )
            key = None

    # 10. Key detection (only when a key is present).
    key_type = None
    if key is not None:
        key_type = _detect_key_type(key)
        if key_type is None:
            raise DecodeError(
                DecodeErrorCode.DECODING_INVALID_KEY,
                "The Pix key does not match any recognized format.",
            )

    return DecodedInstruction(
        key=key,
        key_type=key_type,
        location=location,
        mode=mode,
        amount=amount,
        txid=txid,
        description=sub26.get("02"),
        merchant_name=fields["59"],
        merchant_city=fields["60"],
        mcc=fields.get("52"),
        crc_valid=CrcValid.boolean_True,
    )
