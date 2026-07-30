---
id: adr-platform-001
type: adr
ontology: openpix-architecture-v1
title: Keep OpenAPI Contracts with the Owning Service
status: accepted
context: platform
created: 2026-07-29
updated: 2026-07-29
tags: [adr, platform, openapi, ownership]
relations:
  - type: belongs_to
    target: ctx-platform
  - type: resolves
    target: rfc-platform-001
  - type: governs
    target: ctx-sdui
  - type: governs
    target: ctx-decoding
  - type: governs
    target: ctx-payment
  - type: governs
    target: ctx-observability
---

# ADR-PLATFORM-001: Service-local OpenAPI contracts

## Status

Accepted.

## Context

O backend é um monorepo com serviços de ownership independente e stacks
poliglotas. Um contrato central poderia sugerir ownership central e releases
coordenadas.

## Decision

Cada contrato fica em `<service-name>-service/contracts/openapi.yaml`. Conceitos
transversais podem ser repetidos ou publicados futuramente como artefatos de
governança, mas nenhum serviço referencia schemas internos de outro no runtime.

## Consequences

### Positive

- ownership e revisão acompanham o deployable;
- cada pipeline valida somente seu contrato;
- serviços podem evoluir sem compartilhar código;
- descoberta continua possível pelo knowledge graph.

### Negative

- convenções transversais podem divergir;
- alterações amplas exigem automação de lint e governança;
- consumidores precisam declarar explicitamente qual contrato usam.

## Rejected alternatives

- Um único `backend-openapi.yaml`.
- Modelos Python/Java compartilhados como fonte do contrato.
- Gerar o contrato apenas a partir do runtime sem revisão contract-first.

## Knowledge graph

- Resolve [[RFC-PLATFORM-001-contract-first-service-boundaries]].
- Pertence a [[CTX-PLATFORM]].
