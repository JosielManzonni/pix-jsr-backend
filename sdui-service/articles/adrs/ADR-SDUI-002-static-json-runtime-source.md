---
id: adr-sdui-002
type: adr
ontology: openpix-architecture-v1
title: Use Validated Static JSON as the Initial SDUI Source
status: accepted
context: sdui
created: 2026-07-29
updated: 2026-07-29
tags: [adr, sdui, json, pydantic, incremental-delivery]
relations:
  - type: belongs_to
    target: ctx-sdui
  - type: related_to
    target: rfc-sdui-001
  - type: depends_on
    target: adr-sdui-001
---

# ADR-SDUI-002: Validated static JSON source

## Status

Accepted as an interim decision.

## Context

O primeiro milestone precisa estabilizar contratos e comportamento HTTP antes
de introduzir banco, migrations e workflow de publicação.

## Decision

`configuration.json` e `screens.json` são as fontes runtime. `utils.py` lê e
localiza documentos sem depender de FastAPI; `main.py` converte os dicionários
para os modelos Pydantic gerados do OpenAPI.

ETags são derivados da representação canônica. Arquivo ausente, JSON inválido,
tela desconhecida e schema inválido são traduzidos para Problem Details.

## Consequences

### Positive

- ciclo local curto;
- fixtures legíveis e versionadas;
- schema é validado antes da resposta;
- persistência não é adicionada sem necessidade.

### Negative

- não existe publicação transacional;
- edição exige deploy;
- não há audit trail, rollback formal ou concorrência;
- referências cruzadas ainda precisam de validação de publicação.

## Exit criteria

Esta ADR deverá ser superseded quando Admin API e publicação exigirem drafts,
revisões imutáveis, rollback e auditoria persistida.

## Knowledge graph

- Contexto: [[CTX-SDUI]]
- Compatibilidade: [[RFC-SDUI-001-mobile-context-and-component-compatibility]]
- Contexto HTTP: [[ADR-SDUI-001-typed-request-context-dependencies]]
