"""Shared canonical payload vectors and builders for the decoding tests.

Single home for the raw BR Code vectors and the payload-building helpers that
were previously duplicated across test_main and test_interpreter.
"""

from __future__ import annotations

import binascii


def _tlv(tag: str, value: str) -> str:
    return tag + f"{len(value):02d}" + value


def _build(payload_without_crc: str) -> str:
    """Append a CRC computed independently (binascii) to keep fixture CRC honest.

    CRC scope: over the payload INCLUDING the literal "6304" tag+length bytes,
    excluding only the final 4 CRC hex characters.
    """
    body = payload_without_crc + "6304"
    crc = f"{binascii.crc_hqx(body.encode('ascii'), 0xFFFF):04X}"
    return body + crc


# Valid CPF/CNPJ test keys (check digits validate).
VALID_CPF = "52998224725"
VALID_CNPJ = "11222333000181"
# A valid RFC 4122 v4 EVP key used by the dynamic vectors.
VALID_EVP = "71d6c6e1-64ea-4a11-9560-a10870c40ca2"


def _dynamic_parts(
    key: str | None = VALID_CPF,
    txid: str | None = "TXID123",
    amount: str | None = "12.30",
    name: str | None = "Merchant",
    city: str | None = "BRASILIA",
    pim: str | None = "12",
    gui: str = "br.gov.bcb.pix",
    currency: str | None = "986",
    country: str | None = "BR",
    pfi: str = "01",
    description: str | None = None,
    location: str | None = None,
    mcc: str | None = None,
) -> str:
    parts = [_tlv("00", pfi)]
    if pim is not None:
        parts.append(_tlv("01", pim))
    sub26 = _tlv("00", gui)
    if key is not None:
        sub26 += _tlv("01", key)
    if description is not None:
        sub26 += _tlv("02", description)
    if location is not None:
        sub26 += _tlv("25", location)
    parts.append(_tlv("26", sub26))
    if mcc is not None:
        parts.append(_tlv("52", mcc))
    if currency is not None:
        parts.append(_tlv("53", currency))
    if amount is not None:
        parts.append(_tlv("54", amount))
    if country is not None:
        parts.append(_tlv("58", country))
    if name is not None:
        parts.append(_tlv("59", name))
    if city is not None:
        parts.append(_tlv("60", city))
    if txid is not None:
        parts.append(_tlv("62", _tlv("05", txid)))
    return "".join(parts)


def _dynamic(
    key: str | None = VALID_CPF,
    txid: str | None = "TXID123",
    amount: str | None = "12.30",
    name: str | None = "Merchant",
    city: str | None = "BRASILIA",
    pim: str | None = "12",
    gui: str = "br.gov.bcb.pix",
    currency: str | None = "986",
    country: str | None = "BR",
    pfi: str = "01",
    description: str | None = None,
    location: str | None = None,
    mcc: str | None = None,
) -> str:
    return _build(
        _dynamic_parts(
            key=key,
            txid=txid,
            amount=amount,
            name=name,
            city=city,
            pim=pim,
            gui=gui,
            currency=currency,
            country=country,
            pfi=pfi,
            description=description,
            location=location,
            mcc=mcc,
        )
    )


def _dynamic_vector(txid: str, amount: str | None, city: str = "SAO PAULO") -> str:
    """A dynamic, key-based BR Code with an EVP key and an MCC field."""
    sub26 = _tlv("00", "br.gov.bcb.pix") + _tlv("01", VALID_EVP)
    parts = [
        _tlv("00", "01"),
        _tlv("01", "12"),
        _tlv("26", sub26),
        _tlv("52", "0000"),
        _tlv("53", "986"),
    ]
    if amount is not None:
        parts.append(_tlv("54", amount))
    parts.append(_tlv("58", "BR"))
    parts.append(_tlv("59", "COMPANY1DATA"))
    parts.append(_tlv("60", city))
    parts.append(_tlv("62", _tlv("05", txid)))
    return _build("".join(parts))


# Static p1 fixture from the rework (CRC B659): static phone key.
P1_STATIC = (
    "00020101021126690014br.gov.bcb.pix0114+55279957710220229Doacao Livre / "
    "QRCODE - PYPIX52040000530398654045.005802BR5905Teste6009Cariacica"
    "61082914861362130509PIXMP00016304B659"
)

# Verified p5 vector: DYNAMIC, location-based (tag 26.25, no key, no scheme),
# CRC 2D75.
P5_DYNAMIC = (
    "00020101021226450014br.gov.bcb.pix2523bitsorbyte.com.br/login"
    "5204000053039865802BR5916TESOURO NACIONAL6008BRASILIA62070503***63042D75"
)
