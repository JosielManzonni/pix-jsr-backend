---
id: ctx-decoding
type: context
ontology: openpix-architecture-v1
title: Pix Payload Decoding Context
status: active
context: decoding
created: 2026-07-29
updated: 2026-07-29
tags: [context, decoding, pix, br-code]
relations:
  - type: depends_on
    target: ctx-platform
  - type: produces_for
    target: ctx-payment
  - type: observed_by
    target: ctx-observability
---

# Pix Payload Decoding

Contexto responsável por validar e normalizar payloads Pix/BR Code. A saída é
uma instrução interpretada; criar ou persistir um pagamento pertence ao
Payment Context.

## Knowledge graph

- [[RFC-DECODING-001-pix-payload-decoding-boundary]]
- [[ADR-DECODING-001-stateless-payload-decoding]]
- [[CTX-PAYMENT]]
- [[CTX-OBSERVABILITY]]
