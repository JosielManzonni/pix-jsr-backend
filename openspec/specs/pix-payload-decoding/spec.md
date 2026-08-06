# pix-payload-decoding Specification

## Purpose
TBD - created by archiving change add-pix-decoding-service. Update Purpose after archive.
## Requirements
### Requirement: Decode a valid Pix BR Code payload

The service SHALL accept a raw Pix/BR Code payload and return a normalized,
interpreted payment instruction. The instruction contains EITHER a recipient
Pix key with its detected key type (`cpf`, `cnpj`, `phone`, `email`, `evp`),
OR a dynamic location carried in tag 26.25, plus mode (`static` | `dynamic`),
optional amount (string, 2 decimal places), optional txid, optional
description, merchant name, merchant city, optional MCC, and CRC16
verification result. For a location-based dynamic instruction, `key` and
`key_type` are null and `location` contains the raw tag 26.25 value. Decoding
never creates or persists a payment.

#### Scenario: Valid dynamic BR Code

Given a well-formed dynamic BR Code payload with a valid CRC16,
Pix GUI, currency BRL, and exactly one recipient source: a recognized key in
tag 26.01 or a non-empty location in tag 26.25
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 200 and the body is the interpreted instruction
And the mode is `dynamic` and the txid is the one carried in the payload

#### Scenario: Valid dynamic BR Code with a location

Given a well-formed dynamic BR Code payload with a valid CRC16 and a non-empty
tag 26.25 but no tag 26.01
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 200 and the mode is `dynamic`
And `key` and `key_type` are null and `location` equals the raw tag 26.25 value

#### Scenario: Valid static BR Code

Given a well-formed static BR Code payload (point of initiation `11` or absent)
with a valid CRC16
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 200 and the instruction mode is `static`

#### Scenario: Static requires a key and ignores a location

Given a static BR Code payload carrying tag 26.01
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 200 with `key` set and `location` null, even if tag 26.25
is also present

### Requirement: Strict validation with structured errors

The service SHALL reject any payload that fails validation with a 422 and a
Problem Details body carrying `type`, `title`, `status`, `detail`, `code`, and
`correlationId`. Failure classes: malformed TLV structure, CRC16 mismatch,
missing mandatory field, currency other than BRL, invalid Pix key, missing
recipient key/location, conflicting dynamic key and location, payload over the
maximum length, and characters outside the allowed charset.

#### Scenario: CRC16 mismatch

Given a BR Code payload whose provided CRC does not match the computed CRC16
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` identifies the CRC failure

#### Scenario: Malformed TLV

Given a payload that cannot be parsed as an EMV TLV chain (truncated field,
invalid length)
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` identifies the parse failure

#### Scenario: Missing mandatory field

Given a payload missing a mandatory field (for example the merchant account
info or the CRC field)
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` identifies the missing field

#### Scenario: Non-BRL currency

Given a payload whose transaction currency is not `986`
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` identifies the unsupported currency

#### Scenario: Invalid Pix key

Given a payload whose Pix key does not match any recognized key format
(CPF, CNPJ, phone, email, or EVP)
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` identifies the invalid key

#### Scenario: Dynamic with both key and location

Given a dynamic BR Code payload carrying both tag 26.01 and tag 26.25
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` is `DECODING_INVALID_PAYLOAD`

#### Scenario: Dynamic with neither key nor location

Given a dynamic BR Code payload carrying neither tag 26.01 nor tag 26.25
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` is `DECODING_MISSING_MANDATORY_FIELD`

#### Scenario: Dynamic with empty location and no key

Given a dynamic BR Code payload with an empty tag 26.25 and no tag 26.01
When a client POSTs it to `/decode/v1/pix-payloads`
Then the response is 422
And the Problem Details `code` is `DECODING_INVALID_PAYLOAD`

### Requirement: Correlation across the boundary

The service SHALL accept `X-Correlation-Id` and reflect it in the response and
in any Problem Details body; when absent, a correlation id SHALL be generated.

#### Scenario: Client-provided correlation id

Given a request carrying `X-Correlation-Id: abc-123`
When the payload is invalid and rejected
Then the Problem Details body contains `correlationId: abc-123`
And the response carries the same correlation id header

### Requirement: Boundary discipline

The service MUST expose no payment-creation or persistence behavior. Request
payloads and decoded key material are never written to logs. The OpenAPI
contract lives at `decoding-service/contracts/openapi.yaml` and is the only
interface of the service.

#### Scenario: Payload not logged

Given a request with a BR Code payload
When the service processes it (valid or invalid)
Then no log record contains the payload string or its decoded key material

#### Scenario: Contract ownership

Given the decoding service contract
Then it is served from `decoding-service/contracts/openapi.yaml`
And no internal model or table of another service is referenced by it

