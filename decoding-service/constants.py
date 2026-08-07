"""Verified Pix/EMV constants for BR Code decoding.

Sources:
- BACEN "Manual de Padrões para Iniciação do Pix"
  https://www.bcb.gov.br/acessoinformacao/legislacao_normativas/manual-de-padroes-para-iniciacao-do-pix
- EMVCo EMV QR Code Specification for Payment Systems (QRCPS)
  https://www.emvco.com/specifications/emv-qr-code/

The values below were cross-checked against the official Pix manual and two
independent EMV QRCPS implementations. They are the single source of truth for
all decode limits, key formats, and CRC parameters in this service.

The error ``code`` values are NOT defined here: they are the ``DecodeErrorCode``
enum generated from the OpenAPI contract, so they cannot drift from the wire
format.
"""

# --- Payload envelope ------------------------------------------------------

# Maximum total payload length in characters (EMV QRCPS).
MAX_PAYLOAD_LENGTH = 512

# --- CRC16-CCITT-FALSE (EMV QRCPS Annex C / Pix) ---------------------------
# Polynomial 0x1021, init 0xFFFF, MSB-first, no input/output reflection, no
# xor-out. Output is 4 UPPERCASE hex characters. Computed with the stdlib
# ``binascii.crc_hqx`` (CRC-CCITT, identical algorithm, C-speed). Verified
# against the published A5C7 test vector and the reviewer's vectors.
CRC_INIT = 0xFFFF
CRC_HEX_LEN = 4  # 16-bit CRC expressed as 4 UPPERCASE hex characters
# CRC scope: computed over the entire payload INCLUDING the literal tag+length
# bytes "6304", EXCLUDING only the final 4 CRC hex characters.
CRC_TAG = "63"
CRC_LENGTH_BYTES = "04"

# --- TLV structure ----------------------------------------------------------

# Known top-level tags. Unknown top-level tags are ignored (EMV reader rule).
# A repeated KNOWN tag makes the payload malformed.
KNOWN_TAGS = frozenset(
    {"00", "01", "26", "52", "53", "54", "58", "59", "60", "61", "62", "63"}
)
# Known sub-tags inside tag 26 (merchant account information).
KNOWN_SUB_TAGS_26 = frozenset({"00", "01", "02", "25"})
# Known sub-tags inside tag 62 (additional data).
KNOWN_SUB_TAGS_62 = frozenset({"05"})

# --- Field values (raw ASCII compared after parsing) ------------------------

PFI_VALUE = "01"  # tag 00 payload format indicator
PIM_STATIC = "11"  # tag 01 point of initiation: static
PIM_DYNAMIC = "12"  # tag 01 point of initiation: dynamic
GUI = "BR.GOV.BCB.PIX"  # tag 26.00 global unique identifier (case-insensitive)
CURRENCY_BRL = "986"  # tag 53 ISO 4217 numeric code for BRL
COUNTRY_BR = "BR"  # tag 58 ISO 3166-1 alpha-2

# --- Field length limits (characters of the ASCII value) --------------------

LIMIT_DESCRIPTION = 72  # tag 26.02 reference label / description
LIMIT_MERCHANT_NAME = 25  # tag 59
LIMIT_MERCHANT_CITY = 15  # tag 60
LIMIT_TXID = 25  # tag 62.05, charset [a-zA-Z0-9*]

# --- Field value formats ----------------------------------------------------

# tag 54 amount: up to 10 integer digits, a '.' separator, exactly 2 decimals.
AMOUNT_RE = r"^\d{1,10}\.\d{2}$"
# tag 62.05 txid charset.
TXID_RE = r"^[a-zA-Z0-9*]+$"
# tag 52 merchant category code: exactly 4 digits.
MCC_RE = r"^\d{4}$"
# CRC field value: exactly 4 UPPERCASE hex characters.
CRC_VALUE_RE = r"[0-9A-F]{4}"

# --- Key formats ------------------------------------------------------------
#
# Shape regexes gate the cheap disqualifiers; deeper structural validation
# (check digits for CPF/CNPJ, linear email rule, RFC 4122 v4 for EVP) lives in
# interpreter._detect_key_type and maps a shape-valid but invalid key to
# DECODING_INVALID_KEY.

CPF_RE = r"^\d{11}$"
CNPJ_RE = r"^\d{14}$"
# Mobile: +55 + 2 DDD digits + 9 subscriber digits = 14 characters.
PHONE_RE = r"^\+55\d{11}$"

# --- Order of decode checks (documented in interpreter.interpret) -----------
# Kept here as documentation only; the actual order lives in the interpreter.
