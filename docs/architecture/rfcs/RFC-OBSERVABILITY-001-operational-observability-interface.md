---
id: rfc-observability-001
type: rfc
ontology: openpix-architecture-v1
title: Operational Observability Interface
status: accepted
context: observability
created: 2026-07-29
updated: 2026-08-07
tags: [rfc, observability, health, ready, metrics, traces, logs]
relations:
  - type: belongs_to
    target: ctx-observability
  - type: decided_by
    target: adr-observability-001
  - type: governed_by
    target: rfc-platform-001
  - type: observes
    target: ctx-sdui
  - type: observes
    target: ctx-decoding
  - type: observes
    target: ctx-payment
---

# RFC-OBSERVABILITY-001: Operational Observability Interface

## Summary

Todo serviço expõe a mesma superfície operacional: `GET /health` (liveness),
`GET /ready` (readiness) e `GET /metrics` (Prometheus text exposition format
0.0.4) em uma **porta separada** da porta da API. Logs estruturados carregam
`trace_id` e `correlation_id`. O observability-service hospeda o pacote de
instrumentação compartilhado (`openpix_observability`) usado por todos os
serviços.

## Motivation

Sem uma interface operacional comum, cada serviço inventa sua própria
liveness, readiness e formato de métricas, e operação não consegue distinguir
"processo morto" de "processo vivo mas não-ready" nem coletar telemetria de
forma uniforme. A ADR de pull-based endpoints define o mecanismo; esta RFC
define o formato comum da interface.

## Proposal

### Probes na porta da API, parte do contrato

- `GET /health` — liveness: 200 quando o processo está vivo e servindo. Sem
  dependências, nunca cacheada, sem dados sensíveis.
- `GET /ready` — readiness: 200 quando o processo pode aceitar trabalho.
  Reflete somente o próprio processo: nunca depende da readiness de serviços
  observados (aviso de cascata da ADR aplicado estritamente).
- Ambos declaram `ServiceStatus` (`{"status": "ok"}`) no contrato OpenAPI de
  cada serviço (bump aditivo: decoding 1.0.0 → 1.1.0, sdui 1.1.0 → 1.2.0).

### Métricas em porta separada, fora do contrato

- `GET /metrics` na porta de métricas (`METRICS_PORT`, default 9100), servindo
  Prometheus text exposition format 0.0.4 (`text/plain; version=0.0.4;
  charset=utf-8`).
- A porta separada é a forma aceita de proteção "por rede" da ADR: operação
  restringe exatamente essa porta por política de rede. Nenhum esquema de
  credencial em-app é inventado (não existe contexto de identidade ainda).
- O endpoint de métricas é deliberadamente ausente dos contratos OpenAPI: a
  superfície de contrato permanece JSON pura e a invariante
  runtime==contrato se mantém por porta.

### Traces e logs estruturados

- W3C Trace Context: `traceparent`/`tracestate` aceitos; quando ausentes, um
  contexto novo `00-<32 hex>-<16 hex>-01` é gerado. `tracestate` propaga
  somente com `traceparent` válido (regra W3C).
- Logs estruturados key=value via formatter stdlib: cada linha carrega
  `trace_id` e `correlation_id` (vazios quando sem contexto de request).
- `X-Correlation-ID` continua header de aceite/reflexo como hoje; o
  middleware resolve o id efetivo (header ou gerado, máx. 128) uma única vez
  por request para que logs e respostas concordem.

### Data policy

- Tokens, payloads, chaves Pix, contas, documentos e idempotency IDs nunca
  aparecem como atributos de telemetria (métricas, logs, exemplos).
- Correlation IDs nunca viram labels de métricas. Labels vêm de um conjunto
  limitado (OpenAPI operationId).

## Alternatives

### Endpoints operacionais empurrados (push) para um agregador

Uma "visão operacional" central com status agregado foi considerada; sem
consumidor concreto, a agregação é follow-up quando existir.

### Métricas no mesmo contrato, porta da API

Expor `/metrics` no contrato exigiria resposta schema-less `text/plain` ou
wrapper JSON que quebraria o scraping Prometheus e o contrato puro JSON.
Rejeitado em favor da porta separada (ver ADR-OBSERVABILITY-001).

## Compatibility

A superfície operacional é aditiva e idempotente: probes não mudam respostas
de negócio nem códigos de erro. Serviços novos devem expor exatamente a mesma
superfície.

## Security

Probes e métricas não expõem endereços, credenciais ou detalhes sensíveis.
A porta de métricas deve ser restrita por política de rede no deployment;
expor telemetria de plataforma é um gate de deployment, não um comportamento
de código.

## Rollout

1. Publicar `observability-service/contracts/openapi.yaml` e os bumps aditivos
   de sdui/decoding.
2. Adicionar `/health` e `/ready` ao contrato e aos apps.
3. Adicionar a porta de métricas (listeners gêmeos em um processo).
4. Restringir a porta de métricas por rede no deployment (gate documentado em
   cada `AGENTS.md` de serviço).

## Spec

A especificação comportamental canônica (SHALL/MUST, cenários
Given/When/Then) vive em `openspec/specs/operational-observability/spec.md`,
agregada no archive do change `add-observability-service`. Esta nota registra o
porquê e o como; a spec registra o quê.

## Knowledge graph

- Contexto: [[CTX-OBSERVABILITY]]
- Decisão: [[ADR-OBSERVABILITY-001-pull-based-operational-endpoints]]
- Governado por: [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- Observa: [[CTX-SDUI]], [[CTX-DECODING]], [[CTX-PAYMENT]]

> Nota (derivação): `docs/architecture/generated/knowledge-graph.jsonld` NÃO é
> reconstruído por esta mudança — `scripts/` não existe neste repositório. O
> artefato é uma projeção derivada e não deve ser editado à mão; o grafo não
> refletirá as novas notas até que um script de build exista.
