## Implementation slices

### Slice 1: Format research (tasks 1.1–1.2)

**Tasks:** 1.1–1.2
**Tests first:** none — research slice; findings recorded as source-referenced notes used by Slice 2 tests
**TDD exception:** research produces no production code; explicit exception

### Slice 2: Shared instrumentation package (tasks 2.1–2.7)

**Tasks:** 2.1–2.7
**Tests first:** failing unit tests for formatter fields and no-sensitive-material (2.2) before formatter (2.3); trace-context accept/generate tests (2.4) before implementation (2.5); metrics label-cardinality tests (2.6) before implementation (2.7)

### Slice 3: observability-service (tasks 3.1–3.5)

**Tasks:** 3.1–3.5
**Tests first:** integration tests for `/health`, `/ready`, metrics-port exposition, and served-OpenAPI==contract (3.5) drive the scaffold; contract (3.1) written before code
**TDD exception:** none

### Slice 4: Retrofit sdui-service (tasks 4.1–4.4)

**Tasks:** 4.1–4.4
**Tests first:** failing tests for new endpoints, metrics port, trace headers, and log fields (4.2) before implementation (4.3)

### Slice 5: Retrofit decoding-service (tasks 5.1–5.4)

**Tasks:** 5.1–5.4
**Tests first:** failing tests incl. data-policy checks (5.2) before implementation (5.3)

### Slice 6: Documentation (tasks 6.1–6.5)

**Tasks:** 6.1–6.5
**Tests first:** none — Markdown artifacts; verified by link resolution and cross-checks against the aggregated spec at archive time
**TDD exception:** documentation slice; explicit exception

### Slice 7: Final verification (tasks 7.1–7.3)

**Tasks:** 7.1–7.3
**Tests first:** n/a — verification pass

## Review checkpoints

- After Slice 3: council review of the observability contract shape (health/ready only, no metrics path), metrics-port separation, and data policy as spec'd
- After Slice 5: oracle review of the full diff (three services, contracts, package) until clean; reconcile findings into specs/tasks
- After Slice 6: docs-vs-spec drift check (RFC/ADR statements match the aggregated spec)

## Final verification intent

- `python -m pytest` from `observability-service/` — all green
- `python -m pytest` from `sdui-service/` — all green (existing suite + retrofit)
- `python -m pytest` from `decoding-service/` — all green, incl. served-OpenAPI==contract assertion
- Contract YAML validation for all three services; served OpenAPI == contract (no `/metrics` anywhere)
- Business-behavior regression check: decoding error codes and response shapes unchanged

## Intended commit grouping

- Commit 1: shared instrumentation package (`observability-service/openpix_observability/` + tests + requirements)
- Commit 2: observability-service (contract, models, app, metrics listener, AGENTS.md, tests)
- Commit 3: sdui-service retrofit (contract 1.1.0, models, endpoints, metrics, tests)
- Commit 4: decoding-service retrofit (contract 1.1.0, models, endpoints, metrics, tests)
- Commit 5: docs — RFC-OBSERVABILITY-001, ADR-OBSERVABILITY-001, CTX links, README index, root AGENTS.md gate lift
