# Payment Context

The payment context owns the lifecycle of Pix payments: creation from an
interpreted instruction, value/currency validation, transitions, idempotency,
persistence, and results. It never reads raw Pix payloads and never decides
how a payload is decoded. (Architecture map lives in `docs/architecture/`.)

## Language

**Payment**:
The aggregate that records an intent to move BRL via Pix and tracks it
through its lifecycle to a terminal result.
_Avoid_: charge, order, transaction

**Payment Instruction**:
The normalized, interpreted payment data produced by the decoding context
(key or location, mode, amount, txid, merchant) that seeds a Payment.
_Avoid_: payload, decoded payload

**Idempotency Key**:
A caller-supplied token that makes repeated create requests safe: the same
key yields the same Payment instead of a duplicate. Idempotency applies at
two points: deduplicating create requests by key, and ensuring only one
consumer processes the same Payment Intent.
_Avoid_: reference, retry token

**Executor**:
The boundary through which a Payment's money movement actually happens
(an external PSP integration).
_Avoid_: PSP, bank, gateway

**Result**:
The terminal outcome of a Payment lifecycle: confirmed, failed, or cancelled.
_Avoid_: status, outcome

**Payment Intent**:
The queued work item that carries a Payment toward execution by a consumer.
Distinct from the Payment: the Payment is the aggregate; the intent is the
execution request en route to the Executor.
_Avoid_: job, task, message

**Consumer**:
The process that receives Payment Intents and drives them through the
Executor.
_Avoid_: worker, subscriber

**Pedro Bank**:
The fictional banking institution that executes money movement; the concrete
Executor for this project.
_Avoid_: PSP, provider (when the Executor is Pedro Bank)

**Payment History**:
A cursor-paginated listing of a specific user's Payments, ordered newest
first; each entry carries the Payment's current status.
_Avoid_: feed, list, page, statement

**User**:
A single person who owns Pix keys and initiates payments. One person can
hold many keys across accounts and institutions.
_Avoid_: client, account holder, customer

**Pix Key**:
An identifier registered in the Pix directory (CPF, CNPJ, phone, email, or
random key/EVP) that points to exactly one transactional account. A User owns
several; each is unique across the whole directory. The account a key points
to (participant, branch, number, type) is data carried on the key, matching
the DICT Entry shape — there is no separate Account entity.
_Avoid_: chave (in English prose), alias, address

**Open Finance**:
The Open Finance Brasil APIs (BACEN) leveraged as the source of user and
account data. The payment context never performs DICT operations (key
registration, portability, claims) itself.
_Avoid_: directory operations, DICT ops
