---
id: sdui-medium-brief
type: brief
ontology: openpix-architecture-v1
title: Medium brief — sdui context
status: active
context: sdui
relations:
  - type: belongs_to
    target: ctx-sdui
---

# Medium brief — contexto sdui

Os artigos completos gerados a partir deste contexto **não vivem neste
repositório**. Eles são publicados em `pix-jsr-publication`:

```text
/home/josiel/Documents/git/articles/medium/pix-jsr-publication/part0-intro/backend/
├── 01-o-que-e-sdui.md
├── 02-contract-first-sdui-backend.md
└── 03-sdui-compatibility-prevention-reaction.md
```

Este arquivo guarda apenas o necessário para regenerar ou atualizar esses
artigos a partir do backend, sem duplicar o texto final aqui.

## Do que cada artigo trata

1. **O que é SDUI** — responsabilidades de backend e cliente, analogia com
   carteiras digitais (Samsung/Google/Apple Wallet), trade-offs, quando não
   usar. Perfil B (não é específico do Pix JSR).
2. **Contract-first SDUI backend** — como este serviço trata contrato,
   catálogo, versionamento e validação antes da publicação.
3. **SDUI compatibility: prevention vs reaction** — como o backend previne
   telas incompatíveis (headers do cliente) e como o cliente reage a
   componentes que não conhece (fallback seguro).

## Onde está a decisão técnica por trás de cada artigo

- [[ADR-SDUI-001-typed-request-context-dependencies]] — `../adrs/`
- [[ADR-SDUI-002-static-json-runtime-source]] — `../adrs/`
- [[RFC-SDUI-001-mobile-context-and-component-compatibility]] — `../rfcs/`
- Diagramas de origem (Mermaid/Excalidraw): `../diagrams/`
- Contexto cruzado: `../../../docs/architecture/contexts/CTX-SDUI.md`

Ao atualizar um artigo publicado, atualize primeiro a decisão técnica aqui;
o artigo em `pix-jsr-publication` deve refletir a decisão, não o contrário.
