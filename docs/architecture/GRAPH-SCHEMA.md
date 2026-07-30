---
id: graph-schema
type: schema
ontology: openpix-architecture-v1
title: Architecture Knowledge Graph Metadata Schema
status: active
context: platform
created: 2026-07-29
updated: 2026-07-29
tags:
  - architecture
  - knowledge-graph
  - metadata
relations:
  - type: governs
    target: architecture-index
---

# Metadados do knowledge graph

Todos os RFCs, ADRs e nós de contexto usam YAML frontmatter. O frontmatter é a
fonte estruturada; wikilinks no corpo existem para navegação humana.

## Campos obrigatórios

| Campo | Regra |
|---|---|
| `id` | Identificador global, estável e em kebab-case. |
| `type` | `context`, `rfc`, `adr`, `article`, `index` ou `schema`. |
| `ontology` | Versão do mapeamento, atualmente `openpix-architecture-v1`. |
| `title` | Nome legível da entidade. |
| `status` | Estado compatível com o tipo do documento. |
| `context` | Bounded context principal. |
| `created` | Data ISO `YYYY-MM-DD`. |
| `updated` | Última mudança semântica. |
| `tags` | Termos controlados e úteis para recuperação. |
| `relations` | Arestas tipadas para outros IDs globais. |

## Estados

- RFC: `draft`, `proposed`, `accepted`, `rejected`, `withdrawn`.
- ADR: `proposed`, `accepted`, `deprecated`, `superseded`.
- Contexto, índice e schema: `active` ou `deprecated`.
- Artigo: `draft`, `review`, `published`.

## Tipos de relação

Use verbos estáveis:

- `belongs_to`: documento pertence a um contexto;
- `contains`: índice agrega um conjunto de nós;
- `defines`: origem define um schema ou convenção;
- `proposes`: RFC propõe uma decisão ou capacidade;
- `decided_by`: proposta foi resolvida por um ADR;
- `resolves`: ADR resolve uma RFC;
- `implements`: artefato implementa uma decisão;
- `explains`: artigo ou guia explica uma decisão;
- `depends_on`: origem depende semanticamente do destino;
- `produces_for`: origem produz contrato consumível pelo destino;
- `observes`: origem coleta sinais sobre o destino;
- `observed_by`: contexto é observado por outro;
- `governs`: origem estabelece regras para o destino;
- `supersedes`: origem substitui uma decisão anterior;
- `related_to`: relação relevante sem dependência.

Cada `target` deve apontar para um `id` existente:

```yaml
relations:
  - type: belongs_to
    target: ctx-sdui
  - type: decided_by
    target: adr-sdui-001
```

## Regras para busca semântica

1. Um documento trata uma decisão principal.
2. Títulos e resumos descrevem o problema, não apenas a tecnologia.
3. Acrônimos são expandidos na primeira ocorrência.
4. Alternativas rejeitadas permanecem registradas.
5. IDs não mudam quando arquivos são movidos.
6. Relações importantes aparecem no frontmatter e em `## Knowledge graph`.
7. Dados secretos, payloads Pix e identificadores pessoais não entram nas notas.

## Convenção de nomes

```text
CTX-<CONTEXTO>.md
RFC-<CONTEXTO>-<NNN>-<slug>.md
ADR-<CONTEXTO>-<NNN>-<slug>.md
```

O basename é único em todo o vault para que wikilinks do Obsidian funcionem
sem depender do caminho físico.

## Projeção interoperável

Os IDs locais são expandidos sob `https://openpix.dev/knowledge/`. Tipos e
relações são mapeados pelo [[ONTOLOGY]] para Dublin Core, Schema.org, SKOS e o
vocabulário OpenPix. O JSON-LD é derivado e nunca deve ser editado manualmente:

```bash
python3 scripts/build_knowledge_graph.py
python3 scripts/build_knowledge_graph.py --check
```

## Knowledge graph

- Governado por [[README|Architecture Knowledge Graph]].
- Ontologia: [[ONTOLOGY]].
- Aplicado por [[RFC-PLATFORM-001-contract-first-service-boundaries]].
