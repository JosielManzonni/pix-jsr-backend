# AGENTS.md — openspec/

Guidance for agents working in the OpenSpec layer of this repository.

The spec layer of the repository. Holds the change lifecycle
(`openspec/changes/`, archived changes) and the aggregated capability specs
(`openspec/specs/`).

## Two layers, mutually aware

- `openspec/` is the SPEC layer: behavioral requirements, Given/When/Then
  scenarios, SHALL/MUST contracts, aggregated per capability in
  `openspec/specs/<capability>/spec.md`.
- `docs/` is the ARCHITECTURE layer: context, decisions, rationale, structure
  (`docs/architecture` RFCs, ADRs, contexts).
- The layers are separate and one does not replace the other: a spec states
  what must hold; an architecture note records why and how.
- They must stay aware of each other: a fact stated in one layer must be
  reflected or referenced in the other. Drift between an archived spec and
  `docs/architecture` is a defect.

## Change lifecycle

- House-style flow: `/opsx-propose` (proposal/design/specs/tasks/plan) →
  `/house-apply` (test-first implementation, `verify.md`, `tasks.md`
  checkboxes) → `/house-archive` (retrospective, archive move, spec
  aggregation into `openspec/specs/`).
- Reference the commands (`opsx-propose`, `house-apply`, `house-archive`) and
  the skills (`openspec-house-style`, `openspec-propose`,
  `openspec-apply-change`, `openspec-archive-change`) by name.

## Archive means reconcile with docs

- After a change is archived and made canonical (aggregated into
  `openspec/specs/`), it MUST be reconciled with the documentation layer. The
  archive step is not complete until `docs/architecture` reflects the
  canonical spec:
  - Create or update the RFC/ADR notes for the affected capability
    (`docs/architecture/rfcs/`, `adrs/`).
  - Resolve knowledge-graph links: contexts (`CTX-*`) and the README RFC/ADR
    indexes.
  - Update service ownership maps in the root `AGENTS.md` when a service's
    contract or existence changed.
  - Update the owning service's OpenAPI contract when the canonical spec
    changed it.
  - Mark superseded decisions `superseded` in frontmatter, never delete.
  - Never hand-edit `docs/architecture/generated/knowledge-graph.jsonld`
    (derived; rebuild scripts missing in this repo — do not claim a rebuild).
- If docs were updated during implementation, verify after archiving that they
  still match the aggregated spec exactly (no drift).

## Conventions

- `changes/` is transient lifecycle state; `archive/` is the historical
  record; `specs/` is canonical.
- `config.yaml` pins the schema (`house-style`).
- Specs use SHALL/MUST in requirement statements.
