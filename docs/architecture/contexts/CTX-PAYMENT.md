---
id: ctx-payment
type: context
ontology: openpix-architecture-v1
title: Payment Lifecycle Context
status: active
context: payment
created: 2026-07-29
updated: 2026-08-18
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
  - type: related_to
    target: ref-bacen-pix-dict
---

# Payment Lifecycle

Contexto responsável pelo aggregate Payment, validação de valor e moeda,
transições, idempotência, persistência e resultados. O `payment-service` cria
pagamentos a partir de dados normalizados e os executa de forma assíncrona por
um Executor; não aceita BR Code bruto, não conhece componentes SDUI nem decide
como um payload é lido. O lifecycle mais rico legado, incluindo comandos de
confirm/cancel, está superseded e não é comportamento implementado.

## Knowledge graph

- [[RFC-PAYMENT-001-payment-lifecycle-and-idempotency]]
- [[ADR-PAYMENT-001-aggregate-state-machine]]
- [[CTX-DECODING]]
- [[CTX-SDUI]]
- [[CTX-OBSERVABILITY]]
- [[ref-bacen-pix-dict|BACEN Pix/DICT Canonical Reference]]
