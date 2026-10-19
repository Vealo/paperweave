---
schema: task-store/v1
id: TASK-006
key: IMP-imp-2026-002-domain-workspace:P1:identity-access
title: Реализовать идентификацию и контроль доступа
source_ref: imp-2026-002-domain-workspace#P1
parent_ref: imp-2026-002-domain-workspace
phase: P1
priority: high
depends_on:
- TASK-005
criteria:
- id: AC-1
  text: Владелец проекта утвердил provisioning, local/remote режим и жизненный цикл
    сессии; решение связано с актуальным ADR/Spec.
  checked: true
  evidence:
  - docs/decisions/ADR-0007-local-identity-and-project-access.md
- id: AC-2
  text: Для существующих проектов определена и проверена миграция владельца с rollback
    на disposable DB.
  checked: true
  evidence:
  - docs/evidence/architecture/imp-2026-002-p1-identity-access.md
- id: AC-3
  text: API list/create/get/update закрыты проверками доступа; тесты подтверждают
    allow/deny и отсутствие межпользовательской утечки.
  checked: true
  evidence:
  - tests/integration/test_projects_api.py
- id: AC-4
  text: UI показывает состояния входа, истечения сессии и отказа отдельно от ошибки
    API.
  checked: true
  evidence:
  - frontend/src/views/LoginView.vue; frontend/src/views/AccessDeniedView.vue
status: done
revision: 7
blockers: []
created_at: '2026-10-19T14:00:24Z'
updated_at: '2026-10-19T14:41:05Z'
progress_note: Identity, sessions and ownership shipped; migration rollback, 22 backend
  tests and frontend checks pass.
---

## Outcome

Ввести согласованную модель входа и проверить изоляцию проектов по правам пользователя.

## Scope

После решения ACF-1: уточнить/зафиксировать Spec и security criteria, реализовать user/session boundary, проверить каждый project API use case и миграцию существующих Project rows. Не выбирать provisioning или удалённый режим самостоятельно.

## Notes
