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
status: in_progress
revision: 3
blockers: []
created_at: '2026-10-19T11:59:13Z'
updated_at: '2026-10-19T12:33:55Z'
next_action: Review exact P2 diff, commit TASK-002 and integrate into main
progress_note: 'Projects API, PostgreSQL migration and isolated API integration suite
  pass: 16 tests.'
---

## Outcome

FastAPI предоставляет health и создание/чтение проектов, сохраняемых PostgreSQL через мигрируемую схему.

## Scope

Реализовать Projects persistence, SQLAlchemy модели/репозиторий, Alembic revision, /api/v1 health и projects endpoints, валидацию и unit/integration проверки на изолированных ресурсах. Без edit/delete, pagination, PDF, LLM, jobs и auth.

## Notes

