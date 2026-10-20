---
schema: task-store/v1
id: TASK-024
key: IMP-2026-003:P2:normalize-theme-setting
title: Нормализовать сохранённую настройку темы
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#phase-2
parent_ref: imp-2026-003-light-design-system-user-settings
phase: P2
priority: none
depends_on:
- TASK-023
criteria:
- id: AC-1
  text: 'AC-P2-001: все прежние значения system, dark, light приводятся к light; новые
    настройки имеют default light.'
  checked: true
  evidence:
  - 'Disposable PostgreSQL migration rehearsal: system/dark/light all normalized to
    light; new DB default and CHECK constraint enforce light.'
  - Disposable PostgreSQL rehearsal also downgraded to 0010 and re-upgraded; existing
    values remained light after downgrade, then the light-only constraint/default
    returned.
  - Task implementation commit adebfef3e1d4c2db235279e9770361b45344f499 on main.
- id: AC-2
  text: 'AC-P2-002: API читает/сохраняет light, сохраняет user isolation и предсказуемо
    обрабатывает legacy/invalid payload.'
  checked: true
  evidence:
  - 'API integration coverage: GET returns light, legacy system/dark/light PATCH returns
    light, sepia is 422, and member updates do not affect owner settings.'
  - Task implementation commit adebfef3e1d4c2db235279e9770361b45344f499 on main.
- id: AC-3
  text: 'AC-P2-003: migration rehearsal подтверждает отсутствие изменений других пользовательских
    данных.'
  checked: true
  evidence:
  - 'Isolated Compose test run: 87 passed; migration rehearsal preserved email, display_name,
    password_hash, role, and is_active.'
  - Task implementation commit adebfef3e1d4c2db235279e9770361b45344f499 on main; local
    Compose test database was disposable.
status: done
revision: 5
blockers: []
created_at: '2026-10-20T11:41:18Z'
updated_at: '2026-10-20T12:19:34Z'
progress_note: TASK-024 verified and committed on main as adebfef; 87 isolated tests
  passed.
---

## Outcome

Привести сохранённое и новое значение user_settings.theme к единственному поддерживаемому значению light через ORM/API/repository и локальную миграцию.

## Scope

Добавить совместимый переход API, migration backfill system/dark/light в light, default light и тесты на disposable PostgreSQL. Сохранить user isolation и остальные данные; не запускать миграцию на shared/production DB.

## Notes
