from __future__ import annotations

import pydantic
import pytest

from fixtures import VALID_CPF
from models import (
    CrcValid,
    DecodeErrorCode,
    DecodedInstruction,
    DecodePayloadRequest,
    KeyType,
    Mode,
    ProblemDetails,
)


def test_decode_payload_request_accepts_payload_without_constraints():
    request = DecodePayloadRequest(payload="000201...")
    assert request.payload == "000201..."


def test_decode_payload_request_requires_payload():
    with pytest.raises(pydantic.ValidationError):
        DecodePayloadRequest()


def test_decoded_instruction_validates_sample_static_instruction():
    instruction = DecodedInstruction(
        key=VALID_CPF,
        key_type=KeyType.cpf,
        mode=Mode.static,
        merchant_name="Fulano de Tal",
        merchant_city="SAO PAULO",
        crc_valid=True,
    )
    assert instruction.key == VALID_CPF
    assert instruction.key_type == KeyType.cpf
    assert instruction.mode == Mode.static
    assert instruction.amount is None
    assert instruction.txid is None
    assert instruction.description is None
    assert instruction.location is None
    assert instruction.mcc is None
    assert instruction.crc_valid is CrcValid.boolean_True


def test_decoded_instruction_validates_optional_fields():
    instruction = DecodedInstruction(
        key="12a34b56-c0d0-4e5f-9a1b-2c3d4e5f6a7b",
        key_type=KeyType.evp,
        mode=Mode.dynamic,
        amount="10.00",
        txid="txid123",
        description="payment",
        merchant_name="Merchant",
        merchant_city="BRASILIA",
        mcc="0000",
        crc_valid=True,
    )
    assert instruction.amount == "10.00"
    assert instruction.txid == "txid123"
    assert instruction.mcc == "0000"


def test_key_and_key_type_are_optional():
    instruction = DecodedInstruction(
        mode=Mode.dynamic,
        merchant_name="Merchant",
        merchant_city="BRASILIA",
        crc_valid=True,
    )
    assert instruction.key is None
    assert instruction.key_type is None
    assert instruction.location is None


def test_location_based_instruction_allows_null_key_and_key_type():
    instruction = DecodedInstruction(
        key=None,
        key_type=None,
        location="bitsorbyte.com.br/login",
        mode=Mode.dynamic,
        merchant_name="TESOURO NACIONAL",
        merchant_city="BRASILIA",
        crc_valid=True,
    )
    assert instruction.key is None
    assert instruction.key_type is None
    assert instruction.location == "bitsorbyte.com.br/login"


def test_decoded_instruction_rejects_invalid_amount_format():
    with pytest.raises(pydantic.ValidationError):
        DecodedInstruction(
            key=VALID_CPF,
            key_type=KeyType.cpf,
            mode=Mode.static,
            amount="10.0",
            merchant_name="Merchant",
            merchant_city="BRASILIA",
            crc_valid=True,
        )


def test_decoded_instruction_rejects_crc_valid_false():
    with pytest.raises(pydantic.ValidationError):
        DecodedInstruction(
            key=VALID_CPF,
            key_type=KeyType.cpf,
            mode=Mode.static,
            merchant_name="Merchant",
            merchant_city="BRASILIA",
            crc_valid=False,
        )


def test_problem_details_validates_sample_error():
    problem = ProblemDetails(
        type="https://openpix.dev/problems/decoding-crc-mismatch",
        title="CRC mismatch",
        status=422,
        detail="The payload CRC does not match.",
        code=DecodeErrorCode.DECODING_CRC_MISMATCH,
        correlationId="correlation-123",
    )
    assert problem.status == 422
    assert problem.code == DecodeErrorCode.DECODING_CRC_MISMATCH
    assert problem.correlationId == "correlation-123"


def test_problem_details_rejects_unknown_error_code():
    with pytest.raises(pydantic.ValidationError):
        ProblemDetails(
            type="https://openpix.dev/problems/unknown",
            title="Unknown",
            status=422,
            detail="Unknown code.",
            code="NOT_A_REAL_CODE",
            correlationId="correlation-123",
        )
