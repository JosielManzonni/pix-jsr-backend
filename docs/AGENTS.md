# AGENTS.md — docs/

Guidance for editing documentation in this repository.

## Source of truth

- `architecture/` is the authoritative reference. Any architectural change
  must be reflected here, not only in code.
- `architecture/generated/knowledge-graph.jsonld` is a deterministic derived
  projection of the Markdown. Never edit it by hand.

## OpenSpec layer awareness

- `docs/` and `openspec/` are two separate layers of the same repository:
  `docs/` records architecture (context, decisions, rationale); `openspec/`
  records behavioral requirements (specs, Given/When/Then, SHALL/MUST).
- They are mutually aware: the canonical spec of a capability lives in
  `openspec/specs/`; `docs/architecture` notes (RFCs/ADRs/contexts) must
  reflect archived specs — when a change is archived and made canonical,
  reconcile docs with it.
- When editing `docs/`: check the related `openspec/specs/<capability>/spec.md`
  for behavioral constraints; do not state facts in docs that contradict a
  canonical spec, and reference the spec rather than duplicating it.
- When an openspec change archives a new canonical spec: update the relevant
  RFC/ADR, resolve knowledge-graph links, update service ownership (root
  `AGENTS.md`), and keep the OpenAPI contract in sync. Drift between layers is
  a defect.
- `openspec/AGENTS.md` defines the spec layer side of this relationship.

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
