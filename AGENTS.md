# AGENTS.md

Agentic coding guidance for this repository. Authoritative reference is the
architecture documentation under `docs/architecture/` (read it before any
architectural change).

## Bounded contexts

The architecture documents four bounded contexts plus a cross-cutting platform
context. Each is owned by its own service directory:

- **sdui** — mobile configuration, evaluated feature availability, SDUI screen
  composition, renderer compatibility.
- **decoding** — Pix payload interpretation.
- **payment** — payment lifecycle and idempotency.
- **observability** — health, metrics, logs, traces.

Implemented services:

- `sdui-service/` — owns the **sdui** context. Tests: `python -m pytest` from
  `sdui-service/`.
- `decoding-service/` — owns the **decoding** context. Tests:
  `.venv/bin/python -m pytest` from `decoding-service/`.

`payment` and `observability` are documented boundaries only; do not create
them or invent their behavior.

## Source of truth

- Markdown under `docs/architecture/` is authoritative.
- `docs/architecture/generated/knowledge-graph.jsonld` is a deterministic
  derived projection; never edit it by hand.
- Each service directory owns its runtime and its contract
  (`sdui-service/contracts/openapi.yaml`, `decoding-service/contracts/openapi.yaml`).
  Contract changes belong with that service.

## Rules

- Respect service ownership and contract-first boundaries: interfaces between
  services are the OpenAPI contracts, not internal coupling.
- Any architectural change must update the relevant `docs/architecture/`
  notes (decision docs, their in/out links, and the related OpenAPI contract
  when applicable). Superseded decisions are marked `superseded`, not deleted.
- Do not invent behavior for services that do not exist yet.

## Workflow

1. **Inspect** the relevant docs and code before changing anything.
2. **Plan** the minimal bounded change within one service/context.
3. **Change** only that scope; do not touch unrelated code.
4. **Verify** with the targeted command for the touched service (see that
   service's `AGENTS.md`).

## Unavailable automation

These are not present in the repo; do not assume they work:

- `scripts/build_knowledge_graph.py` — `scripts/` does not exist. The graph
  rebuild commands documented in `docs/architecture/README.md` cannot run.
- CI — no `.github/`, workflow, or CI config exists.
- Dependency environment — no virtualenv/`.env` is checked in; installation
  and activation are environment-specific and unmanaged here.
