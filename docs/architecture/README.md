---
id: architecture-index
type: index
ontology: openpix-architecture-v1
title: OpenPix JSR Architecture Knowledge Graph
status: active
context: platform
created: 2026-07-29
updated: 2026-07-30
tags:
  - architecture
  - knowledge-graph
  - openpix-jsr
relations:
  - type: defines
    target: graph-schema
  - type: contains
    target: architecture-ontology
  - type: contains
    target: ctx-platform
  - type: contains
    target: ctx-sdui
  - type: contains
    target: ctx-decoding
  - type: contains
    target: ctx-payment
  - type: contains
    target: ctx-observability
---

# OpenPix JSR Architecture Knowledge Graph

Este índice é a porta de entrada para decisões, propostas e contextos do
backend. Cada nota tem um `id` global, metadados previsíveis e relações
direcionadas. Isso permite navegação no Obsidian hoje e extração para um grafo
ou busca semântica no futuro.

## Como navegar

- [[GRAPH-SCHEMA]] define o vocabulário dos metadados.
- [[ONTOLOGY]] define o alinhamento JSON-LD/RDF.
- [[CTX-PLATFORM]] reúne decisões transversais.
- [[CTX-SDUI]] reúne configuração e composição de telas.
- [[CTX-DECODING]] reúne interpretação de payloads Pix.
- [[CTX-PAYMENT]] reúne o ciclo de vida de pagamentos.
- [[CTX-OBSERVABILITY]] reúne saúde, métricas, logs e traces.

## RFCs

- [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- [[RFC-SDUI-001-mobile-context-and-component-compatibility]]
- [[RFC-DECODING-001-pix-payload-decoding-boundary]]
- [[RFC-PAYMENT-001-payment-lifecycle-and-idempotency]]
- [[RFC-OBSERVABILITY-001-operational-observability-interface]]

## ADRs

- [[ADR-PLATFORM-001-service-local-openapi-contracts]]
- [[ADR-SDUI-001-typed-request-context-dependencies]]
- [[ADR-SDUI-002-static-json-runtime-source]]
- [[ADR-DECODING-001-stateless-payload-decoding]]
- [[ADR-PAYMENT-001-aggregate-state-machine]]
- [[ADR-OBSERVABILITY-001-pull-based-operational-endpoints]]

## Artigos

- [[01-o-que-e-sdui]]
- [[02-contract-first-sdui-backend]]
- [[03-sdui-compatibility-prevention-reaction]]

## Regra de manutenção

Uma mudança arquitetural deve atualizar o documento que tomou a decisão, seus
links de entrada e saída e, quando aplicável, o contrato OpenAPI relacionado.
Decisões não são apagadas: são marcadas como `superseded` e apontam para a nova
decisão.

Depois de editar qualquer nó:

```bash
python3 scripts/build_knowledge_graph.py
python3 scripts/build_knowledge_graph.py --check
```

O Markdown é autoritativo. O arquivo
`generated/knowledge-graph.jsonld` é uma projeção determinística para GraphRAG,
triplestores ou outras ferramentas semânticas.
