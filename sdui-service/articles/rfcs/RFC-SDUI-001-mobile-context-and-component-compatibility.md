---
id: rfc-sdui-001
type: rfc
ontology: openpix-architecture-v1
title: Mobile Context and Layered SDUI Compatibility
status: accepted
context: sdui
created: 2026-07-29
updated: 2026-07-29
tags: [rfc, sdui, mobile-context, compatibility, renderer]
relations:
  - type: belongs_to
    target: ctx-sdui
  - type: depends_on
    target: rfc-platform-001
  - type: decided_by
    target: adr-sdui-001
  - type: related_to
    target: adr-sdui-002
---

# RFC-SDUI-001: Mobile context and layered compatibility

## Summary

O cliente declara contexto e capacidade de interpretação por headers. O
servidor usa essas informações para evitar conteúdo sabidamente incompatível,
mas cada componente também retorna `compatibilityVersion`; o renderer mantém a
responsabilidade final de falhar com segurança.

## Problem

App build, país, locale, capability de produto e versão do renderer evoluem em
ritmos diferentes. Usar somente `X-App-Version` acopla o schema SDUI à release
do aplicativo. Usar somente uma lista de componentes também não cobre mudanças
no documento como um todo.

## Proposal

O request móvel inclui:

- `X-App-Platform`, `X-App-Version`, `X-App-Build` e `X-App-Package`;
- país, idioma, timezone e moeda como dimensões independentes;
- `X-App-Capabilities` para features de produto;
- `X-SDUI-Contract-Version` para o envelope;
- `X-SDUI-Component-Versions` como mapa compacto `type=version`;
- correlação, trace context e validators de cache.

Cada componente retorna:

```json
{
  "type": "text",
  "compatibilityVersion": ["1"]
}
```

O servidor responde `406` quando detecta incompatibilidade. Ainda assim, o
cliente deve reconhecer `(type, version)`, aplicar fallback ou rejeitar a tela
quando não puder renderizá-la com segurança.

## Why both layers

O header reduz respostas inúteis e permite seleção server-side. O campo no
componente torna a representação autodescritiva e protege contra configuração
incorreta, cache antigo ou evolução parcial. Nenhuma das camadas, isoladamente,
é uma garantia absoluta.

## Alternatives

### Apenas app build

É compacto, mas obriga o servidor a conhecer toda a matriz entre build e
renderer.

### Apenas versão por componente na resposta

Mantém o documento autodescritivo, mas o servidor descobre a incompatibilidade
somente depois de enviar uma tela possivelmente inutilizável.

### Manifest completo do renderer no body

Escala para catálogos extensos, porém adiciona uma chamada ou payload de
negociação que ainda não é necessário.

## Limits

O mapa em header deve ter limites de itens e bytes. Se o catálogo crescer a
ponto de pressionar limites de infraestrutura, uma versão agregada do renderer
ou um manifest versionado deve substituir a enumeração, via nova RFC.

## Acceptance criteria

- headers são parseados uma vez;
- versões incompatíveis resultam em Problem Details `406`;
- `compatibilityVersion` é obrigatório e não vazio;
- cliente continua tratando componente desconhecido;
- cache varia pelas dimensões que alteram a representação.

## Knowledge graph

- Contexto: [[CTX-SDUI]]
- Implementação de contexto: [[ADR-SDUI-001-typed-request-context-dependencies]]
- Fonte atual: [[ADR-SDUI-002-static-json-runtime-source]]
- Governança: [[RFC-PLATFORM-001-contract-first-service-boundaries]]
