---
id: adr-decoding-001
type: adr
ontology: openpix-architecture-v1
title: Stateless Payload Decoding
status: accepted
context: decoding
created: 2026-08-05
updated: 2026-08-05
tags: [adr, decoding, stateless, pix, contract-first]
relations:
  - type: belongs_to
    target: ctx-decoding
  - type: resolves
    target: rfc-decoding-001
  - type: governed_by
    target: rfc-platform-001
  - type: produces_for
    target: ctx-payment
  - type: observed_by
    target: ctx-observability
---

# ADR-DECODING-001: Stateless Payload Decoding

## Status

Accepted.

## Context

O backend é um monorepo com serviços de ownership independente. Decodificar um
BR Code é uma operação pura (payload em, instrução interpretada out), mas sem
uma fronteira explícita ela poderia vazar para criação de pagamento, persistência
ou regras de PSP, acoplando parsing a ciclo de vida.

## Decision

`decoding-service` é um serviço stateless:

- um único endpoint estrito `POST /decode/v1/pix-payloads`;
- nenhuma persistência e nenhuma criação de pagamento;
- inválidos (CRC, moeda não-BRL, TLV malformado, chave desconhecida) respondem
  422 via Problem Details, sem leniência;
- contract-first: `contracts/openapi.yaml` é o único interface e é servido
  verbatim pelo app FastAPI;
- modelos gerados a partir do contrato (padrão `sdui-service`, via
  `datamodel-code-generator`).

## Consequences

### Positive

- parsing e interpretação são testáveis em isolamento e reutilizáveis;
- o Payment context consome a instrução diretamente, sem reimplementar regras;
- payloads e chaves não são persistidos nem logados, reduzindo superfície de
  dados sensíveis;
- contrato único evita drift entre schema servido e schema publicado.

### Negative

- strictness rejeita BR Codes não conformes emitidos por alguns emissores;
  leniência é possível como follow-up se um cliente concreto precisar;
- a instrução é um primeiro chute de schema; o Payment context pode exigir
  evolução aditiva.

## Rejected alternatives

- Validar e interpretar em dois endpoints (validate/interpret) — YAGNI, o
  consumidor pode usar a instrução diretamente.
- Decodificação leniente com warnings na resposta — respostas "talvez" não são
  determinísticas.
- Persistir payloads ou instruções decodificadas — viola a fronteira stateless
  e aumenta exposição de dados.

## Verification

Evidência observada nesta implementação:

- 132 testes passando via `decoding-service/.venv/bin/python -m pytest`.
- Schema OpenAPI servido igual a `contracts/openapi.yaml` (assertado em teste:
  `main.app.openapi() == yaml.safe_load(contrato)`).
- CRC16-CCITT verificado contra vetores conhecidos externos (strings
  Odoo/pypix), com CRCs `A5C7`, `F1E4`, `90CA`, `B659`, `9182` e `2D75`; o vetor
  `p5` (`2D75`) decodifica agora como instrução dinâmica baseada em localização
  (tag 26.25), sem chave. Um vetor pypix cujo CRC declarado não batia foi
  corrigido por recomputação contra `binascii.crc_hqx(..., 0xFFFF)`.
- Ciclo de revisão do conselho pós-implementação: revisão multi-modelo; todas
  as conclusões foram tratadas, incluindo a decisão de escopo de suporte à
  localização dinâmica (key XOR location).

## Superseded

None.

## Knowledge graph

- Resolve [[RFC-DECODING-001-pix-payload-decoding-boundary]].
- Pertence a [[CTX-DECODING]].
- Governado por [[RFC-PLATFORM-001-contract-first-service-boundaries]].
- Produz para [[CTX-PAYMENT]].
- Observado por [[CTX-OBSERVABILITY]].
