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
  checked: false
  evidence: []
- id: AC-2
  text: 'AC-P2-002: API читает/сохраняет light, сохраняет user isolation и предсказуемо
    обрабатывает legacy/invalid payload.'
  checked: false
  evidence: []
- id: AC-3
  text: 'AC-P2-003: migration rehearsal подтверждает отсутствие изменений других пользовательских
    данных.'
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-20T11:41:18Z'
updated_at: '2026-10-20T11:41:18Z'
---

## Outcome

Привести сохранённое и новое значение user_settings.theme к единственному поддерживаемому значению light через ORM/API/repository и локальную миграцию.

## Scope

Добавить совместимый переход API, migration backfill system/dark/light в light, default light и тесты на disposable PostgreSQL. Сохранить user isolation и остальные данные; не запускать миграцию на shared/production DB.

## Notes
