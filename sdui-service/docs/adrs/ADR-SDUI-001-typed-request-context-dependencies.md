---
id: adr-sdui-001
type: adr
ontology: openpix-architecture-v1
title: Parse Mobile Headers with Typed FastAPI Dependencies
status: accepted
context: sdui
created: 2026-07-29
updated: 2026-07-29
tags: [adr, sdui, fastapi, dependency-injection, headers]
relations:
  - type: belongs_to
    target: ctx-sdui
  - type: resolves
    target: rfc-sdui-001
  - type: related_to
    target: adr-sdui-002
---

# ADR-SDUI-001: Typed request context dependencies

## Status

Accepted and implemented.

## Context

Os endpoints de configuração e tela repetiam a declaração de headers de app,
região, locale, capabilities, correlação, tracing e cache. A repetição aumenta
o risco de aliases e validações divergirem.

## Decision

Usar dependências FastAPI com `Annotated`:

- `get_mobile_request_context` normaliza o contexto compartilhado;
- `get_sdui_request_context` acrescenta as versões de contrato e componentes;
- endpoints recebem `MobileRequestContext` ou `SduiRequestContext`;
- parâmetros das dependências continuam aparecendo no OpenAPI gerado.

## Why not a decorator

Decorators escondem a assinatura da operação, exigem cuidado para preservar
metadata e integram pior com validação/OpenAPI. `Depends` faz parte do modelo de
execução do FastAPI e mantém tipos visíveis.

## Consequences

### Positive

- uma regra para cada header;
- endpoint focado no caso de uso;
- contextos imutáveis e testáveis;
- documentação automática preservada.

### Negative

- a função de dependência concentra muitos parâmetros;
- contexto de cliente continua não confiável;
- alterações transversais afetam todos os endpoints consumidores.

## Verification

Testes confirmam headers únicos no OpenAPI runtime, Problem Details para
validação inválida e normalização de capabilities/versões.

## Knowledge graph

- Resolve [[RFC-SDUI-001-mobile-context-and-component-compatibility]].
- Relaciona-se a [[ADR-SDUI-002-static-json-runtime-source]].
- Pertence a [[CTX-SDUI]].
