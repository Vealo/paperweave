# Архитектурный контроль — imp-2026-001-mvp-foundation

Дата: 2026-10-19. Scope: local MVP runtime, project persistence/API and Vue UI. Baseline `b1ecdc91c41d6cf2f38b74af001d181eeefa6c3e`; dirty tree preserved.

## Текущие владельцы и evidence

- Frontend boundary: `frontend/src/main.ts`, `App.vue` — заглушки; `package.json` содержит Vue, PrimeVue 4, TypeScript and Tiptap dependencies.
- API/domain/DB boundaries: Python package contains only `main.py` and `.gitkeep` placeholders for API, Projects, infrastructure/db and integrations. No routes or repository were found.
- Persistence/migrations: `migrations/.gitkeep`; no Project schema or migration exists.
- Tests: only empty `tests/unit`, `tests/integration` placeholders.
- Product context: PDF requests local browser→UI→FastAPI→PostgreSQL, with project create/list/detail and persistence. The direct later frontend instruction selects Vue/PrimeVue/TS; PDF's NiceGUI suggestion is not followed. Future Tiptap is outside MVP.

## Verdict: `pass_with_conditions`

Proposed boundaries are proportionate for a single-user local MVP: Vue owns presentation, FastAPI HTTP routes own transport validation, Projects owns project behavior, DB adapter owns SQL persistence, Alembic owns schema evolution, Compose owns process orchestration. No separate worker, broker, generalized repository framework, or extra domain entities are needed for this slice.

## Findings and conditions

| ID | Severity/scope | Finding | Impact | Owner | Exit condition / next action |
|---|---|---|---|---|---|
| ARCH-MVP-01 | degraded / phases P1,P4 | Config flows from TOML via launcher into Compose processes; avoid duplicated user-config sources and secret-bearing logs. | Divergent effective config or credential disclosure. | Runtime/config | P1 tests prove validation and safe logging; P4 proves all services use same mounted config. |
| ARCH-MVP-02 | degraded / phases P1,P4 | UI/API/DB exposure is a trust boundary. API and UI host ports loopback only; DB internal-only. | Accidental network exposure/data access. | Runtime | Compose config and local runtime evidence confirm bindings before P4 closes. |
| ARCH-MVP-03 | informational / phases P2,P3,P4 | Browser cannot resolve Compose-only hostname such as `api`; container health checks may use service DNS but browser API base URL must be browser-reachable. | UI appears disconnected despite healthy containers. | Frontend/runtime | Decide and verify browser-facing URL in P3/P4; keep configurable and local-only. |
| ARCH-MVP-04 | degraded / phases P2,P4 | Readiness depends on DB; liveness must not; migration failure must prevent app readiness. | Incorrect ready signal or startup ordering. | API/runtime | Endpoint and startup integration checks prove distinction/order. |
| ARCH-MVP-05 | degraded / phases P2,P4 | Test DB/data must be isolated from normal persistent project volume. | Accidental loss/corruption of user work. | Test/runtime | `make test` selects isolated database/resources and demonstrates cleanup-safe execution. |

## Направление зависимостей

`Vue UI → HTTP API → Project application behavior → DB adapter → PostgreSQL`. Transport types remain in API boundary; SQLAlchemy sessions do not escape infrastructure. UI does not call PostgreSQL. Config parsing has no connection side effects at import. Database schema changes use forward migrations and `down` preserves volume.

Conditions are phase-scoped; no IMP-wide blocker remains. This review is not ADR acceptance and does not claim implementation or runtime evidence.
