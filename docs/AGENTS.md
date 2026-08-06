# AGENTS.md — docs/

Guidance for editing documentation in this repository.

## Source of truth

- `architecture/` is the authoritative reference. Any architectural change
  must be reflected here, not only in code.
- `architecture/generated/knowledge-graph.jsonld` is a deterministic derived
  projection of the Markdown. Never edit it by hand.

## Frontmatter and wikilinks

- Every note in `architecture/` has frontmatter with a global `id`, `type`,
  `status`, and `relations`. Preserve this shape.
- Update the document that made a decision, its in/out links, and the related
  OpenAPI contract when applicable.
- Superseded decisions are marked `superseded` in frontmatter, not deleted.

## Generated artifact caution

- The JSON-LD graph is derived. Changing it by hand is invalid; rebuild from
  Markdown instead.
- The documented rebuild commands in `architecture/README.md`
  (`python3 scripts/build_knowledge_graph.py` and `--check`) cannot run here:
  `scripts/` does not exist. Do not claim the graph was rebuilt.
