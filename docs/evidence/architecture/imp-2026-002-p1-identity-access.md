# Архитектурный контроль — IMP-2026-002 P1 Identity and Access

- Baseline: main at 1aedd023eb89fce799ea75e345cf9035f9aa48a1
- Scope: local-only identity, account provisioning, server-side sessions, ownership boundary for existing and new Projects, and browser login/session states.
- Decision owner: Denis Karmalak
- Verdict: pass_with_conditions (P1 only; local HTTP loopback boundary)

## Текущие границы

| Объект/состояние | Канонический владелец | Текущее представление | Источник истины |
|---|---|---|---|
| User account | Identity module | users | PostgreSQL |
| Browser session | Identity module | sessions, raw random token in HttpOnly cookie, only SHA-256 token hash persisted | PostgreSQL |
| Project ownership | Projects module | projects.owner_id → users.id | PostgreSQL |
| Authentication decision | FastAPI dependency | Valid active session resolves one User | session row and User record |
| Browser login/setup state | Vue router and auth view | owner bootstrap, login, authenticated views, session-expired state | Auth API |
| Initial owner claim | Auth API, exactly once | reserved owner row created by migration and claimed by first local setup | PostgreSQL |

## Decisive evidence

- Existing project API enters through src/paperweave/api/router.py, handlers in src/paperweave/api/projects.py, service in src/paperweave/modules/projects/service.py, and persistence in src/paperweave/infrastructure/db/project_repository.py.
- rg confirms these handlers are mounted in one FastAPI router and have no alternate project CRUD route in src/ or frontend/.
- GitNexus impact was low for ProjectService, ProjectRecord, SqlAlchemyProjectRepository, and create_app; it returned risk UNKNOWN for function-level project route symbols because callers were not resolved. The source fallback above bounded the route and injection paths.
- Existing TOML validation restricts deployment.bind_host to a loopback IP. Compose publishes API and UI only on that address; PostgreSQL remains internal.
- Browser API traffic uses configured local API port; UI and API are limited to local loopback.
- GitNexus detect_changes(scope=all) on the task worktree returned high risk, 75 changed symbols and 12 affected existing processes, with no partial/truncated flag. The impact centers on the shared frontend request/error path and existing project API/repository flow. The new identity files are not represented as established graph symbols, so those were verified by direct source inspection and mounted-route search. Backend integration tests cover the connected project/auth paths.

## Findings and gates

| ID | Severity | Scope | Finding and mitigation | Exit condition |
|---|---|---|---|---|
| P1-AC-01 | informational | P1 | Local-only is the approved first delivery. No public registration or remote deployment is enabled. A future remote mode requires a new threat-model decision. | Passed: deployment config restricts bind host to loopback; integration test denies untrusted Origin and only owner can create users. |
| P1-AC-02 | degraded | P1 | A reserved, passwordless bootstrap owner lets the migration assign legacy projects before credentials exist. The first owner setup claims this row once; there is no later re-bootstrap. This relies on the approved loopback-only boundary. | Passed: disposable test-db backfill/downgrade/upgrade proof; second bootstrap is denied by integration test. |
| P1-AC-03 | informational | P1 | Browser mutations require an approved loopback Origin; the session cookie is HttpOnly, SameSite Strict, host-only, and scoped to /api/v1. Secure is false because the first delivery serves HTTP only on loopback. | Passed: integration checks cover allowed/denied Origin and HttpOnly, SameSite, path and max-age cookie attributes. |
| P1-AC-04 | informational | P1 | Session idle timeout is 12 hours and absolute lifetime is 7 days. Database stores only the token hash; every authenticated request checks and slides idle activity. | Passed: integration checks cover logout, idle expiry, absolute expiry, and account/project isolation. |
| P1-AC-05 | informational | P1 | Migration backfills existing projects to the reserved owner. Downgrade removes identity/session tables and owner_id but preserves existing project rows. | Passed: disposable rollback test confirmed owner backfill, row survival, and successful upgrade afterward. |

## Verification outcome

- Backend: `PAPERWEAVE_CONFIG=config.example.toml make test` — 22 passed; the test runner creates an isolated Compose PostgreSQL service backed by tmpfs.
- Frontend: `npm ci`, `npm run typecheck`, and `npm run build` passed. Vite reports the pre-existing runtime-config script is intentionally not bundled because it is a classic script; the production bundle completed successfully.
- Migration: separate disposable Compose project `pw-task006-migration-proof` verified legacy owner assignment, downgrade data preservation, and re-upgrade; its container and network were removed afterward.
- `git diff --check` passed. Python bytecode compilation passed with cache redirected to `/tmp` because the managed worktree source mount is read-only to default sandbox writes.
- Graph change analysis reported HIGH risk and was reviewed against the affected flows and focused integration coverage. This is not reported as a low-risk or unchanged graph result.

## Decision and data flow

1. Alembic creates a reserved owner row with no password, adds nullable projects.owner_id, assigns all existing projects to that row, then enforces NOT NULL and the foreign key.
2. The local UI offers one-time owner setup while that row remains unclaimed. Setup replaces the placeholder email/name, stores a salted password hash, creates a server-side session and sends a random opaque token in an HttpOnly cookie.
3. The owner creates member accounts. Open registration is absent.
4. Each request resolves the cookie token hash to an unexpired session and User. Project list/create/get/update use the authenticated user's ID in every repository query.
5. Logout deletes the server-side session. Idle and absolute expiry both invalidate the same token.

## Protected invariants

- Do not expose the raw session token or password in logs, responses, or database rows.
- Do not return another user's project from get/update; use 404 for an unknown or unowned project.
- Do not leave Project ownership nullable after migration.
- Do not allow a second owner bootstrap after initial claim.
- Do not expand CORS or bind address beyond the approved loopback UI origin.
- Rollback never deletes Project content.

## Component allocation

Identity password/session rules stay in modules/identity and infrastructure/db/identity_repository.py; HTTP auth and access dependencies stay in api; project ownership filters stay in the Project persistence adapter; migration owns historical row backfill; Vue owns only login/setup presentation and route navigation.

The selected scope does not include password reset, account deletion, project sharing, remote use, TLS, or production deployment.
