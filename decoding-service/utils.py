from __future__ import annotations

import binascii
import re

import constants
from models import DecodeErrorCode


class DecodeError(ValueError):
    """Rejected payload carrying a stable machine error code.

    ``code`` is a member of the generated ``DecodeErrorCode`` enum from the
    contract, so the runtime code cannot drift from the wire format.
    """

    def __init__(self, code: DecodeErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _malformed(detail: str) -> DecodeError:
    return DecodeError(DecodeErrorCode.DECODING_MALFORMED_TLV, detail)


# Tag and length must be exactly two ASCII decimal digits. ``str.isdigit`` is
# not used because it accepts full-width Unicode digits.
_TWO_ASCII_DIGITS = re.compile(r"[0-9]{2}")


def crc16_ccitt(data: bytes) -> int:
    """CRC16-CCITT-FALSE over ``data`` (poly 0x1021, init 0xFFFF, MSB-first).

    ``data`` is the payload bytes INCLUDING the literal tag+length ``6304``,
    EXCLUDING only the final 4 CRC characters. Implemented with the stdlib
    ``binascii.crc_hqx(..., CRC_INIT)``, which is CRC-CCITT (poly 0x1021, init
    0xFFFF, MSB-first, no reflection) — identical to the algorithm this service
    requires. Verified against the published A5C7 test vector and the
    reviewer's verified vectors.
    """
    return binascii.crc_hqx(data, constants.CRC_INIT)


def parse_emv_tlv(
    data: str,
    *,
    known_tags: frozenset[str] = constants.KNOWN_TAGS,
    crc_field: bool = True,
) -> list[tuple[str, str]]:
    """Parse ONE flat EMV TLV level from a raw ASCII string.

    Wire format: 2-digit tag, 2-digit DECIMAL length, then ``length`` raw ASCII
    value characters. No hex encoding anywhere in the payload. This function
    parses a single template level only; recursive parsing of the sub-TLV inside
    tags 26 and 62 is the responsibility of the interpretation layer.

    Raises ``DecodeError`` with code ``DECODING_MALFORMED_TLV`` for:
    - a tag or length made of non-``[0-9]`` characters;
    - a length that overruns the remaining input or a truncated tag/length;
    - a repeated known tag;
    - tags not in non-descending numeric order (canonical EMV ordering;
      equal values are allowed; the final CRC tag is exempt from the
      comparison);
    - (when ``crc_field`` is true) a CRC field not in the fixed ``6304`` +
      exactly 4 UPPERCASE hex character form, or a CRC field that is not the
      final field.

    Unknown tags are returned as-is; ignoring them is an interpretation
    concern, not a parse error.
    """
    fields: list[tuple[str, str]] = []
    seen_known: set[str] = set()
    index = 0
    length = len(data)
    previous: int | None = None

    while index < length:
        if index + 4 > length:
            raise _malformed("Truncated TLV tag or length.")
        tag = data[index : index + 2]
        size = data[index + 2 : index + 4]
        if not (_TWO_ASCII_DIGITS.fullmatch(tag) and _TWO_ASCII_DIGITS.fullmatch(size)):
            raise _malformed("TLV tag and length must be two ASCII decimal digits.")
        index += 4

        # Canonical EMV ordering: tags at one level must be non-descending by
        # numeric value. Equal values are allowed (unknown duplicate tags);
        # a strictly descending pair is malformed. The final CRC tag is exempt
        # from the numeric comparison: unknown tags numerically above it (e.g.
        # "64") may legally precede it, and the CRC is still enforced as final.
        if not (crc_field and tag == constants.CRC_TAG):
            tag_number = int(tag)
            if previous is not None and tag_number < previous:
                raise _malformed("TLV tags must be in non-descending numeric order.")
            previous = tag_number

        if tag in known_tags:
            if tag in seen_known:
                raise _malformed(f"Duplicate known tag {tag}.")
            seen_known.add(tag)

        if crc_field and tag == constants.CRC_TAG:
            if size != constants.CRC_LENGTH_BYTES:
                raise _malformed("CRC field must use the fixed 6304 form.")
            crc = data[index : index + constants.CRC_HEX_LEN]
            if (
                len(crc) != constants.CRC_HEX_LEN
                or not re.fullmatch(constants.CRC_VALUE_RE, crc)
            ):
                raise _malformed("CRC value must be 4 UPPERCASE hex characters.")
            index += constants.CRC_HEX_LEN
            if index != length:
                raise _malformed("CRC field must be the final field.")
            fields.append((tag, crc))
            break

        field_length = int(size, 10)
        if index + field_length > length:
            raise _malformed(f"Field {tag} length overruns the payload.")
        value = data[index : index + field_length]
        index += field_length
        fields.append((tag, value))

    return fields
