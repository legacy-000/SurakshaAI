# Known Limitations

Audit date: 2026-07-14. These are observed limitations, not future commitments.

## Deployment and configuration

- The checked-in project uses inconsistent tooling: the root manifest expects Catalyst CLI, while the README and Makefile use unverified `zcil`/`zcrun` commands and refer to a non-existent `backend/` directory.
- `catalyst.json` declares `suraksha_ai` and `chatbot`; `frontend/services/api.ts` targets `suraksha-api`, which is not declared as a deployable target.
- The declared client is `suraksha-dashboard/`; a separate Next.js app exists at `frontend/`. Both contain overlapping UI and API code.
- `functions/suraksha_ai/catalyst-config.json` embeds a developer-local Windows `PYTHONPATH`, which is not portable to Catalyst deployment.
- Console state is unknown: project association, API Gateway enablement, tables, Authentication configuration, model entitlement, File Store/Stratus, Cache, and scheduled jobs were not verifiable from the checkout.

## Security and data handling

- API Gateway rules leave `/api/**` unauthenticated, and the handler trusts a client-supplied `session.user_context`.
- The action router includes unauthenticated `run_sql`, `import_table`, and profile-creation actions. It exposes raw exception text in error responses.
- Current authentication and RBAC are hard-coded mock identities and mock tokens; audit logs and conversation state are process-local.
- SQL validation only checks that a string starts with `SELECT` and lacks several write keywords. It does not parse/allow-list tables and columns, inject row scope, bound results, enforce query cost, or safely protect AI query execution.
- Dashboard fallback behavior fabricates results, including unsupported factual counts and SQL syntax that conflicts with the documented Data Store query restrictions. It must never be presented as live intelligence.

## Architecture and implementation

- Source code is duplicated across `functions/`, `functions/suraksha_ai/common/`, `functions/suraksha-api/`, and `ai_engine/`, with incompatible imports and multiple SDK assumptions.
- PostgreSQL/PostGIS/Redis/Docker artifacts remain and conflict with the mandatory Catalyst-primary architecture. They may remain as local design references only until explicitly retired or isolated.
- The relational SQL schemas are not proven compatible with Catalyst Data Store schema provisioning; they do not constitute a Data Store migration path.
- The current model clients contain hard-coded identifiers and unverified endpoint/SDK calls. Model names and availability must be confirmed in the hackathon Catalyst tenant before any inference implementation.
- Forecasting, analytics, evidence, reporting, voice, file storage, job scheduling, and AI governance are not acceptance-tested. Several modules are stubs or return mock data.
- No commander, mission DAG, claim ledger, intelligence judge, model/prompt registry, or evidence persistence implementation was found.

## Validation limitations

- Python and pytest are unavailable on PATH in this workspace, so the repository test suite was not executable.
- Existing test files do not establish deployed Catalyst behavior, authenticated request flow, real Data Store access, or console configuration.
- Existing documents contain claims of completed migration, seeded tables, deployed services, and passing capabilities that cannot be substantiated from this audit. They must be corrected only as part of a deliberate documentation reconciliation after live verification.
