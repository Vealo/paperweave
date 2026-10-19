---
schema: task-store/v1
id: TASK-002
key: IMP-imp-2026-001-mvp-foundation:P2:projects-api-persistence
title: Реализовать хранение проектов и API MVP
source_ref: request:2026-10-19-paperweave-mvp-foundation
parent_ref: imp-2026-001-mvp-foundation
phase: P2
priority: high
depends_on:
- TASK-001
criteria:
- id: AC-1
  text: Первая миграция создаёт projects (UUID id, name до 200, nullable description,
    timestamptz created_at) и Alembic version table; операции проекта используют PostgreSQL.
  checked: true
  evidence:
  - 'make test: isolated DB migrations applied twice; integration schema check confirmed
    projects fields and Alembic revision 20261019_0001; PostgreSQL CRUD passed'
- id: AC-2
  text: GET /api/v1/health/live не зависит от БД; GET /api/v1/health/ready отвечает
    200 при доступной БД и 503 при недоступной.
  checked: true
  evidence:
  - 'integration test_live_and_ready_report_database_state: live 200 while DB endpoint
    failed; ready returned 503 on failure and 200 on test DB'
- id: AC-3
  text: POST /api/v1/projects trim-валидирует name 1–200 и description максимум 5000,
    дубликаты имён разрешены, возвращает 201 с backend UUID и UTC created_at.
  checked: true
  evidence:
  - 'integration create/list/detail contract: trim, lengths, duplicate names, 201
    UUID UTC, newest first, 404/422'
- id: AC-4
  text: GET /api/v1/projects возвращает новые первыми; GET /api/v1/projects/{uuid}
    различает 200/404/422.
  checked: true
  evidence:
  - integration test_create_list_and_get_project_contract verified list order and
    detail response/status codes
- id: AC-5
  text: Unit/integration tests не используют пользовательскую рабочую БД и покрывают
    успешные и ошибочные границы контракта.
  checked: true
  evidence:
  - make test 16 passed; Compose test-db uses tmpfs; tests/conftest.py rejects any
    TEST_DATABASE_URL not targeting test-db
status: done
revision: 4
blockers: []
created_at: '2026-10-19T11:59:13Z'
updated_at: '2026-10-19T12:35:36Z'
progress_note: All P2 criteria accepted; task commit integrated into main and post-merge
  checks passed.
---

## Outcome

FastAPI предоставляет health и создание/чтение проектов, сохраняемых PostgreSQL через мигрируемую схему.

## Scope

Реализовать Projects persistence, SQLAlchemy модели/репозиторий, Alembic revision, /api/v1 health и projects endpoints, валидацию и unit/integration проверки на изолированных ресурсах. Без edit/delete, pagination, PDF, LLM, jobs и auth.

## Notes

## Finalization receipt — 2026-10-19

- Acceptance: TASK-002 AC-1…AC-5 passed; isolated `make test` passed 16 tests.
- Task branch: `codex/task-002-projects-api-db`, based on `main` at `4fa9bc85bb8ad42f2dbdb2af8ba8844235f1248b`.
- Task commit: `ba932454ce617c5dfe080caeaafe448dfdc68139` (`feat(TASK-002): add projects API and PostgreSQL persistence`).
- Parent integration: merge commit `09cc5156b6c85450ef2470d3fd2b1bc0b9df2a19` on `main`; reachability verifier returned `reachable: true` at that parent HEAD.
- Post-integration checks: `make test` — 16 passed; plan, phase, IMP contract, task-store and TODO validators passed; `git diff --check` passed.
- Test isolation: Compose test profile uses a dedicated PostgreSQL `tmpfs`; test fixture rejects any database URL that does not target `test-db`; migration ran twice and schema/revision were inspected.
- GitNexus: incomplete/unavailable, not a pass. MCP detected 13 changed files but zero symbols on stale/empty graph; prior post-integration CLI refresh failed on read-only `/home/denis/.gitnexus/registry.json`. Direct source/reference and diff review plus required checks passed; no unresolved P2 data-integrity risk found.
- External actions: no push, hosted CI, PR, or deployment performed.
