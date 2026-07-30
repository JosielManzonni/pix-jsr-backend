---
id: architecture-ontology
type: schema
ontology: openpix-architecture-v1
title: OpenPix JSR Architecture Ontology
status: active
context: platform
created: 2026-07-29
updated: 2026-07-29
tags: [architecture, ontology, json-ld, rdf]
relations:
  - type: defines
    target: graph-schema
  - type: governs
    target: architecture-index
---

# OpenPix JSR Architecture Ontology

Markdown continua sendo a fonte de verdade. A ontologia define como o
frontmatter é projetado para JSON-LD/RDF sem exigir que autores editem triples.

## Namespaces reutilizados

| Prefixo | Uso |
|---|---|
| `dcterms` | título, datas, relações documentais e subjects |
| `schema` | artigo, texto e caminho do documento |
| `skos` | conceitos que representam bounded contexts |
| `prov` | base para proveniência futura |
| `openpix` | RFC, ADR e relações específicas da arquitetura |

O namespace do projeto é `https://openpix.dev/ontology/`. IDs locais são
expandidos como `https://openpix.dev/knowledge/{id}` durante a geração.

## Tipos

| Frontmatter | Classe JSON-LD |
|---|---|
| `rfc` | `openpix:RequestForComments` |
| `adr` | `openpix:ArchitectureDecision` |
| `context` | `openpix:ArchitectureContext` e `skos:Concept` |
| `article` | `schema:TechArticle` |
| `index` | `openpix:ArchitectureIndex` |
| `schema` | `openpix:MetadataSchema` |

## Relações

As relações legíveis do frontmatter são convertidas em predicates:

```yaml
relations:
  - type: resolves
    target: rfc-sdui-001
```

```json
{
  "resolves": [
    "https://openpix.dev/knowledge/rfc-sdui-001"
  ]
}
```

O mapeamento normativo está em `context.jsonld`; as classes e propriedades
próprias estão em `openpix-architecture.ttl`.

## Geração

Na raiz do repositório:

```bash
python3 scripts/build_knowledge_graph.py
python3 scripts/build_knowledge_graph.py --check
```

O primeiro comando gera
`docs/architecture/generated/knowledge-graph.jsonld`. O segundo não altera
arquivos e falha quando o artefato está desatualizado ou o grafo é inválido,
sendo adequado para CI.

## Knowledge graph

- Metadados: [[GRAPH-SCHEMA]]
- Índice: [[README|Architecture Knowledge Graph]]
