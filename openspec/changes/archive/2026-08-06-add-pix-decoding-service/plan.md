## Implementation slices

### Slice 1: Spec-constant research

**Tasks:** 1.1, 1.2
**Tests first:** none — research precedes any code
**TDD exception:** explicit — no testable behavior in a research slice; its
output (verified constants) is consumed by Slice 2's contract

### Slice 2: Service scaffold + contract

**Tasks:** 2.1–2.4
**Tests first:** an import/round-trip test asserting generated models load and
match the contract shapes (written before the models exist, failing first)
**TDD exception:** none

### Slice 3: CRC16 + TLV parser

**Tasks:** 3.1–3.4
**Tests first:** unit tests for CRC16-CCITT and TLV parsing (with a real BR
Code fixture) written before the implementation; parser tests added after CRC
tests go green
**TDD exception:** none

### Slice 4: Interpretation + validation

**Tasks:** 4.1–4.6
**Tests first:** key-type detection tests, then mode/txid tests, then
validation-rule tests — each written before its implementation
**TDD exception:** none

### Slice 5: HTTP layer + integration tests

**Tasks:** 5.1–5.4
**Tests first:** TestClient integration tests for all documented 200/422 paths
and correlation reflection written before endpoint wiring is complete
**TDD exception:** none

### Slice 6: Documentation

**Tasks:** 6.1–6.5
**Tests first:** none — Markdown
**TDD exception:** explicit — docs-only slice; validated by link/relation
consistency check and review

## Review checkpoints

- After Slice 3: parser correctness review (TLV edge cases, CRC scope) —
  oracle review of the decoder core
- After Slice 5: full HTTP + validation review against the spec scenarios —
  every scenario in the delta spec mapped to a passing test
- After Slice 6: docs consistency review (frontmatter relations, links,
  AGENTS.md wording)

## Final verification intent

- `python -m pytest` from `decoding-service/` — all tests pass
- Contract YAML validation: `openspec`-independent — YAML parses and examples
  validate against schemas (prism/`yaml` + pydantic round-trip)
- `python -m pytest` from `sdui-service/` — no regressions
- Every delta-spec scenario covered by at least one test (checkpoint
  artifacts recorded in verify.md)

## Intended commit grouping

- Commit 1: decoding-service scaffold + contract + generated models
- Commit 2: decoder core (CRC, TLV, interpretation, validation) with tests
- Commit 3: HTTP layer + integration tests
- Commit 4: docs (RFC-DECODING-001, ADR-DECODING-001, CTX/README links,
  AGENTS.md gate)
