# Payment Lifecycle Specification

## ADDED Requirements

### Requirement: Payment creation

The service SHALL expose `POST /payments` that creates a Payment from
decoded-instruction data and enqueues a Payment Intent atomically in the same
persistence transaction. The request SHALL carry a valid API key, an
`Idempotency-Key` header, a payee Pix key, an amount, and MAY carry a
description. The schema SHALL NOT accept a raw Pix BR Code payload field.

#### Scenario: Successful creation

- **GIVEN** a caller with a valid API key
- **WHEN** it POSTs a valid payment request with an `Idempotency-Key`
- **THEN** the response is 201 with a Payment body whose `status` is `created`
  and whose `id`, `createdAt`, and `updatedAt` are set
- **AND** exactly one pending Payment Intent exists for that Payment

#### Scenario: Missing Idempotency-Key

- **WHEN** a request arrives without the `Idempotency-Key` header
- **THEN** the response is 422 with a Problem Details body containing `code`
  and `correlationId`, and nothing is persisted

#### Scenario: Invalid amount

- **WHEN** the amount is `"0.00"`, negative, above `"9999999.99"`, not a
  string matching `^\d+\.\d{2}$`, or a JSON number
- **THEN** the response is 422 with a Problem Details body and nothing is
  persisted

#### Scenario: Unauthenticated

- **WHEN** the API key is missing or unknown
- **THEN** the response is 401 with a Problem Details body

#### Scenario: Raw payload rejected

- **WHEN** the request body carries a BR Code string field
- **THEN** the response is 422; the service never parses raw Pix payloads

### Requirement: Idempotent creation

The service SHALL enforce a unique constraint on (caller, Idempotency-Key).

#### Scenario: Replay returns the original

- **GIVEN** a Payment was created with Idempotency-Key K and body B
- **WHEN** the same caller POSTs K with an identical body B
- **THEN** the response is 200 with the original Payment, and no duplicate
  Payment or Intent is persisted

#### Scenario: Key reuse with different body

- **WHEN** the same caller POSTs K with a different body
- **THEN** the response is 409 with a Problem Details body

### Requirement: Payment lifecycle states

A Payment SHALL exist in exactly one of `created`, `confirmed`, `failed`.
Transitions SHALL be authorized only by the Payment aggregate: `created →
confirmed` and `created → failed` are the only transitions; `confirmed` and
`failed` are terminal.

#### Scenario: Terminal states are immutable

- **GIVEN** a Payment in `confirmed` or `failed`
- **WHEN** any further transition is attempted
- **THEN** it is rejected with a stable domain error and the state is unchanged

#### Scenario: No other states exist

- **WHEN** a Payment is serialized
- **THEN** `status` is one of `created`, `confirmed`, `failed` and no
  confirm/cancel endpoints exist

### Requirement: Asynchronous execution

Pending intents SHALL be claimed by in-process consumers via an atomic
conditional update, so exactly one consumer wins a given intent. The consumer
SHALL call the Executor synchronously without holding a database lock, then
persist the terminal state. The service SHALL NOT retry a failed Executor
call internally.

#### Scenario: Single winner under competition

- **GIVEN** one pending intent and two consumers claiming concurrently
- **THEN** exactly one claim succeeds and the Executor is called once

#### Scenario: Executor success

- **WHEN** the Executor confirms
- **THEN** the Payment transitions to `confirmed`

#### Scenario: Executor failure without retry

- **WHEN** the Executor call fails or times out
- **THEN** the Payment transitions to `failed` with a reason, the intent is
  consumed, and no internal retry is attempted; a caller retry requires a new
  intent

### Requirement: Executor boundary

Execution SHALL go through an Executor port. The shipped implementation SHALL
be an in-repo Pedro Bank fake: deterministic confirmation by default, failure
injection available for tests, and no network calls.

#### Scenario: Fake is deterministic

- **WHEN** the fake Executor is invoked in its default configuration
- **THEN** it confirms, without any network traffic

#### Scenario: Failure injection

- **WHEN** the fake is configured to fail
- **THEN** the consumer marks the Payment `failed` with the injected reason

### Requirement: Payment retrieval

The service SHALL expose `GET /payments/{paymentId}` scoped to the caller
identified by the API key.

#### Scenario: Owner reads own payment

- **THEN** the response is 200 with the Payment including its current `status`

#### Scenario: Other user's payment is invisible

- **WHEN** the payment belongs to a different user
- **THEN** the response is 404, disclosing nothing about existence

#### Scenario: Not cacheable

- **THEN** the response carries `Cache-Control: no-store`

### Requirement: Payment history

The service SHALL expose a per-user payment history served with the HTTP
QUERY method at runtime (RFC 10008). Because OpenAPI 3.0.3/3.1 cannot declare
`query`, the contract SHALL declare the operation as `post` with an extension
note recording the runtime method. Results SHALL be newest-first, keyset-
paginated with an opaque cursor, and stable under concurrent inserts.

#### Scenario: Default page

- **WHEN** the caller queries history without parameters
- **THEN** the response is 200 with `{items, nextCursor}`, at most 50 items,
  each carrying `status`, newest first, containing only the caller's payments

#### Scenario: Limit bounds

- **WHEN** `limit` is below 1 or above 100
- **THEN** the response is 422 with a Problem Details body

#### Scenario: Cursor traversal without duplicates

- **GIVEN** more than one page of history
- **WHEN** the caller follows `nextCursor` across pages
- **THEN** no item repeats, no item is skipped, and the cursor remains stable
  while new payments are inserted

#### Scenario: Served contract declares post

- **WHEN** the served OpenAPI document is inspected
- **THEN** the history operation is declared as `post` and carries the note
  that the runtime method is QUERY

### Requirement: Money representation

Amounts SHALL be decimal BRL, serialized as JSON strings matching
`^\d+\.\d{2}$`, with `0 < amount ≤ 9,999,999.99`. The currency SHALL be BRL
only.

#### Scenario: Precision preserved

- **WHEN** a Payment is created with amount `"1234.56"`
- **THEN** it is stored and returned exactly as `"1234.56"` with no float
  rounding

### Requirement: Pix identity model

The caller's API key SHALL identify the User (a person, CPF/CNPJ). PixKey
SHALL carry account data (participant, branch, number, type — the DICT Entry
shape) as data; there SHALL be no Account entity. The service SHALL NOT
perform DICT operations.

#### Scenario: No DICT surface

- **WHEN** the contract is inspected
- **THEN** no key registration, portability, claim, or key-registry operation
  exists

### Requirement: Operational surface

The service SHALL expose the platform operational surface per the
observability conventions: `/health` and `/ready` in the contract, metrics on
a separate port, `X-Correlation-ID` echo or generation, structured logs, and
W3C trace context via the shared observability package.

#### Scenario: Probes respond

- **WHEN** `/health` and `/ready` are called
- **THEN** they respond per the contract without exposing internals

### Requirement: Financial data hygiene

Responses under `/payments` SHALL carry `Cache-Control: no-store`. Pix keys,
account data, idempotency keys, raw payloads, and internal database ids SHALL
NOT appear in logs, metrics, or traces.

#### Scenario: Logs carry no sensitive material

- **WHEN** any payment operation is logged
- **THEN** the log fields contain no Pix key, account number, idempotency
  key, or raw payload
