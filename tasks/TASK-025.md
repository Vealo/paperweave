---
schema: task-store/v1
id: TASK-025
key: IMP-2026-003:P3:single-light-theme-owner
title: Устранить конфликт настроек и активной схемы
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#phase-3
parent_ref: imp-2026-003-light-design-system-user-settings
phase: P3
priority: none
depends_on:
- TASK-024
criteria:
- id: AC-1
  text: 'AC-P3-001: настройки не загружаются/применяются параллельно разными владельцами
    темы.'
  checked: true
  evidence:
  - docs/evidence/verification/TASK-025-acceptance-ledger.yaml
  - commit:3884a7a30dafdb6c293efe1e4a04be7e6b147103
- id: AC-2
  text: 'AC-P3-002: ни route transition, ни настройка пользователя/ОС не устанавливают
    .p-dark.'
  checked: true
  evidence:
  - docs/evidence/verification/TASK-025-acceptance-ledger.yaml
  - commit:3884a7a30dafdb6c293efe1e4a04be7e6b147103
- id: AC-3
  text: 'AC-P3-003: персональная тема не дублируется в системном placeholder menu.'
  checked: true
  evidence:
  - docs/evidence/verification/TASK-025-acceptance-ledger.yaml
  - commit:3884a7a30dafdb6c293efe1e4a04be7e6b147103
status: done
revision: 4
blockers: []
created_at: '2026-10-20T11:41:26Z'
updated_at: '2026-10-20T12:25:34Z'
progress_note: TASK-025 завершена и интегрирована в main; 7 frontend-тестов, typecheck
  и build прошли.
---

## Outcome

Оставить один владелец состояния оформления, исключить активацию тёмной темы и убрать недоступный выбор темы из пользовательских настроек.

## Scope

Согласовать App.vue, ProfileView.vue, main.ts и связанные frontend API/tests: единый bootstrap/update path, светлая схема при любых OS preferences и API сбоях, личный профиль отдельно от заглушки системных настроек. Не удалять settings API/table и не добавлять localStorage.

## Notes
