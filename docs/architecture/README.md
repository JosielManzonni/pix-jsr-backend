---
id: architecture-index
type: index
ontology: openpix-architecture-v1
title: OpenPix JSR Architecture Knowledge Graph
status: active
context: platform
created: 2026-07-29
updated: 2026-08-09
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
  - type: contains
    target: ref-bacen-pix-dict
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
- [[ref-bacen-pix-dict|BACEN Pix/DICT]] é a referência canônica externa (regulamento, manual DICT, API DICT).

## Onde vivem as decisões

Este índice reúne apenas o que é transversal a mais de um serviço:
schema de metadados, ontologia, contextos e o knowledge graph gerado.

ADRs, RFCs e diagramas de um contexto **implementado** ficam junto do
serviço que o possui, não aqui:

- **sdui** → `sdui-service/docs/{adrs,rfcs,diagrams}`
- **decoding** → `decoding-service/docs/{adrs,rfcs}`
- **payment** → ainda não implementado como serviço; a proposta vive em
  `openspec/changes/add-payment-service/` até ser arquivada.
- **observability** → ainda não implementado; nenhum ADR/RFC existe além do
  contexto documentado em [[CTX-OBSERVABILITY]].

Apenas decisões verdadeiramente cross-service ficam neste `docs/architecture/`:

## RFCs (cross-cutting)

- [[RFC-PLATFORM-001-contract-first-service-boundaries]]

## ADRs (cross-cutting)

- [[ADR-PLATFORM-001-service-local-openapi-contracts]]

Os artigos do Medium gerados a partir deste backend não vivem neste
repositório. Eles são publicados em `pix-jsr-publication`; cada serviço
guarda o brief necessário para regerá-los em `<service>/docs/medium/`
(ver `sdui-service/docs/medium/README.md`).

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
