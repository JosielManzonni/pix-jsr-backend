---
id: adr-observability-001
type: adr
ontology: openpix-architecture-v1
title: Pull-Based Operational Endpoints
status: accepted
context: observability
created: 2026-07-29
updated: 2026-08-07
tags: [adr, observability, health, ready, metrics, pull, network-protection]
relations:
  - type: belongs_to
    target: ctx-observability
  - type: resolves
    target: rfc-observability-001
  - type: governed_by
    target: rfc-platform-001
  - type: observes
    target: ctx-sdui
  - type: observes
    target: ctx-decoding
  - type: observes
    target: ctx-payment
---

# ADR-OBSERVABILITY-001: Pull-Based Operational Endpoints

## Status

Accepted.

## Context

Serviços precisam de pontos de verificação operacional (liveness/readiness) e
de coleta de métricas. O mecanismo escolhido é pull-based: o orquestrador
(ou coletor) consulta os endpoints; não há agente push nem agregação central
ainda. A proteção do endpoint de métricas foi definida como "rede e/ou
credencial". Uma readiness mal projetada pode causar cascata: se `/ready`
depende de outros serviços, uma falha observada derruba a própria
observabilidade.

## Decision

- `GET /health` (liveness) e `GET /ready` (readiness) na porta da API, parte
  do contrato OpenAPI de cada serviço, nunca cacheados, sem dados sensíveis.
- `/ready` reflete somente o processo dono — nunca a readiness de serviços
  observados — aplicando estritamente o aviso de cascata.
- `GET /metrics` em **porta separada** (`METRICS_PORT`), servindo Prometheus
  text exposition format 0.0.4. A porta separada é a forma aceita de proteção
  "por rede" da definição original: operação restringe exatamente essa porta
  por política de rede, e nenhum esquema de credencial em-app é inventado
  (não existe contexto de identidade no sistema ainda).
- `/metrics` é deliberadamente ausente do contrato OpenAPI: a superfície de
  contrato permanece JSON pura e a invariante runtime==contrato se mantém por
  porta.
- Cada serviço roda dois listeners em um processo: porta da API e porta de
  métricas. Portas vêm do ambiente (`APP_PORT`, `METRICS_PORT`).
- Um pacote compartilhado (`openpix_observability`, hospedado pelo
  observability-service) provê o formatter de logs estruturados (key=value com
  `trace_id`/`correlation_id`), o middleware de W3C Trace Context e o setup de
  métricas com labels limitados (operationId).

## Consequences

### Positive

- Superfície operacional uniforme entre sdui, decoding e observability.
- Invariante runtime==contrato preservada; formato de métricas versionado pela
  media type (`version=0.0.4`), não pela versão do contrato.
- Sem código de auth inventado; a rede é o controle.
- Readiness não derruba observabilidade em cascata.

### Negative

- Uma porta de métricas mal exposta no deployment vazaria telemetria de
  plataforma; a restrição de rede é um gate de deployment obrigatório
  (documentado nos `AGENTS.md` dos serviços).
- O pacote compartilhado acopla serviços em tempo de build; aceito porque é a
  infraestrutura que esta RFC atribui a este contexto, e integração de negócio
  continua somente por contratos.

## Rejected alternatives

- `/metrics` no contrato e na porta da API — exigiria resposta schema-less ou
  wrapper JSON que quebra o scraping Prometheus e a pureza JSON do contrato.
- Credencial em-app para `/metrics` — inventaria comportamento de identidade
  que pertence a um futuro contexto de auth/pagamento.
- Readiness dependente de serviços observados — cascata de falhas; rejeitado.
- Agente push/agregação central de status — sem consumidor concreto; follow-up
  quando existir.

## Verification

Evidência observada nesta implementação:

- `observability-service`: 35 testes passando (pacote compartilhado + serviço,
  incl. teste de integração dos dois listeners com sockets reais).
- `sdui-service`: 37 testes passando (27 existentes + 10 observability).
- `decoding-service`: 143 testes passando (132 existentes + 11 observability),
  incluindo `main.app.openapi() == contrato` com as novas paths de probe.
- Media type `text/plain; version=0.0.4; charset=utf-8` verificada no
  `prometheus-client` 0.21.1 instalado; collectors default (process, platform,
  GC) presentes no registry.
- Data policy verificada por teste: payload e material de chave ausentes de
  logs e métricas; correlation IDs ausentes de labels.
- Ciclo de revisão: checkpoint pós-observability-service e pós-retrofit com
  revisão do diff completo; achados tratados (cap de 128 do correlation id no
  middleware, ordem de imports).

## Superseded

None.

## Knowledge graph

- Resolve [[RFC-OBSERVABILITY-001-operational-observability-interface]].
- Pertence a [[CTX-OBSERVABILITY]].
- Governado por [[RFC-PLATFORM-001-contract-first-service-boundaries]].
- Observa [[CTX-SDUI]], [[CTX-DECODING]], [[CTX-PAYMENT]].
