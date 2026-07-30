---
id: rfc-platform-001
type: rfc
ontology: openpix-architecture-v1
title: Contract-First Boundaries for OpenPix JSR Backend Services
status: accepted
context: platform
created: 2026-07-29
updated: 2026-07-29
tags: [rfc, platform, contract-first, openapi, bounded-context]
relations:
  - type: belongs_to
    target: ctx-platform
  - type: decided_by
    target: adr-platform-001
  - type: governs
    target: rfc-sdui-001
  - type: governs
    target: rfc-decoding-001
  - type: governs
    target: rfc-payment-001
  - type: governs
    target: rfc-observability-001
---

# RFC-PLATFORM-001: Contract-first service boundaries

## Summary

Cada serviço publica seu próprio contrato OpenAPI e expõe somente conceitos do
bounded context que possui. Integrações acontecem por contratos versionados,
nunca por classes, tabelas ou modelos internos compartilhados.

## Motivation

Um repositório único facilita o início do projeto, mas também facilita
acoplamentos silenciosos. Sem limites explícitos, SDUI pode começar a carregar
estado de pagamento, decoding pode criar transações e observability pode virar
um depósito de dados de negócio.

## Proposal

- `sdui-service` possui configuração e telas.
- `decoding-service` possui interpretação de payloads.
- `payment-service` possui o ciclo de vida de Payment.
- `observability-service` possui interfaces operacionais.
- cada serviço mantém `<service>/contracts/openapi.yaml`;
- erros HTTP seguem Problem Details com `code` e `correlationId`;
- correlação e W3C Trace Context atravessam fronteiras;
- API version, contract version e content revision permanecem conceitos
  distintos;
- mudanças incompatíveis criam uma nova versão pública.

## Alternatives

### Um contrato central monolítico

Facilita descoberta inicial, mas confunde ownership e faz uma alteração local
parecer uma release coordenada de toda a plataforma.

### Compartilhar modelos entre serviços

Reduz duplicação aparente, porém transfere o acoplamento para build e runtime,
além de não funcionar de forma saudável entre Python e Java.

## Compatibility

Mudanças aditivas são preferidas. Enum e discriminator exigem atenção especial,
pois um cliente antigo pode não reconhecer um novo valor. Todo consumidor deve
tratar extensões desconhecidas de forma segura.

## Security

Contratos não tornam dados confiáveis. Headers enviados pelo cliente são
contexto não confiável; autenticação e autorização devem vir de identidade
validada. Tokens, payloads Pix, chaves e dados pessoais não podem aparecer em
logs ou exemplos reais.

## Rollout

1. Publicar contratos locais.
2. Validar YAML e referências em CI.
3. Validar exemplos contra schemas.
4. Adicionar contract tests por consumidor.
5. Publicar artefatos versionados quando houver múltiplos repositórios.

## Knowledge graph

- Contexto: [[CTX-PLATFORM]]
- Decisão: [[ADR-PLATFORM-001-service-local-openapi-contracts]]
- Governados: [[RFC-SDUI-001-mobile-context-and-component-compatibility]],
  [[RFC-DECODING-001-pix-payload-decoding-boundary]],
  [[RFC-PAYMENT-001-payment-lifecycle-and-idempotency]] e
  [[RFC-OBSERVABILITY-001-operational-observability-interface]].
