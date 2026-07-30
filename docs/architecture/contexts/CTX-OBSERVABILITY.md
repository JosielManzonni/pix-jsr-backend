---
id: ctx-observability
type: context
ontology: openpix-architecture-v1
title: Observability Context
status: active
context: observability
created: 2026-07-29
updated: 2026-07-29
tags: [context, observability, metrics, traces, health]
relations:
  - type: depends_on
    target: ctx-platform
  - type: observes
    target: ctx-sdui
  - type: observes
    target: ctx-decoding
  - type: observes
    target: ctx-payment
---

# Observability

Contexto responsável por padrões de logs, métricas, traces e interfaces
operacionais. Ele observa os demais contextos sem absorver suas regras de
negócio ou dados sensíveis.

## Knowledge graph

- [[RFC-OBSERVABILITY-001-operational-observability-interface]]
- [[ADR-OBSERVABILITY-001-pull-based-operational-endpoints]]
- [[CTX-SDUI]]
- [[CTX-DECODING]]
- [[CTX-PAYMENT]]
