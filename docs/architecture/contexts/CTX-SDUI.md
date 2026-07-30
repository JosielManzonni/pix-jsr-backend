---
id: ctx-sdui
type: context
ontology: openpix-architecture-v1
title: Server-Driven UI Context
status: active
context: sdui
created: 2026-07-29
updated: 2026-07-29
tags: [context, sdui, mobile-configuration, compatibility]
relations:
  - type: depends_on
    target: ctx-platform
  - type: observed_by
    target: ctx-observability
  - type: related_to
    target: ctx-payment
---

# Server-Driven UI

Contexto responsável por configuração móvel, disponibilidade avaliada de
features, composição de telas, compatibilidade do renderer e publicação futura.
Não executa pagamentos nem interpreta payload Pix.

## Knowledge graph

- [[RFC-SDUI-001-mobile-context-and-component-compatibility]]
- [[ADR-SDUI-001-typed-request-context-dependencies]]
- [[ADR-SDUI-002-static-json-runtime-source]]
- [[CTX-PLATFORM]]
- [[CTX-PAYMENT]]
- [[CTX-OBSERVABILITY]]
