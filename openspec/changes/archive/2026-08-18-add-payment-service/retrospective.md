## Retrospective

<!-- Closeout artifact. Capture what happened, what worked, and what to watch next time. -->

### What shipped

Payment-service shipped as a contract-first FastAPI service with a three-state payment lifecycle, SQLite persistence, two-layer idempotency, and an atomic intent consumer using the PedroBankFake Executor without internal retries. It includes the API, QUERY history, observability, service-local RFC/ADR documentation, and architecture/root gate updates.

### What went well

Test-first slices, runner gates, the fix-loop review, and contract parity tests worked well. The direct observability implementation and deviation were recorded because the shared package was absent.

### What to watch next time

QUERY tooling and proxy support remain a risk. SQLite is single-writer, and the consumer is in-process. The generated graph is stale because the rebuild script is absent. The `.venv` is a local ignored environment.

### Follow-ups

- Integrate a future observability service or shared package.
- Replace PedroBankFake with a real Executor.
- Rebuild the generated graph when the rebuild script exists.
