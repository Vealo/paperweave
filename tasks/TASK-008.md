---
schema: task-store/v1
id: TASK-008
key: IMP-imp-2026-002-domain-workspace:P3:project-workspace
title: Собрать интерфейс рабочего пространства проекта
source_ref: imp-2026-002-domain-workspace#P3
parent_ref: imp-2026-002-domain-workspace
phase: P3
priority: medium
depends_on:
- TASK-006
- TASK-007
criteria:
- id: AC-1
  text: Из проекта можно открыть рукопись и перейти к разделу с сохранением контекста.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-008-acceptance-ledger.yaml
- id: AC-2
  text: Левая навигация, центральный редактор и правая контекстная область разделяют
    свои роли.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-008-acceptance-ledger.yaml
- id: AC-3
  text: Loading/empty/error и responsive состояния работают; save/API/AI статусы визуально
    различимы.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-008-acceptance-ledger.yaml
- id: AC-4
  text: Typecheck/build и ручная browser-проверка основных состояний проходят.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-008-acceptance-ledger.yaml
status: done
revision: 5
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T15:21:03Z'
progress_note: P3 merged to main; post-merge checks, GitNexus refresh and reachability
  passed.
---

## Outcome

Пользователь работает в shell с project navigation, структурой рукописи, центральным редактором и контекстной областью.

## Scope

Собрать layout и маршруты поверх утверждённых project/manuscript API на Vue 3, TypeScript, PrimeVue 4; не дублировать доменные правила во frontend.

## Notes
