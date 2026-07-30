---
id: ctx-payment
type: context
ontology: openpix-architecture-v1
title: Payment Lifecycle Context
status: active
context: payment
created: 2026-07-29
updated: 2026-07-29
tags: [context, payment, idempotency, state-machine]
relations:
  - type: depends_on
    target: ctx-platform
  - type: observed_by
    target: ctx-observability
  - type: related_to
    target: ctx-decoding
  - type: related_to
    target: ctx-sdui
---

# Payment Lifecycle

Contexto responsável pelo aggregate Payment, validação de valor e moeda,
transições, idempotência, persistência e resultados. Não conhece componentes
SDUI nem decide como um payload é lido.

## Knowledge graph

- [[RFC-PAYMENT-001-payment-lifecycle-and-idempotency]]
- [[ADR-PAYMENT-001-aggregate-state-machine]]
- [[CTX-DECODING]]
- [[CTX-SDUI]]
- [[CTX-OBSERVABILITY]]
