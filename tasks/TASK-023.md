---
schema: task-store/v1
id: TASK-023
key: IMP-2026-003:P1:semantic-light-palette
title: Реализовать семантическую палитру светлой темы
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#phase-1
parent_ref: imp-2026-003-light-design-system-user-settings
phase: P1
priority: none
depends_on: []
criteria:
- id: AC-1
  text: 'AC-P1-001: основные действия используют #5B7917 с читаемым текстом.'
  checked: false
  evidence: []
- id: AC-2
  text: 'AC-P1-002: #0D3500 ограничен тёмным состоянием акцента; крупные surfaces
    нейтральны.'
  checked: false
  evidence: []
- id: AC-3
  text: 'AC-P1-003: общие компоненты используют централизованные semantic tokens.'
  checked: false
  evidence: []
status: blocked
revision: 3
blockers:
- 'IMP-BL-01 remains: main at 74901be has uncheckpointed edits in frontend/src/App.vue,
  frontend/src/main.ts, frontend/src/styles/main.css, docs/design-system.md, docs/data-model.md,
  and DOCS.md; no TASK-023 worktree exists from a checkpoint.'
created_at: '2026-10-20T11:41:12Z'
updated_at: '2026-10-20T11:50:45Z'
progress_note: 'Проверено: main на 74901be; шесть пересекающихся файлов остаются без
  checkpoint.'
---

## Outcome

Утвердить и внедрить единую семантическую палитру светлой темы на основе #5B7917 для главных действий и #0D3500 для тёмного состояния акцента, сохранив нейтральные крупные поверхности.

## Scope

После checkpoint IMP-BL-01 сверить PrimeVue/Aura public theme API; централизовать semantic tokens в frontend theme/styles и применить к общим компонентам; синхронизировать docs/design-system.md. Не менять данные/API, не заливать крупные поверхности цветами палитры, не выполнять массовый редизайн и не включать тёмную схему.

## Notes
