---
id: ctx-platform
type: context
ontology: openpix-architecture-v1
title: Platform and Contract Governance Context
status: active
context: platform
created: 2026-07-29
updated: 2026-07-29
tags: [context, platform, contracts, governance]
relations:
  - type: governs
    target: ctx-sdui
  - type: governs
    target: ctx-decoding
  - type: governs
    target: ctx-payment
  - type: governs
    target: ctx-observability
---

# Platform and Contract Governance

Contexto responsável por limites de serviço, convenções HTTP, correlação,
tracing, versionamento e qualidade dos contratos. Não possui regras de SDUI,
decodificação ou pagamentos.

## Knowledge graph

- [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- [[ADR-PLATFORM-001-service-local-openapi-contracts]]
- [[CTX-SDUI]]
- [[CTX-DECODING]]
- [[CTX-PAYMENT]]
- [[CTX-OBSERVABILITY]]
