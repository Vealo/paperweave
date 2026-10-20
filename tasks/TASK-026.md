---
schema: task-store/v1
id: TASK-026
key: IMP-2026-003:P4:contrast-and-contract-audit
title: Провести сквозной аудит контраста и согласованности
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#phase-4
parent_ref: imp-2026-003-light-design-system-user-settings
phase: P4
priority: none
depends_on:
- TASK-023
- TASK-024
- TASK-025
criteria:
- id: AC-1
  text: 'AC-P4-001: проверенные экраны не содержат светлой поверхности с белым или
    низкоконтрастным текстом.'
  checked: false
  evidence: []
- id: AC-2
  text: 'AC-P4-002: согласие/статус читается и без восприятия оттенка цвета.'
  checked: false
  evidence: []
- id: AC-3
  text: 'AC-P4-003: design-system, user_settings, API и UI не противоречат друг другу.'
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-20T11:41:26Z'
updated_at: '2026-10-20T11:41:26Z'
---

## Outcome

Подтвердить читаемость основных страниц и полноэкранных диалогов в светлой схеме, исправить локальные нарушения и согласовать дизайн-код, модель настроек, API и UI.

## Scope

Проверить projects, project workspace, profile, users/new, login/setup, account menu, forms/messages и fullscreen dialogs; проверить focus, disabled, error и status без зависимости от оттенка; синхронизировать docs/design-system.md и docs/data-model.md. Только локальные маршруты, без массового редизайна и dark theme.

## Notes
